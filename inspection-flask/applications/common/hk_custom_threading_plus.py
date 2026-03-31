from __future__ import annotations

import threading
import time
import traceback
from collections import deque

import numpy as np

import settings
from utils.workwear_policy import evaluate_workwear_compliance, get_person_crop
from violation_module.vio_workwear_missing import WorkwearMissingViolation


class SimpleIoUTracker:
    """基于 IoU 的帧间目标关联，为每个人员分配稳定的 track_id。

    固定机位、帧间隔 2 秒左右的加油站场景下，
    IoU 贪心匹配足够区分连续出现的同一人和不同人。

    max_age 参数控制丢失容忍：当某 track 连续 max_age 帧未被匹配到时才移除，
    避免单帧漏检导致同一人被切成新 track。
    """

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 2):
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
        """对当前帧的 person_contexts 分配 track_id 并返回。

        贪心匹配：按 IoU 从大到小配对，超过阈值沿用旧 track_id，否则分配新 ID。
        未匹配的旧 track 在 max_age 帧内保留，超龄后移除。
        """
        if not person_contexts:
            self._prev_tracks = [
                {**t, "age": t.get("age", 0) + 1}
                for t in self._prev_tracks
                if t.get("age", 0) + 1 <= self.max_age
            ]
            return person_contexts

        prev = self._prev_tracks
        used_prev: set[int] = set()
        used_curr: set[int] = set()

        pairs: list[tuple[float, int, int]] = []
        for ci, ctx in enumerate(person_contexts):
            for pi, pt in enumerate(prev):
                iou = self._compute_iou(ctx.get("bbox", []), pt.get("bbox", []))
                if iou >= self.iou_threshold:
                    pairs.append((iou, ci, pi))
        pairs.sort(key=lambda t: t[0], reverse=True)

        assignments: dict[int, int] = {}
        for _iou, ci, pi in pairs:
            if ci in used_curr or pi in used_prev:
                continue
            assignments[ci] = prev[pi]["track_id"]
            used_curr.add(ci)
            used_prev.add(pi)

        for ci, ctx in enumerate(person_contexts):
            tid = assignments.get(ci, self._alloc_id())
            ctx["track_id"] = tid

        new_prev = [
            {"bbox": ctx.get("bbox", []), "track_id": ctx["track_id"], "age": 0}
            for ctx in person_contexts
        ]
        for pi, pt in enumerate(prev):
            if pi not in used_prev and pt.get("age", 0) + 1 <= self.max_age:
                new_prev.append({**pt, "age": pt.get("age", 0) + 1})
        self._prev_tracks = new_prev

        return person_contexts

    def reset(self):
        self._prev_tracks = []
        self._next_id = 0


