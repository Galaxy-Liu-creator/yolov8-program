from __future__ import annotations

import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import cv2

from hk.hksdk.device import HKStream
import settings

# 连续抓图失败计数，达到阈值时升级为 warning 日志（每摄像头独立计数）
_FAIL_COUNTS: dict[int, int] = {}
_FAIL_WARN_THRESHOLD = 5
_STREAM_CLIENTS: dict[int, HKStream] = {}
_DIRECTORY_CURSOR: dict[int, int] = {}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".mpeg", ".mpg"}


def _compute_frame_hash(image, size: int = 8) -> bytes:
    """计算帧内容的轻量级感知哈希，用于检测图像内容是否真正变化。

    将图像缩放到 size x size 灰度图后做均值二值化，
    性能开销极低，足以区分"同一张静态图"和"真正的新帧"。
    """
    small = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if len(small.shape) == 3 else small
    mean_val = gray.mean()
    return bytes(int(px > mean_val) for px in gray.flatten())


def _camera_source_signature(camera) -> tuple:
    return (
        getattr(camera, "frame_path", None),
        getattr(camera, "stream_url", None),
        getattr(camera, "ip", None),
        getattr(camera, "port", None),
        getattr(camera, "username", None),
        getattr(camera, "password", None),
        getattr(camera, "channel", None),
    )


def _read_first_frame_from_video(video_path: Path):
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            return None
        ok, frame = capture.read()
        if ok and frame is not None and getattr(frame, "size", 0) > 0:
            return frame
        return None
    finally:
        capture.release()


def _read_from_frame_path(camera):
    frame_path = getattr(camera, "frame_path", None)
    if not frame_path:
        return None

    path_obj = Path(frame_path)
    if not path_obj.exists():
        return None

    camera_id = int(camera.id)
    if path_obj.is_file():
        suffix = path_obj.suffix.lower()
        if suffix in _IMAGE_EXTS:
            return cv2.imread(str(path_obj))
        return None

    if not path_obj.is_dir():
        return None

    candidates = sorted(
        p for p in path_obj.iterdir()
        if p.is_file() and p.suffix.lower() in (_IMAGE_EXTS | _VIDEO_EXTS)
    )
    if not candidates:
        return None

    cursor = _DIRECTORY_CURSOR.get(camera_id, 0)
    selected = candidates[cursor % len(candidates)]
    _DIRECTORY_CURSOR[camera_id] = (cursor + 1) % len(candidates)
    if selected.suffix.lower() in _IMAGE_EXTS:
        return cv2.imread(str(selected))
    return _read_first_frame_from_video(selected)


def _get_stream_client(camera):
    camera_id = int(camera.id)
    signature = _camera_source_signature(camera)
    client = _STREAM_CLIENTS.get(camera_id)

    if client is None or getattr(client, "source_signature", None) != signature:
        if client is not None:
            client.logout()
        client = HKStream(
            team=f"camera-{camera_id}",
            stream_url=getattr(camera, "stream_url", None) or getattr(settings, "DEFAULT_STREAM_URL", None),
            frame_path=getattr(camera, "frame_path", None),
        )
        port = getattr(camera, "port", None) or getattr(settings, "DEFAULT_CAMERA_PORT", 8000)
        channel = getattr(camera, "channel", None) or getattr(settings, "DEFAULT_CAMERA_CHANNEL", 1)
        if not client.login(
            getattr(camera, "ip", None),
            port,
            getattr(camera, "username", None),
            getattr(camera, "password", None),
        ):
            return None
        client.play_preview({str(camera.id): channel})
        client.source_signature = signature
        _STREAM_CLIENTS[camera_id] = client

    return client


