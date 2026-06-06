from __future__ import annotations

"""工服未穿戴报警演示脚本。

本脚本用于资料包内的离线测试，严格贴合项目当前在线检测规范：

1. person 整帧检测；
2. ROI 重叠比例过滤；
3. 对候选人员区域执行 workwear/clothes 检测；
4. 用 IoU tracker 给同一人员分配 track_id；
5. 按 track_id 做时间窗口违规比例判断；
6. 只保存触发 track 的证据图。

注意：
- 本脚本是离线演示入口，不依赖 Flask、数据库和摄像头线程。
- 真正线上系统仍以 inspection-flask 中的线程、规则和证据保存逻辑为准。
"""

import argparse
import json
from collections import deque
from datetime import datetime
from pathlib import Path


# ─── 与项目 settings.py 对齐的默认配置 ───────────────────────────────────────
IMGSZ = 640
PERSON_CONF = 0.55
WORKWEAR_CONF = 0.45
PREDICT_IOU = 0.45
PREDICT_MAX_DET = 100

MONITORED_PERSON_LABELS = {"person"}
WORKWEAR_LABELS = {"clothes"}
WORKWEAR_COMPLIANCE_MODE = "any"
USE_WHITE_BG_MASK = False

MIN_PERSON_AREA_MODE = "absolute"
MIN_PERSON_BOX_AREA = 3000
MIN_PERSON_AREA_RATIO = 0.005
ROI_MIN_OVERLAP_RATIO = 0.5

TEMPORAL_WINDOW_SIZE = 5
TEMPORAL_TRIGGER_RATIO = 0.6
MIN_TRACK_APPEAR_FRAMES = 2
TRACKER_MAX_AGE = 2
TRACKER_IOU_THRESHOLD = 0.3

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class SimpleIoUTracker:
    """基于 IoU 的轻量人员跟踪器，与项目在线链路的 track_id 口径一致。"""

    def __init__(self, iou_threshold: float = TRACKER_IOU_THRESHOLD, max_age: int = TRACKER_MAX_AGE):
        self.iou_threshold = iou_threshold
        self.max_age = max(1, max_age)
        self._next_id = 0
        self._prev_tracks: list[dict] = []

    @staticmethod
    def _compute_iou(box_a: list, box_b: list) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter == 0:
            return 0.0
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def _alloc_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def update(self, person_contexts: list[dict]) -> list[dict]:
        if not person_contexts:
            self._prev_tracks = [
                {**track, "age": track.get("age", 0) + 1}
                for track in self._prev_tracks
                if track.get("age", 0) + 1 <= self.max_age
            ]
            return person_contexts

        prev = self._prev_tracks
        used_prev: set[int] = set()
        used_curr: set[int] = set()
        pairs: list[tuple[float, int, int]] = []

        for curr_idx, ctx in enumerate(person_contexts):
            for prev_idx, prev_track in enumerate(prev):
                iou = self._compute_iou(ctx.get("bbox", []), prev_track.get("bbox", []))
                if iou >= self.iou_threshold:
                    pairs.append((iou, curr_idx, prev_idx))
        pairs.sort(key=lambda item: item[0], reverse=True)

        assignments: dict[int, int] = {}
        for _iou, curr_idx, prev_idx in pairs:
            if curr_idx in used_curr or prev_idx in used_prev:
                continue
            assignments[curr_idx] = prev[prev_idx]["track_id"]
            used_curr.add(curr_idx)
            used_prev.add(prev_idx)

        for curr_idx, ctx in enumerate(person_contexts):
            ctx["track_id"] = assignments.get(curr_idx, self._alloc_id())

        new_prev = [
            {"bbox": ctx.get("bbox", []), "track_id": ctx["track_id"], "age": 0}
            for ctx in person_contexts
        ]
        for prev_idx, prev_track in enumerate(prev):
            if prev_idx not in used_prev and prev_track.get("age", 0) + 1 <= self.max_age:
                new_prev.append({**prev_track, "age": prev_track.get("age", 0) + 1})
        self._prev_tracks = new_prev
        return person_contexts

    def reset(self):
        self._prev_tracks = []
        self._next_id = 0


