from __future__ import annotations

import logging

import settings
from utils.workwear_policy import evaluate_workwear_compliance
from violation_module.base import BaseVio

LOGGER = logging.getLogger(__name__)


class WorkwearMissingViolation(BaseVio):
    """YOLOv8 作业区人员疑似未穿工服规则。

    规则口径：
    1. 只统计 ROI 内的人体目标（面积过滤已由上游 build_person_contexts 完成）。
    2. 按 track_id 维度做时序判定：同一人连续违规才触发，不同人拼出的违规帧不累计。
    3. track 至少出现 MIN_TRACK_APPEAR_FRAMES 帧才进入违规判定，过滤短暂掠过目标。
    4. 任一 track 的「违规帧数 / 该 track 出现帧数 >= trigger_ratio」即触发告警。
    5. 证据图只保留触发 track 的标注，不混入其他 track 的数据。
    """

    rule_code = "workwear_missing"
    rule_name = getattr(settings, "WORKWEAR_VIOLATION_NAME", "作业区人员疑似未穿工服")

    def run(self) -> list | None:
        """执行工服违规规则判定，返回所有触发 track 的告警结果列表。

        返回值：
        - list: 至少有一个 track 触发时，返回各 track 的 save() 结果列表
        - None: 无触发
        """
        workwear_labels = self._load_workwear_labels()
        if not workwear_labels:
            LOGGER.warning(
                "WORKWEAR_LABELS is empty, skip %s rule evaluation.",
                self.rule_code,
            )
            self.plot_targets.clear()
            return None

        trigger_ratio = self._load_trigger_ratio()
        min_appear = self._load_min_track_appear()

        if not self.targets:
            self.plot_targets.clear()
            return None

        track_stats: dict[int, dict] = {}

        for frame_idx, frame_item in enumerate(self.targets):
            persons = self._extract_persons(frame_item)
            for person in persons:
                if not self._is_valid_person(person):
                    continue

                track_id = person.get("track_id")
                if track_id is None:
                    continue

                if track_id not in track_stats:
                    track_stats[track_id] = {
                        "appear": 0,
                        "violation": 0,
                        "best_conf": 0.0,
                    }

                track_stats[track_id]["appear"] += 1

                if not self._has_compliant_workwear(person, workwear_labels):
                    track_stats[track_id]["violation"] += 1
                    self._add_person_to_plot(frame_idx, person)
                    conf = float(person.get("confidence", 0.0))
                    if conf > track_stats[track_id]["best_conf"]:
                        track_stats[track_id]["best_conf"] = conf

        if not track_stats:
            self.plot_targets.clear()
            return None

        triggered_tracks: list[int] = []
        for tid, stats in track_stats.items():
            if stats["appear"] < min_appear:
                continue
            if stats["appear"] == 0:
                continue
            ratio = stats["violation"] / stats["appear"]
            if ratio >= trigger_ratio:
                triggered_tracks.append(tid)

        if not triggered_tracks or not self.plot_targets:
            self.plot_targets.clear()
            return None

        all_plot_targets = dict(self.plot_targets)
        results = []
        for tid in triggered_tracks:
            self.plot_targets = dict(all_plot_targets)
            self._filter_plot_targets_by_track(tid)
            if not self.plot_targets:
                continue
            result = self.save(self.rule_name)
            if result:
                results.append(result)

        self.plot_targets.clear()
        return results if results else None

    @staticmethod
    def _extract_persons(frame_item: dict | object) -> list[dict]:
        if not isinstance(frame_item, dict):
            return []

        persons = frame_item.get("persons", [])
        if not isinstance(persons, list):
            return []

        return [person for person in persons if isinstance(person, dict)]

    @staticmethod
    def _load_workwear_labels() -> set[str]:
        raw_labels = getattr(settings, "WORKWEAR_LABELS", [])
        if not isinstance(raw_labels, (list, tuple, set)):
            return set()

        return {
            str(label).strip()
            for label in raw_labels
            if str(label).strip()
        }

    @staticmethod
    def _load_trigger_ratio() -> float:
        raw_value = getattr(settings, "TEMPORAL_TRIGGER_RATIO", 0.6)
        try:
            return min(max(float(raw_value), 0.0), 1.0)
        except (TypeError, ValueError):
            return 0.6

    @staticmethod
    def _load_min_track_appear() -> int:
        raw_value = getattr(settings, "MIN_TRACK_APPEAR_FRAMES", 2)
        try:
            return max(int(raw_value), 1)
        except (TypeError, ValueError):
            return 2

    @staticmethod
    def _is_valid_person(person: dict) -> bool:
        """校验人员上下文是否有效。

        面积过滤已由上游 build_person_contexts 统一完成，
        此处仅做 bbox 格式校验、ROI 判定和基本面积正值校验。
        """
        bbox = person.get("bbox", [])
        if not isinstance(bbox, list) or len(bbox) != 4:
            return False

        if not person.get("in_roi", True):
            return False

        area = person.get("area", 0)
        try:
            area_value = float(area)
        except (TypeError, ValueError):
            return False

        return area_value > 0

    @staticmethod
    def _has_compliant_workwear(person: dict, workwear_labels: set[str]) -> bool:
        workwear_items = person.get("workwear_items", [])
        return evaluate_workwear_compliance(workwear_items, workwear_labels=workwear_labels)

    def _add_person_to_plot(self, frame_idx: int, person: dict) -> None:
        bbox = person.get("bbox", [])
        if len(bbox) != 4:
            return

        try:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            confidence = float(person.get("confidence", 0.0))
        except (TypeError, ValueError):
            return

        track_id = person.get("track_id")
        person_target = [x1, y1, x2, y2, confidence, "person"]
        self.add_plot_targets(frame_idx, [person_target, [], confidence, track_id])

    def _filter_plot_targets_by_track(self, triggered_track) -> None:
        """只保留属于触发 track 的证据标注，确保证据图与触发目标一致。"""
        filtered: dict = {}
        for frame_idx, target_lists in self.plot_targets.items():
            kept = [
                t for t in target_lists
                if isinstance(t, list) and len(t) >= 4 and t[3] == triggered_track
            ]
            if kept:
                filtered[frame_idx] = kept
        self.plot_targets = filtered