def _read_frame_from_camera(camera):
    """从摄像头读取一帧。

    读取优先级：
    1. frame_path：本地图像回放（调试）
    2. stream_url：视频文件 / RTSP / OpenCV 支持的其他流

    若未配置或读取失败则返回 None，避免把占位图当作真实检测输入。
    """
    local_frame = _read_from_frame_path(camera)
    if local_frame is not None and getattr(local_frame, "size", 0) > 0:
        return local_frame

    client = _get_stream_client(camera)
    if client is None:
        return None
    return client.read_frame(str(camera.id))


def get_img(cameras, app):
    """遍历启用的摄像头，抓取最新帧并写入全局缓存。
    每个摄像头只保留最新帧，旧帧由新帧直接覆盖。"""
    for camera in cameras:
        if int(getattr(camera, "enable", 0)) != 1:
            continue

        cid = int(camera.id)
        image = _read_frame_from_camera(camera)

        if image is None or image.size == 0:
            _FAIL_COUNTS[cid] = _FAIL_COUNTS.get(cid, 0) + 1
            fail_count = _FAIL_COUNTS[cid]
            app.config["hk_frame_cache"].pop(cid, None)
            if fail_count == 1 or fail_count % _FAIL_WARN_THRESHOLD == 0:
                app.logger.warning(
                    "camera %s 连续第 %d 次抓图失败，请检查设备连接、frame_path 或 stream_url 配置",
                    cid,
                    fail_count,
                )
            continue

        if _FAIL_COUNTS.get(cid, 0) > 0:
            app.logger.info("camera %s 抓图恢复正常", cid)
        _FAIL_COUNTS[cid] = 0

        new_hash = _compute_frame_hash(image)
        existing = app.config["hk_frame_cache"].get(cid)
        if existing and existing.get("frame_hash") == new_hash:
            continue

        app.config["hk_frame_cache"][cid] = {
            "frame": image, "ts": datetime.now(), "frame_hash": new_hash,
        }


class HKRecorderThread(threading.Thread):
    def __init__(self, manager, camera):
        super().__init__(daemon=True, name=f"HKRecorderThread-{camera.id}")
        self.manager = manager
        self.camera = camera

    def run(self):
        self.manager.run_once(cameras=[self.camera])


class HKRecorder:
    def __init__(self, manager, camera):
        self.manager = manager
        self.camera = camera

    def run(self, app):
        self.manager.run_once(app=app, cameras=[self.camera])


class HKRecorderThreadManager:
    def __init__(self, app=None):
        self.app = app
        self.cameras: dict[str, object] = {}
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()

    def bind_app(self, app):
        self.app = app

    def register_camera(self, camera):
        with self._lock:
            self.cameras[str(camera.id)] = camera

    def unregister_camera(self, camera_id):
        with self._lock:
            self.cameras.pop(str(camera_id), None)
        try:
            cache_key = int(camera_id)
        except (TypeError, ValueError):
            cache_key = camera_id
        _FAIL_COUNTS.pop(cache_key, None)
        _DIRECTORY_CURSOR.pop(cache_key, None)
        stream_client = _STREAM_CLIENTS.pop(cache_key, None)
        if stream_client is not None:
            stream_client.logout()
        if self.app is not None:
            self.app.config.get("hk_frame_cache", {}).pop(cache_key, None)

    def list_cameras(self):
        with self._lock:
            return list(self.cameras.values())

    def run_once(self, app=None, cameras=None):
        app = app or self.app
        if app is None:
            return

        camera_list = self.list_cameras() if cameras is None else cameras
        try:
            get_img(camera_list, app)
        except Exception as exc:  # pragma: no cover - 依赖运行环境
            trace = traceback.format_exc()
            app.logger.error("抓图失败: %s\n%s", exc, trace)

    def _loop(self):
        if self.app is None:
            return

        with self.app.app_context():
            while self._running:
                self.run_once(self.app)
                time.sleep(settings.get_image_interval)

    def start_background(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="HKRecorderThreadManager",
        )
        self._thread.start()

    def stop_background(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def run(self, app):
        self.bind_app(app)
        self.run_once(app=app)