def parse_roi(raw_roi: str | None) -> list[int] | None:
    if not raw_roi:
        return None
    parts = [int(value.strip()) for value in raw_roi.split(",")]
    if len(parts) != 4:
        raise ValueError("--roi 格式应为 x1,y1,x2,y2")
    return parts


def in_roi(bbox: list, roi: list[int] | None) -> bool:
    if not roi:
        return True
    x1, y1, x2, y2 = bbox
    rx1, ry1, rx2, ry2 = roi
    ix1 = max(x1, rx1)
    iy1 = max(y1, ry1)
    ix2 = min(x2, rx2)
    iy2 = min(y2, ry2)
    if ix2 <= ix1 or iy2 <= iy1:
        return False
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    person_area = max(1, (x2 - x1) * (y2 - y1))
    return inter_area / person_area >= ROI_MIN_OVERLAP_RATIO


def crop_person(frame, bbox: list):
    x1, y1, x2, y2 = [int(value) for value in bbox]
    h, w = frame.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def extract_detected_labels(workwear_items: list[dict]) -> set[str]:
    return {
        str(item.get("label", "")).strip()
        for item in workwear_items
        if isinstance(item, dict) and str(item.get("label", "")).strip()
    }


def evaluate_workwear_compliance(workwear_items: list[dict]) -> bool:
    if not isinstance(workwear_items, list):
        return False
    detected = extract_detected_labels(workwear_items)
    if WORKWEAR_COMPLIANCE_MODE == "all":
        return WORKWEAR_LABELS.issubset(detected)
    return bool(detected & WORKWEAR_LABELS)


def parse_yolo_boxes(result) -> list[dict]:
    detections: list[dict] = []
    for box in result.boxes:
        cls_raw = box.cls[0]
        cls_id = int(cls_raw.item()) if hasattr(cls_raw, "item") else int(cls_raw)
        conf_raw = box.conf[0]
        conf = float(conf_raw.item()) if hasattr(conf_raw, "item") else float(conf_raw)
        label = result.names[cls_id] if isinstance(result.names, (list, dict)) else str(cls_id)
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
        detections.append({"bbox": [x1, y1, x2, y2], "confidence": conf, "label": label})
    return detections


def infer_model(model, image, conf: float, device: str) -> list[dict]:
    results = model(
        image,
        conf=conf,
        imgsz=IMGSZ,
        device=device,
        verbose=False,
        iou=PREDICT_IOU,
        max_det=PREDICT_MAX_DET,
    )
    detections: list[dict] = []
    for result in results:
        detections.extend(parse_yolo_boxes(result))
    return detections


def build_person_contexts(frame, person_model, workwear_model, roi: list[int] | None, device: str) -> list[dict]:
    persons = [
        det for det in infer_model(person_model, frame, PERSON_CONF, device)
        if det.get("label") in MONITORED_PERSON_LABELS
    ]

    frame_area = frame.shape[0] * frame.shape[1]
    contexts: list[dict] = []
    for person in persons:
        bbox = person.get("bbox", [])
        if len(bbox) != 4:
            continue

        x1, y1, x2, y2 = bbox
        area = max(0, x2 - x1) * max(0, y2 - y1)
        if MIN_PERSON_AREA_MODE == "relative":
            if frame_area > 0 and area / frame_area < MIN_PERSON_AREA_RATIO:
                continue
        elif area < MIN_PERSON_BOX_AREA:
            continue

        crop = crop_person(frame, bbox)
        workwear_items: list[dict] = []
        if crop is not None and getattr(crop, "size", 0) > 0:
            workwear_items = [
                det for det in infer_model(workwear_model, crop, WORKWEAR_CONF, device)
                if det.get("label") in WORKWEAR_LABELS
            ]

        contexts.append(
            {
                "bbox": bbox,
                "confidence": float(person.get("confidence", 0.0)),
                "label": person.get("label", "person"),
                "area": area,
                "in_roi": in_roi(bbox, roi),
                "workwear_items": workwear_items,
                "has_workwear": evaluate_workwear_compliance(workwear_items),
            }
        )

    return contexts