class HKCustomThread(threading.Thread):
    def __init__(self, camera, app):
        super().__init__(daemon=True, name=f"HKCustomThread-{camera.id}")
        self.camera = camera
        self.app = app
        self._running = threading.Event()
        self._running.set()
        self.window = deque(maxlen=getattr(settings, "TEMPORAL_WINDOW_SIZE", 5))
        self.tracker = SimpleIoUTracker(
            iou_threshold=0.3,
            max_age=getattr(settings, "TRACKER_MAX_AGE", 2),
        )
        self.last_processed_ts = None
        self.last_alert_ts = None
        self._pipeline_error_logged = False

    def stop(self):
        self._running.clear()

    def fetch_frame(self):
        """从全局缓存读取当前摄像头最新帧；若无新帧则返回 (None, None)。"""
        entry = self.app.config["hk_frame_cache"].get(self.camera.id)
        if entry is None:
            return None, None
        frame = entry.get("frame")
        timestamp = entry.get("ts")
        if frame is None or timestamp is None:
            return None, None
        if timestamp == self.last_processed_ts:
            return None, None
        self.last_processed_ts = timestamp
        return frame.copy(), timestamp

    def detect_persons(self, frame):
        """对整帧执行人员检测，返回检测器统一格式结果列表。"""
        detector = self.app.config.get("person_model")
        if detector is None:
            return []
        return detector.infer(frame, conf_threshold=getattr(settings, "PERSON_CONF", 0.55))

    def _pipeline_ready(self) -> bool:
        if self.app.config.get("detection_pipeline_ready", False):
            self._pipeline_error_logged = False
            return True

        if not self._pipeline_error_logged:
            init_error = self.app.config.get("detection_model_init_error") or (
                "person_model / workwear_model 未完成初始化"
            )
            self.app.logger.error(
                "camera %s 检测链路未就绪，线程等待中: %s",
                self.camera.id,
                init_error,
            )
            self._pipeline_error_logged = True
        return False

    def _in_roi(self, bbox: list) -> bool:
        """判断目标是否在 ROI 区域内（重叠比例策略）。

        计算人框与 ROI 的交叠面积占人框面积的比例，
        达到 ROI_MIN_OVERLAP_RATIO 阈值即视为在监管区域内。
        """
        roi = getattr(self.camera, "roi", None)
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
        overlap_ratio = inter_area / person_area
        min_ratio = getattr(settings, "ROI_MIN_OVERLAP_RATIO", 0.5)
        return overlap_ratio >= min_ratio

    def build_person_contexts(self, frame: np.ndarray, persons: list) -> list[dict]:
        """为每个有效人员构建包含工服检测结果的上下文字典。

        裁剪策略和合规判定均由 utils.workwear_policy 统一提供。
        """
        workwear_detector = self.app.config.get("workwear_model")
        if workwear_detector is None:
            return []
        min_area = getattr(settings, "MIN_PERSON_BOX_AREA", 3000)
        area_mode = getattr(settings, "MIN_PERSON_AREA_MODE", "absolute")
        area_ratio_threshold = getattr(settings, "MIN_PERSON_AREA_RATIO", 0.005)
        workwear_conf = getattr(settings, "WORKWEAR_CONF", 0.45)
        frame_area = frame.shape[0] * frame.shape[1] if area_mode == "relative" else 0

        contexts: list[dict] = []
        for person in persons:
            bbox = person.get("bbox", [])
            if len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            area = max(0, x2 - x1) * max(0, y2 - y1)
            if area_mode == "relative":
                if frame_area > 0 and area / frame_area < area_ratio_threshold:
                    continue
            else:
                if area < min_area:
                    continue

            crop = get_person_crop(frame, bbox)

            workwear_items: list[dict] = []
            if crop is not None and crop.size > 0:
                workwear_items = workwear_detector.infer(
                    crop,
                    conf_threshold=workwear_conf,
                )

            has_workwear = evaluate_workwear_compliance(workwear_items)

            contexts.append(
                {
                    "bbox": bbox,
                    "confidence": float(person.get("confidence", 0.0)),
                    "label": person.get("label", "person"),
                    "area": area,
                    "in_roi": self._in_roi(bbox),
                    "workwear_items": workwear_items,
                    "has_workwear": has_workwear,
                }
            )
        return contexts

    def run_rule_engine(self) -> list | None:
        """对当前时间窗口执行工服违规规则判定。

        WorkwearMissingViolation.run() 内部完成证据图保存与数据库写入。
        触发违规时返回告警结果列表；窗口未达阈值或无有效人员时返回 None。
        """
        violation = WorkwearMissingViolation()
        frames = [item["frame"] for item in self.window]
        datetime_list = [item["timestamp"] for item in self.window]
        targets = list(self.window)
        vio_type = getattr(settings, "WORKWEAR_VIOLATION_TYPE", "workwear_missing")
        violation.init(
            frames=frames,
            datetime_list=datetime_list,
            targets=targets,
            vio_type=vio_type,
            camera_id=self.camera.id,
            station_id=getattr(self.camera, "station_id", None),
            dept_id=getattr(self.camera, "dept_id", None),
            sub_id=getattr(self.camera, "sub_id", None),
        )
        return violation.run()

    def _alert_suppressed(self, timestamp) -> bool:
        """判断当前时刻是否仍处于告警抑制窗口内，避免同一摄像头短时间重复报警。"""
        if self.last_alert_ts is None:
            return False
        suppression = getattr(settings, "alert_suppression_seconds", 300)
        return (timestamp - self.last_alert_ts).total_seconds() < suppression

    def _compute_window_span(self) -> str:
        """计算当前窗口首尾帧的时间跨度，用于日志输出。"""
        n = len(self.window)
        if n < 2:
            return f"{n}帧"
        try:
            first_ts = self.window[0]["timestamp"]
            last_ts = self.window[-1]["timestamp"]
            delta = (last_ts - first_ts).total_seconds()
            return f"{delta:.0f}s（{n}帧）"
        except Exception:
            return f"{n}帧"

    def emit_event(self, triggered, window_span: str = ""):
        """违规触发后记录日志。triggered 为 True（saving 已由 violation.run() 完成）。"""
        if not triggered:
            return
        span_info = f"，窗口跨度 {window_span}" if window_span else ""
        self.app.logger.warning(
            "camera %s 触发工服未穿戴违规告警，证据图已保存%s",
            self.camera.id,
            span_info,
        )

    def run(self):
        idle = getattr(settings, "thread_idle_sleep", 2)
        round_sleep = getattr(settings, "round_interval", 0) or idle

        recorder_manager = self.app.config["hk_recorder_thread_manager"]
        recorder_manager.register_camera(self.camera)
        self.app.logger.info("camera %s 工服检测线程启动", self.camera.id)

        try:
            while self._running.is_set():
                try:
                    if not self._pipeline_ready():
                        time.sleep(idle)
                        continue

                    frame, timestamp = self.fetch_frame()
                    if frame is None:
                        recorder_manager.run_once(app=self.app, cameras=[self.camera])
                        time.sleep(idle)
                        continue

                    persons = self.detect_persons(frame)
                    person_contexts = self.build_person_contexts(frame, persons)
                    person_contexts = self.tracker.update(person_contexts)
                    self.window.append(
                        {
                            "camera_id": self.camera.id,
                            "timestamp": timestamp,
                            "frame": frame,
                            "persons": person_contexts,
                        }
                    )

                    window_size = getattr(settings, "TEMPORAL_WINDOW_SIZE", 5)
                    if len(self.window) < window_size:
                        time.sleep(round_sleep)
                        continue

                    if self._alert_suppressed(timestamp):
                        self.window.clear()
                        self.tracker.reset()
                        time.sleep(round_sleep)
                        continue

                    triggered_list = self.run_rule_engine()
                    if triggered_list:
                        self.last_alert_ts = timestamp
                        window_span = self._compute_window_span()
                        self.window.clear()
                        self.tracker.reset()
                        for triggered in triggered_list:
                            self.emit_event(triggered, window_span=window_span)

                    time.sleep(round_sleep)

                except Exception as exc:  # pragma: no cover
                    trace = traceback.format_exc()
                    self.app.logger.error(
                        "camera %s 检测循环异常: %s\n%s", self.camera.id, exc, trace
                    )
                    time.sleep(idle)
        finally:
            recorder_manager.unregister_camera(self.camera.id)
            self.app.logger.info("camera %s 工服检测线程已停止", self.camera.id)


