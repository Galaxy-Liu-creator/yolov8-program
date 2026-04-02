from __future__ import annotations

import logging
from pathlib import Path

import cv2

import settings

LOGGER = logging.getLogger(__name__)

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class HKStream:
    """海康取流最小兼容封装。

    当前版本优先解决“项目先运行起来”的问题，因此先兼容：
    - 本地单张图片
    - 本地视频文件
    - RTSP / 网络视频流

    它保留旧项目 `HKStream` 的核心接口形状：
    - `login(...)`
    - `play_preview(channels)`
    - `logout()`
    - `IMAGES`

    后续若需要接回完整 HCNetSDK，可在此文件内继续扩展，而不影响上层采图调用方。
    """

    def __init__(self, team: str, stream_url: str | None = None, frame_path: str | None = None):
        self.team = team
        self.stream_url = stream_url
        self.frame_path = frame_path

        self.DEV_IP: str | None = None
        self.DEV_PORT: int | None = None
        self.DEV_USER_NAME: str | None = None
        self.DEV_PASSWORD: str | None = None

        self.CHANNELS: dict[str, int] = {}
        self.IMAGES: dict[str, object] = {}
        self._captures: dict[str, cv2.VideoCapture] = {}
        self.source_signature: tuple | None = None

    def login(self, ip, port, username, password):
        self.DEV_IP = ip
        self.DEV_PORT = int(port) if port else int(getattr(settings, "DEFAULT_CAMERA_PORT", 8000))
        self.DEV_USER_NAME = username
        self.DEV_PASSWORD = password

        ready = bool(self.frame_path or self.stream_url or ip)
        if not ready:
            LOGGER.warning("%s HKStream login skipped: missing ip/stream source", self.team)
        return ready

    def configure(self, *, stream_url: str | None = None, frame_path: str | None = None):
        self.stream_url = stream_url
        self.frame_path = frame_path

    def play_preview(self, channels):
        self.CHANNELS = {}
        self.IMAGES = {}
        for channel_name, channel_id in (channels or {}).items():
            channel_key = str(channel_name)
            try:
                normalized_channel = int(channel_id)
            except (TypeError, ValueError):
                normalized_channel = int(getattr(settings, "DEFAULT_CAMERA_CHANNEL", 1))
            self.CHANNELS[channel_key] = normalized_channel
            self.IMAGES[channel_key] = None
        return list(self.CHANNELS.keys())

    def _normalize_channel_code(self, channel_id: int) -> str:
        if channel_id >= 100:
            return str(channel_id)
        return f"{channel_id}01"

    def _build_rtsp_url(self, channel_id: int) -> str | None:
        if self.stream_url:
            return self.stream_url
        if not self.DEV_IP:
            return None

        port = int(getattr(settings, "RTSP_PORT", 554))
        template = getattr(
            settings,
            "RTSP_PATH_TEMPLATE",
            "rtsp://{username}:{password}@{ip}:{port}/Streaming/Channels/{channel_code}",
        )
        return template.format(
            username=self.DEV_USER_NAME or "",
            password=self.DEV_PASSWORD or "",
            ip=self.DEV_IP,
            port=port,
            channel=channel_id,
            channel_code=self._normalize_channel_code(channel_id),
        )

    @staticmethod
    def _open_capture(source: str):
        capture = cv2.VideoCapture(source)
        if capture is None or not capture.isOpened():
            if capture is not None:
                capture.release()
            return None
        return capture

    def _get_capture(self, channel_name: str, source: str):
        capture = self._captures.get(channel_name)
        if capture is not None and capture.isOpened():
            return capture

        capture = self._open_capture(source)
        if capture is not None:
            self._captures[channel_name] = capture
        return capture

    def read_frame(self, channel_name: str):
        channel_name = str(channel_name)
        if channel_name not in self.CHANNELS:
            return None

        frame_path = self.frame_path
        if frame_path:
            path_obj = Path(frame_path)
            if path_obj.is_file() and path_obj.suffix.lower() in _IMAGE_EXTS:
                frame = cv2.imread(str(path_obj))
                if frame is not None:
                    self.IMAGES[channel_name] = frame
                return frame

        channel_id = self.CHANNELS[channel_name]
        source = None
        if frame_path:
            path_obj = Path(frame_path)
            if path_obj.is_file():
                source = str(path_obj)
        if source is None:
            source = self._build_rtsp_url(channel_id)
        if not source:
            return None

        capture = self._get_capture(channel_name, source)
        if capture is None:
            return None

        ok, frame = capture.read()
        if not ok or frame is None or getattr(frame, "size", 0) == 0:
            capture.release()
            self._captures.pop(channel_name, None)
            capture = self._get_capture(channel_name, source)
            if capture is None:
                return None
            ok, frame = capture.read()
            if not ok or frame is None or getattr(frame, "size", 0) == 0:
                return None

        self.IMAGES[channel_name] = frame
        return frame

    def logout(self):
        for capture in self._captures.values():
            try:
                capture.release()
            except Exception:
                LOGGER.exception("%s release capture failed", self.team)
        self._captures.clear()