def evaluate_window(window: deque) -> list[dict]:
    track_stats: dict[int, dict] = {}
    for frame_idx, frame_item in enumerate(window):
        for person in frame_item.get("persons", []):
            if not person.get("in_roi", True):
                continue
            track_id = person.get("track_id")
            if track_id is None:
                continue
            stats = track_stats.setdefault(
                track_id,
                {"appear": 0, "violation": 0, "frames": [], "best_conf": 0.0},
            )
            stats["appear"] += 1
            if not person.get("has_workwear", False):
                stats["violation"] += 1
                stats["frames"].append(frame_idx)
                stats["best_conf"] = max(stats["best_conf"], float(person.get("confidence", 0.0)))

    triggered: list[dict] = []
    for track_id, stats in track_stats.items():
        if stats["appear"] < MIN_TRACK_APPEAR_FRAMES:
            continue
        ratio = stats["violation"] / max(stats["appear"], 1)
        if ratio >= TEMPORAL_TRIGGER_RATIO:
            triggered.append(
                {
                    "track_id": track_id,
                    "appear": stats["appear"],
                    "violation": stats["violation"],
                    "violation_ratio": ratio,
                    "best_conf": stats["best_conf"],
                }
            )
    return triggered


def draw_evidence(frame, persons: list[dict], triggered_track_ids: set[int]):
    import cv2

    canvas = frame.copy()
    for person in persons:
        if person.get("track_id") not in triggered_track_ids:
            continue
        x1, y1, x2, y2 = [int(value) for value in person["bbox"]]
        color = (0, 0, 255) if not person.get("has_workwear", False) else (0, 180, 0)
        label = f"track={person.get('track_id')} no_workwear"
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        cv2.putText(canvas, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return canvas


def iter_input_frames(input_path: Path, frame_step: int = 1):
    import cv2

    if input_path.is_dir():
        image_paths = sorted(p for p in input_path.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
        for idx, image_path in enumerate(image_paths):
            frame = cv2.imread(str(image_path))
            if frame is not None:
                yield idx, str(image_path), frame
        return

    if input_path.suffix.lower() in IMAGE_EXTS:
        frame = cv2.imread(str(input_path))
        if frame is not None:
            yield 0, str(input_path), frame
        return

    cap = cv2.VideoCapture(str(input_path))
    frame_idx = 0
    kept_idx = 0
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % max(1, frame_step) == 0:
            yield kept_idx, f"{input_path}#frame={frame_idx}", frame
            kept_idx += 1
        frame_idx += 1
    cap.release()


def main() -> int:
    parser = argparse.ArgumentParser(description="离线工服未穿戴报警演示脚本")
    parser.add_argument("input", help="图片、图片目录或视频路径")
    parser.add_argument("--roi", help="可选 ROI: x1,y1,x2,y2；不传则整帧视为监管区域")
    parser.add_argument("--weights-dir", default="weights", help="权重目录，默认 ./weights")
    parser.add_argument("--output", default="alarm_output", help="输出目录")
    parser.add_argument("--device", default="cpu", help="推理设备，如 cpu 或 0")
    parser.add_argument("--frame-step", type=int, default=1, help="视频抽帧间隔，默认每帧处理")
    args = parser.parse_args()

    from ultralytics import YOLO
    import cv2

    script_dir = Path(__file__).resolve().parent
    weights_dir = Path(args.weights_dir)
    if not weights_dir.is_absolute():
        weights_dir = script_dir / weights_dir
    person_weight = weights_dir / "person_detect_yolov8.pt"
    workwear_weight = weights_dir / "workwear_detect_yolov8.pt"
    if not person_weight.exists():
        raise FileNotFoundError(f"人员检测权重不存在: {person_weight}")
    if not workwear_weight.exists():
        raise FileNotFoundError(f"工服检测权重不存在: {workwear_weight}")

    input_path = Path(args.input)
    roi = parse_roi(args.roi)
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    person_model = YOLO(str(person_weight))
    workwear_model = YOLO(str(workwear_weight))
    tracker = SimpleIoUTracker()
    window: deque = deque(maxlen=TEMPORAL_WINDOW_SIZE)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(input_path),
        "roi": roi,
        "weights": {
            "person": str(person_weight),
            "workwear": str(workwear_weight),
        },
        "settings": {
            "PERSON_CONF": PERSON_CONF,
            "WORKWEAR_CONF": WORKWEAR_CONF,
            "ROI_MIN_OVERLAP_RATIO": ROI_MIN_OVERLAP_RATIO,
            "TEMPORAL_WINDOW_SIZE": TEMPORAL_WINDOW_SIZE,
            "TEMPORAL_TRIGGER_RATIO": TEMPORAL_TRIGGER_RATIO,
            "MIN_TRACK_APPEAR_FRAMES": MIN_TRACK_APPEAR_FRAMES,
            "TRACKER_MAX_AGE": TRACKER_MAX_AGE,
            "TRACKER_IOU_THRESHOLD": TRACKER_IOU_THRESHOLD,
        },
        "frames": [],
        "events": [],
    }

    for frame_idx, frame_source, frame in iter_input_frames(input_path, frame_step=args.frame_step):
        contexts = build_person_contexts(frame, person_model, workwear_model, roi, args.device)
        contexts = tracker.update(contexts)
        window.append({"frame_idx": frame_idx, "source": frame_source, "frame": frame, "persons": contexts})

        frame_summary = {
            "frame_idx": frame_idx,
            "source": frame_source,
            "person_count": len(contexts),
            "roi_person_count": sum(1 for ctx in contexts if ctx.get("in_roi", False)),
            "suspect_count": sum(
                1 for ctx in contexts
                if ctx.get("in_roi", False) and not ctx.get("has_workwear", False)
            ),
            "tracks": [
                {
                    "track_id": ctx.get("track_id"),
                    "bbox": ctx.get("bbox"),
                    "in_roi": ctx.get("in_roi"),
                    "has_workwear": ctx.get("has_workwear"),
                    "workwear_count": len(ctx.get("workwear_items", [])),
                }
                for ctx in contexts
            ],
        }
        report["frames"].append(frame_summary)

        if len(window) < TEMPORAL_WINDOW_SIZE:
            continue

        triggered = evaluate_window(window)
        if not triggered:
            continue

        triggered_ids = {item["track_id"] for item in triggered}
        latest_item = window[-1]
        evidence = draw_evidence(latest_item["frame"], latest_item.get("persons", []), triggered_ids)
        evidence_path = evidence_dir / f"alarm_frame_{frame_idx:06d}.jpg"
        cv2.imwrite(str(evidence_path), evidence)
        event = {
            "frame_idx": frame_idx,
            "source": frame_source,
            "rule": "workwear_missing",
            "rule_name": "作业区人员疑似未穿工服",
            "triggered_tracks": triggered,
            "evidence": str(evidence_path),
        }
        report["events"].append(event)

        # 与在线线程一致：触发后清空窗口并重置 tracker，避免同一窗口重复报警。
        window.clear()
        tracker.reset()

    report_path = output_dir / "alarm_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"处理完成: {len(report['frames'])} 帧")
    print(f"触发告警: {len(report['events'])} 次")
    print(f"报告文件: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