class ThreadManager:
    def __init__(self, app=None):
        self.app = app
        self.threads: dict[str, HKCustomThread] = {}
        self._lock = threading.Lock()

    def bind_app(self, app):
        self.app = app

    def add_thread(self, camera) -> bool:
        if self.app is None:
            return False
        if not self.app.config.get("detection_pipeline_ready", False):
            init_error = self.app.config.get("detection_model_init_error") or (
                "YOLOv8 检测模型未完成初始化"
            )
            self.app.logger.error(
                "camera %s 检测线程启动失败: %s",
                camera.id,
                init_error,
            )
            return False

        camera_id = str(camera.id)
        with self._lock:
            existing = self.threads.get(camera_id)
            if existing is not None and existing.is_alive():
                return False
            new_thread = HKCustomThread(camera, self.app)
            self.threads[camera_id] = new_thread
            new_thread.start()
            return True

    def stop_thread(self, camera_id) -> bool:
        camera_id = str(camera_id)
        with self._lock:
            thread = self.threads.get(camera_id)
        if thread is None:
            return False
        thread.stop()
        thread.join(timeout=3.0)
        with self._lock:
            if not thread.is_alive():
                self.threads.pop(camera_id, None)
                return True
            if self.app is not None:
                self.app.logger.warning("camera %s 检测线程未在超时时间内退出，保留跟踪", camera_id)
            return False

    def stop_all_threads(self, app=None):
        app = app or self.app
        camera_ids = list(self.threads.keys())
        for camera_id in camera_ids:
            self.stop_thread(camera_id)
        if app is not None:
            app.logger.warning("所有工服检测线程已停止")

    def restart_all_threads(self, app=None):
        """重启所有启用摄像头的检测线程。

        直接查询数据库获取当前启用的摄像头列表，与 camera_registry 缓存解耦，
        确保重启时能反映最新的摄像头启用状态。错峰启动避免资源竞争。
        """
        app = app or self.app
        if app is None:
            return

        self.stop_all_threads(app)

        from applications.models import HKCamera

        with app.app_context():
            cameras = HKCamera.query.filter_by(is_delete=0, enable=1).all()
            for camera in cameras:
                if self.add_thread(camera):
                    app.logger.info("重启工服检测线程 camera %s", camera.id)
                    time.sleep(0.2)
                else:
                    app.logger.warning("工服检测线程 camera %s 重启失败或已在运行", camera.id)
