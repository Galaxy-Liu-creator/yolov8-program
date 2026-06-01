# -*- coding:utf-8 -*-
import datetime
import os
import time
import traceback
import uuid
from threading import Thread
from collections import deque
from typing import Any, Dict, List, Optional

import cv2
import psutil

from pathlib import Path

# 导入项目配置
import settings
# 导入工具类
from utils.getrycsid import get_rycsid
from utils.logger import logger
from utils.models import get_models, seek_targets
from utils.pose import run_pose
from utils.qianzhi import Logic0
from utils.tools import save_fenxi
from utils.torch_utils import select_device, time_synchronized
from utils.audio_controller import AudioController

# 前端配置（阈值）同步：优先使用前端接口数据，失败时回退到 settings
try:
    from api.frontend_data_extract import frontend_threshold_sync_loop, sync_frontend_thresholds_once
except ImportError:
    frontend_threshold_sync_loop = None


    def sync_frontend_thresholds_once():
        return

# 复用 api/sapi_api.py 作为 SAPI 接口层（由该层对接远端 BASE_URL）
import api.sapi_api as sapi_api
from api.sapi_client import send_risk_event_media
from api.sapi_risk_fetch import get_violation_display_name, get_violation_full_info
from api.sapi_sign import build_signature
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 违规类型与大类信息统一由 api/sapi_risk_fetch.py 提供
# main_test3 不再维护本地 API_RISK_* 映射缓存

# 违规上传时间窗口缓存：{"channel:category": last_upload_time}
VIOLATION_UPLOAD_WINDOW = {}
# 上传时间窗口（秒），可根据需要调整
UPLOAD_WINDOW_SECONDS = 60  # 1分钟

# 违规播报时间窗口缓存：{"channel:category": last_alarm_time}
VIOLATION_ALARM_WINDOW = {}
# 播报时间窗口（秒）
ALARM_WINDOW_SECONDS = 60

# ================= 音频控制器初始化 =================
# 仅在 settings.AUDIO_ENABLED = True 时初始化，避免无音频设备报错
audio_controller = AudioController() if settings.AUDIO_ENABLED else None


def get_cameras() -> List[Dict[str, Any]]:
    """直接从 SAPI 获取摄像头列表，不经过录像机匹配"""

    def _build_signed_params(params: Dict[str, Any]) -> Dict[str, Any]:
        p = dict(params)
        p["timestamp"] = str(int(time.time()))
        p["signature"] = build_signature(p, settings.SAPI_SIGN_SECRET)
        return p

    base_url = getattr(settings, "SAPI_BASE_URL", "").rstrip("/")
    if not base_url:
        logger.warning("SAPI_BASE_URL 未配置")
        return []

    url = f"{base_url}/sapi/biz/camera/page"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    params = {
        "cameraName": "",
        "recorderId": "",
        "cameraType": "",
        "status": "",
        "current": "1",
        "size": "200",
    }

    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=Retry(total=3)))
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=3)))

    try:
        resp = session.get(url, params=_build_signed_params(params), headers=headers, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"获取摄像头列表失败: {e}")
        return []
    finally:
        session.close()

    if not isinstance(data, dict) or data.get("code") not in [0, "0", 200, "200"]:
        logger.error(f"摄像头接口返回异常: {data}")
        return []

    cameras = data.get("data", {}).get("records", [])
    logger.info(f"从 SAPI 获取到 {len(cameras)} 个摄像头")
    return cameras


def get_camera_rtsp_url(camera: Dict[str, Any]) -> str:
    """构建海康摄像头RTSP URL"""
    ip = camera.get("ip", "")
    port = camera.get("port", 554)
    username = camera.get("username", "admin")
    password = camera.get("password", "")
    channel = camera.get("channel", 1)

    if not ip:
        return ""

    return f"rtsp://{username}:{password}@{ip}:{port}/h264/ch{channel}/main/av_stream"


def _extract_rtsp_url(camera_item: dict) -> str:
    """兼容不同字段名提取 RTSP 地址，优先使用摄像头详细信息构建。"""
    # 优先使用摄像头详细信息构建 RTSP URL
    rtsp_url = get_camera_rtsp_url(camera_item)
    if rtsp_url:
        return rtsp_url

    # 兼容不同字段名提取 RTSP 地址
    for key in ["rtspUrl", "rtsp_url", "streamUrl", "url", "cameraUrl", "playUrl"]:
        v = camera_item.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()

    return ""


class FrontendCameraStream:
    """
    多摄像头实时流（来源：前端摄像头管理接口）。
    支持两种检测模式：
    - parallel（并行）：同时处理所有摄像头的帧
    - polling（轮询）：按顺序逐个处理摄像头
    """

    def __init__(self, camera_items, target_fps=5):
        self.target_fps = target_fps
        self.camera_items = camera_items
        self.caps = {}  # channel -> (cap, rtsp)
        self.VIDEO_FAMES = {}  # 与现有逻辑保持字段名兼容
        self.channels = []
        self.FRAMES_COUNT = 0
        self.count = -1
        self._reader_thread = None
        self._running = False
        self.detection_mode = "parallel"  # 默认并行模式
        self._polling_index = 0  # 轮询模式下的当前索引

        max_len = settings.VIDEO_CRT * settings.VIDEO_CRT_SECONDS

        for item in camera_items:
            camera_id = str(item.get("id") or "").strip()
            camera_name = str(item.get("cameraName") or "").strip()
            channel = camera_name or camera_id
            rtsp_url = _extract_rtsp_url(item)

            if not channel or not rtsp_url:
                logger.warning(f"摄像头信息不完整，跳过: id={camera_id}, name={camera_name}, rtsp={rtsp_url}")
                continue

            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                logger.error(f"打开摄像头流失败: {channel} -> {rtsp_url}")
                continue

            self.caps[channel] = (cap, rtsp_url)
            self.VIDEO_FAMES[channel] = deque(maxlen=max_len)
            self.channels.append(channel)

        if not self.channels:
            raise RuntimeError("没有可用的摄像头流")

        logger.info(f"\n摄像头连接成功:")
        for channel in self.channels:
            rtsp_url = self.caps[channel][1]
            logger.info(f"  - {channel}: {rtsp_url}")

    def start(self):
        self._running = True
        self._reader_thread = Thread(target=self._update, daemon=True)
        self._reader_thread.start()

        max_len = settings.VIDEO_CRT * settings.VIDEO_CRT_SECONDS
        logger.info(f"使用前端摄像头作为输入源，等待缓冲帧填充（{max_len} 帧）")
        while self._running:
            if all(len(self.VIDEO_FAMES[cj]) >= max_len for cj in self.channels):
                break
            time.sleep(0.5)

    def _update(self):
        """并行读取所有摄像头的帧"""
        while True:
            any_alive = False
            for cj in self.channels:
                cap, rtsp_url = self.caps[cj]
                if not cap.isOpened():
                    logger.warning(f"摄像头连接已断开: {cj} -> {rtsp_url}")
                    continue

                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(f"读取摄像头帧失败: {cj}")
                    continue

                any_alive = True
                self.VIDEO_FAMES[cj].append(frame)

            if not any_alive:
                time.sleep(1.0)
                continue

            self.FRAMES_COUNT += 1
            time.sleep(1.0 / max(self.target_fps, 1))

    def __iter__(self):
        self.count = -1
        self._polling_index = 0
        return self

    def __next__(self):
        if (not self._running) and (not self._reader_thread or not self._reader_thread.is_alive()):
            raise StopIteration

        self.count += 1

        # 根据检测模式返回不同的结果
        if self.detection_mode == "polling":
            # 轮询模式：每次只返回一个摄像头的帧
            if not self.channels:
                raise StopIteration

            channel_name = self.channels[self._polling_index]
            frames = [list(self.VIDEO_FAMES[channel_name])]

            # 移动到下一个摄像头
            self._polling_index = (self._polling_index + 1) % len(self.channels)

            logger.debug(f"[轮询模式] 当前检测: {channel_name} (第{self._polling_index}/{len(self.channels)})")
            return [channel_name], frames
        else:
            # 并行模式：同时返回所有摄像头的帧
            channels_name = []
            frames = []
            for cj in self.channels:
                channels_name.append(cj)
                frames.append(list(self.VIDEO_FAMES[cj]))
            return channels_name, frames

    def release(self):
        """释放所有摄像头资源"""
        self._running = False
        for channel, (cap, rtsp_url) in self.caps.items():
            try:
                cap.release()
                logger.info(f"摄像头[{channel}]资源已释放")
            except Exception as e:
                logger.error(f"释放摄像头[{channel}]资源失败: {e}")


def get_camera_stream(detection_mode: str = "parallel"):
    """
    从 SAPI 直接获取摄像头列表，构建流对象。

    :param detection_mode: 检测模式，"parallel"（并行）或 "polling"（轮询）
    :return: (流对象, 通道列表)
    """
    camera_items = []

    # ========== 直接从 SAPI 获取摄像头列表（不经过录像机）==========
    for attempt in range(1, 4):
        camera_items = get_cameras()
        if camera_items:
            break
        logger.warning(f"第{attempt}/3次获取摄像头列表为空，2秒后重试")
        time.sleep(2)

    if not camera_items:
        logger.error("未获取到任何摄像头数据")
        return None, []

    # ========== 多摄像头检测方案选择 ==========
    logger.info(f"\n{'=' * 60}")
    logger.info(f"多摄像头检测方案: {detection_mode}")
    logger.info(f"摄像头总数: {len(camera_items)}")
    logger.info(f"{'=' * 60}")

    try:
        # 使用 FrontendCameraStream 处理多路摄像头流
        dataset = FrontendCameraStream(camera_items)
        dataset.start()
        channels = list(dataset.channels)

        logger.info(f"\n检测到摄像头通道: {channels}")
        logger.info(f"检测模式: {detection_mode}")
        logger.info(f"{'=' * 60}")

        # 设置检测模式
        dataset.detection_mode = detection_mode

        return dataset, channels
    except Exception as e:
        logger.error(f"创建摄像头流失败: {e}")
        return None, []


def run_existing_sapi_api():
    """复用 api/sapi_api.py 中配置的远端 BASE_URL（不再启动本地 Flask 服务）。"""
    base_url = (getattr(sapi_api, "BASE_URL", "") or "").rstrip("/")
    if not base_url:
        logger.warning("api/sapi_api.py 未配置 BASE_URL，继续使用 settings.SAPI_BASE_URL")
        return

    settings.SAPI_BASE_URL = base_url
    logger.info(f"SAPI 统一走 api/sapi_api.py BASE_URL: {settings.SAPI_BASE_URL}")


def save_violation_evidence(cj: str, category: str, image, video_frames, frame_count: int):
    """在报警确认后留存违规图片和视频。"""
    # 检查时间窗口：同一通道同一类型在一段时间内只上传一次
    upload_key = f"{cj}:{category}"
    current_time = time.time()
    last_upload_time = VIOLATION_UPLOAD_WINDOW.get(upload_key, 0)

    if current_time - last_upload_time < UPLOAD_WINDOW_SECONDS:
        logger.info(f"[上传限流] {cj} {category} 在 {UPLOAD_WINDOW_SECONDS} 秒内已上传，跳过本次上传")
        return

    try:
        vio_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        vio_uuid = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}~{uuid.uuid4().hex[:8]}"
        # 将摄像头名称中的下划线替换为连字符，避免与文件名解析冲突
        cj_safe = cj.replace("_", "-")
        stem = f"{cj_safe}_{frame_count}_{category}_{vio_time}_{vio_uuid}"

        image_path = settings.VIO_IMAGE_PATH.joinpath(stem).with_suffix(".jpg")
        video_path = settings.VIO_VIDEO_PATH.joinpath(stem).with_suffix(".mp4")

        cv2.imencode(".jpg", image)[1].tofile(str(image_path))

        if video_frames:
            h, w = image.shape[:2]
            writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 5, (w, h))
            for frm in video_frames:
                if frm is None:
                    continue
                if frm.shape[0] != h or frm.shape[1] != w:
                    frm = cv2.resize(frm, (w, h))
                writer.write(frm)
            writer.release()

        # 更新上传时间戳
        VIOLATION_UPLOAD_WINDOW[upload_key] = current_time
        logger.info(f"违规证据留存完成: {stem}")
    except Exception as e:
        logger.error(f"违规证据留存失败: cj={cj}, category={category}, err={e}")


def _pick_single_violation_image(video_path: Path):
    """为一个违规视频选择唯一截图：优先同名图，其次同前缀最新图。"""
    exact_image = settings.VIO_IMAGE_PATH.joinpath(video_path.stem).with_suffix(".jpg")
    if exact_image.exists():
        return exact_image

    candidates = sorted(
        settings.VIO_IMAGE_PATH.glob(f"{video_path.stem}*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None

    if len(candidates) > 1:
        logger.info(f"违规事件 {video_path.stem} 匹配到{len(candidates)}张图，仅上传最新一张: {candidates[0].name}")
    return candidates[0]


def _parse_violation_stem(stem: str):
    """解析违规文件名：cj_frameCount_category_yyyy-mm-dd-HH-MM-SS_uuid。"""
    import re

    m = re.match(
        r"^(?P<cj>[^_]+)_(?P<frame_count>\d+)_(?P<category>.+)_(?P<vio_time>\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_(?P<vio_uuid>.+)$",
        stem,
    )
    if not m:
        return None
    return m.groupdict()


def _numeric_id_now() -> str:
    """生成纯数字且高概率不重复的ID（年月日时分秒+毫秒）。"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]


def upload_violation_media_to_sapi_loop():
    """将违规检测产出的图片/视频通过 SAPI 上传接口传递到前端侧。"""
    logger.info("SAPI违规媒体上传线程启动")

    # 启动时目录中已存在的历史违规文件不再上传，只处理运行后新产生的文件
    try:
        startup_existing_video_stems = {p.stem for p in settings.VIO_VIDEO_PATH.iterdir() if p.is_file()}
    except Exception:
        startup_existing_video_stems = set()
    if startup_existing_video_stems:
        logger.info(f"检测到历史违规视频{len(startup_existing_video_stems)}个，启动后将忽略历史文件，仅上传新违规")

    while True:
        try:
            for video_path in settings.VIO_VIDEO_PATH.iterdir():
                if video_path.stem in startup_existing_video_stems:
                    continue

                parsed = _parse_violation_stem(video_path.stem)
                if not parsed:
                    logger.warning(f"违规文件名不符合上传规范，跳过: {video_path.name}")
                    continue

                cj = parsed["cj"]
                category = parsed["category"]
                vio_time = parsed["vio_time"]
                image_path = _pick_single_violation_image(video_path)
                if not image_path or (not video_path.exists()):
                    continue

                try:
                    dis_time = datetime.datetime.strptime(vio_time, "%Y-%m-%d-%H-%M-%S")
                except Exception:
                    dis_time = datetime.datetime.now()

                event_code = _numeric_id_now()

                # 统一改为调用 api/sapi_risk_fetch.py：先英文转中文，再查完整违规信息
                display_name = get_violation_display_name(category)
                risk_info = get_violation_full_info(
                    category=category,
                    display_name=display_name,
                    force_refresh=False,
                )

                risk_type_id = str(risk_info.get("riskTypeId") or "")
                risk_type_name = str(risk_info.get("riskTypeName") or display_name or category)
                risk_type_level = str(risk_info.get("riskType") or settings.SAPI_DEFAULT_RISK_LEVEL)
                major_type = str(risk_info.get("majorTypeName") or risk_type_name)

                if not risk_type_id:
                    # 保底：避免后端报“违章类型ID不能为空”
                    risk_type_id = str(abs(hash(category)) % 1000000 + 1000000)

                logger.info(
                    f"[违规映射] category={category} display={display_name} "
                    f"riskTypeId={risk_type_id} riskTypeName={risk_type_name} "
                    f"riskType={risk_type_level} major={major_type} matched={risk_info.get('matched')}"
                )

                # eventName 优先使用前端类型名
                event_name = risk_type_name or settings.SAPI_EVENT_NAME_MAP.get(category, category)

                risk_payload = {
                    "eventCode": event_code,
                    "riskTypeId": risk_type_id,
                    "riskTypeName": risk_type_name,
                    "eventName": event_name,
                    "riskType": risk_type_level,
                    "eventSource": settings.SAPI_EVENT_SOURCE,
                    "eventTime": dis_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "eventDesc": settings.SAPI_EVENT_DESC_TEMPLATE.format(
                        category=category,
                        scene=cj,
                        team=settings.TEAM,
                        vio_uuid=event_code,
                    ),
                }

                try:
                    result = send_risk_event_media(risk_payload, image_path, video_path)
                    logger.info(f"SAPI违规媒体上传完成: {video_path.name}, result={result}")
                    # 上传成功后删除本地文件，避免重复上传
                    if isinstance(result, dict) and result.get("code") in [0, "0", 200, "200", None]:
                        image_path.unlink(missing_ok=True)
                        video_path.unlink(missing_ok=True)
                except Exception as e:
                    logger.error(f"SAPI违规媒体上传失败: {video_path.name}, err={e}")

        except Exception as loop_e:
            logger.error(f"SAPI违规媒体上传线程异常: {loop_e}")

        time.sleep(5)


def main():
    # ================= 1. 系统初始化与后台线程启动 =================

    # 启动硬件监控线程（CPU、内存、温度等）
    # post_monitor = Thread(target=device_info, daemon=True)
    # post_monitor.start()

    # 启动违规媒体上传线程（通过SAPI接口上传图片+视频）
    if settings.SAPI_ENABLED:
        post_sapi_media = Thread(target=upload_violation_media_to_sapi_loop, daemon=True)
        post_sapi_media.start()

    # 通过 api/sapi_api.py 的 BASE_URL 统一远端地址（不启动本地 Flask）
    run_existing_sapi_api()

    # 启动前端阈值同步（替代 SAPI 阈值来源）
    try:
        sync_frontend_thresholds_once()
    except Exception as e:
        logger.warning(f"前端阈值同步（启动时）失败: {e}")

    if frontend_threshold_sync_loop:
        post_frontend_thr = Thread(target=frontend_threshold_sync_loop, daemon=True)
        post_frontend_thr.start()

    # [可选] 启动 MinIO 文件上传线程
    # put_minio = Thread(target=put_fenxi, daemon=True)
    # put_minio.start()

    # 计算需要的帧数常量
    channel_crt_count = settings.VIDEO_CRT * settings.VIDEO_CRT_SECONDS
    _channel_detect_count = settings.VIDEO_DETECT * settings.VIDEO_CRT_SECONDS

    # 获取视频数据源（前端摄像头管理，多路摄像头）
    # 检测模式："parallel"（并行检测所有摄像头）或 "polling"（轮询逐个检测）
    detection_mode = getattr(settings, "DETECTION_MODE", "parallel")
    dataset, cjs = get_camera_stream(detection_mode=detection_mode)
    if not cjs:
        logger.error("no channels to detect (摄像头未就绪)")
        return

    logger.info(f"\n{'=' * 60}")
    logger.info(f"检测配置:")
    logger.info(f"  检测模式: {detection_mode}")
    logger.info(f"  摄像头数量: {len(cjs)}")
    logger.info(f"  摄像头列表: {cjs}")
    logger.info(f"{'=' * 60}")

    # 启动前置逻辑线程 (Logic0)
    # Logic0 现在支持动态摄像头名称，直接传递原始摄像头名称
    if getattr(settings, 'ENABLE_LOGIC0', True):
        logic = Thread(target=Logic0, args=(cjs, dataset), daemon=True)
        logic.start()
        logger.info("Logic0 线程已启动")
    else:
        logger.info("Logic0 线程已禁用（可设置 settings.ENABLE_LOGIC0 = True 启用）")

    # 加载 AI 模型
    device = select_device("0")
    model1, model2, names1, _names2, pose_net, _colors = get_models(device)
    print(names1)

    def trigger_violation_alarm(channel_name: str, category: str):
        if not (settings.AUDIO_ENABLED and audio_controller):
            return

        alarm_key = f"{channel_name}:{category}"
        now_ts = time.time()
        last_alarm_ts = VIOLATION_ALARM_WINDOW.get(alarm_key, 0)
        if now_ts - last_alarm_ts < ALARM_WINDOW_SECONDS:
            logger.info(f"[报警限流] {channel_name} {category} 在 {ALARM_WINDOW_SECONDS} 秒内已播报，跳过本次播报")
            return

        vio_name = settings.VIOLATION_ALARM_MAP.get(category)
        if not vio_name:
            return

        audio_file = settings.BASE_DIR / "sounds" / f"{vio_name}.mp3"
        if not audio_file.exists():
            logger.warning(f"音频文件不存在，无法播放违规警报: {audio_file}")
            return

        try:
            Thread(
                target=audio_controller.play_violation_alarm,
                args=(str(audio_file), settings.AUDIO_VOLUME),
                daemon=True
            ).start()
            VIOLATION_ALARM_WINDOW[alarm_key] = now_ts
            logger.info(f"🚨 违规警报触发: {channel_name} -> {vio_name}")
        except Exception as e:
            logger.error(f"触发违规警报失败: {e}")

    def iterate_stream(ds):
        for item in ds:
            yield item

    # ================= 3. 主检测循环 =================
    try:
        # 打印从 API 获取的配置信息
        logger.info("\n===============================================")
        logger.info("从 API 获取的配置信息：")
        logger.info("===============================================")

        # 打印 SAPI 基础 URL
        logger.info(f"SAPI 基础 URL: {settings.SAPI_BASE_URL}")

        # 打印统一二次阈值配置（不按场景）
        logger.info(f"统一二次阈值配置: {settings.ERCI_THRESHOLD}")

        # 违章类型配置统一由 api/sapi_risk_fetch.py 在上传时按需查询
        logger.info("违章类型映射来源: api/sapi_risk_fetch.py (按需查询)")

        logger.info("===============================================")

        for channels_name, frames in iterate_stream(dataset):
            end_time = datetime.datetime.now() - datetime.timedelta(seconds=0)
            start_time = end_time - datetime.timedelta(seconds=30)
            _frames_count = getattr(dataset, "FRAMES_COUNT", 0)
            s_time = time_synchronized()

            images = []

            for k, cj in enumerate(channels_name):
                frame = frames[k]
                f2 = []
                fpss = []
                length_need = settings.VIO_COUNT.get(cj, settings.DEFAULT_VIO_COUNT)
                avail = len(frame)

                if avail == 0:
                    continue

                if length_need <= 1:
                    idxs = [0]
                else:
                    idxs = []
                    for ii in range(length_need):
                        pos = ii * (avail - 1) / (length_need - 1) if length_need > 1 else 0
                        idx = int(round(pos))
                        if idx < 0:
                            idx = 0
                        if idx >= avail:
                            idx = avail - 1
                        if not idxs or idx != idxs[-1]:
                            idxs.append(idx)

                while len(idxs) < length_need:
                    idxs.append(avail - 1)

                for i in idxs[:length_need]:
                    fpss.append(i)
                    f2.append(frame[i])

                images.extend(f2)

            s0_time = time_synchronized()
            erci_count = 0
            pose_count = 0

            targets = seek_targets(model1, device, images)
            s1_time = time_synchronized()

            all_detected_classes = set()
            for t in targets:
                for det in t:
                    if len(det) > 5:
                        all_detected_classes.add(det[5])

            if all_detected_classes:
                logger.info(f"[一次检测结果] 当前批次检测到的目标类别: {list(all_detected_classes)}")

            for im_targets, image in zip(targets, images):
                person_tragets = [i for i in im_targets if i[5] in settings.DEEPSORT]
                person_ids = get_rycsid(image, person_tragets)
                for i, p_id in enumerate(person_ids):
                    person_tragets[i].append(p_id)

            s2_time = time_synchronized()

            for k, v in enumerate(targets):
                for i, det in enumerate(v):
                    if det[5] in settings.POSE and det[4] > settings.ERCI_ZITAI_THRESHOLD:
                        pose_count += 1
                        images_pose = images[k][det[1]:det[3], det[0]:det[2]].copy()
                        poses = run_pose(net=pose_net, height_size=256, cpu=False, track=1, smooth=1,
                                         img=images_pose)
                        det.append(poses or [])

            s3_time = time_synchronized()

            suspect_person_ids = set()
            logged_erci_channels = set()
            played_alarms = set()

            try:
                step_interval = int(settings.ERCI_STEP * settings.VIDEO_DETECT)
            except Exception:
                step_interval = 6
            if step_interval < 1:
                step_interval = 1

            for k, v in enumerate(targets[2:]):
                channel_name = channels_name[int(k / channel_crt_count)]
                threshold = settings.ERCI_THRESHOLD
                erci_enabled = settings.CAMERA_ERCI_ENABLED.get(channel_name, settings.DEFAULT_ERCI_ENABLED)

                if channel_name not in logged_erci_channels and threshold:
                    logged_erci_channels.add(channel_name)

                if k % step_interval == 0:
                    suspect_person_ids.clear()

                    for i, det in enumerate(v):
                        # 初始化变量，避免 UnboundLocalError
                        no_gongyi_traget = False
                        cls_name = det[5]
                        conf = det[4]

                        # 不需要二次监测的违规，直接上传
                        if cls_name not in settings.ERCI and cls_name in settings.VIOLATION_ALARM_MAP:
                            alarm_thr = settings.DIRECT_ALARM_THRESHOLDS.get(cls_name, 0.5)
                            if conf >= alarm_thr:
                                alarm_key = (channel_name, cls_name)
                                if alarm_key not in played_alarms:
                                    logger.info(f"[一次检测-直接报警] {channel_name} {cls_name} {conf:.2f}")
                                    trigger_violation_alarm(channel_name, cls_name)
                                    # 直接保存证据并上传
                                    save_violation_evidence(
                                        cj=channel_name,
                                        category=cls_name,
                                        image=images[k + 2],
                                        video_frames=frames[int((k + 2) / channel_crt_count)],
                                        frame_count=getattr(dataset, "count", 0),
                                    )
                                    played_alarms.add(alarm_key)

                        if erci_enabled and det[5] in settings.ERCI and det[4] > settings.ERCI_PERSON_THRESHOLD:
                            erci_count += 1
                            targets2 = seek_targets(model2, device, [images[k + 2][det[1]:det[3], det[0]:det[2]], ])
                            det.append(targets2[0])

                            no_gongyi_traget = True
                            # 标记是否进行了有效的工衣检测（二次检测执行即设为True）
                            gongyi_detected = True

                            # 遍历二次检测结果
                            for det2 in targets2[0]:
                                vio_type = det2[5]
                                vio_conf = det2[4]

                                if vio_type in threshold:
                                    chk_thr = threshold[vio_type]
                                else:
                                    chk_thr = settings.DIRECT_ALARM_THRESHOLDS.get(vio_type, 0.5)

                                if det[5] in settings.DEEPSORT and len(
                                        det) > 6 and vio_type in settings.VIOLATION_ALARM_MAP:
                                    if vio_conf > chk_thr:
                                        logger.info(
                                            f"[全扫描-确信] {channel_name} ID:{det[6]} 违规:{vio_type} conf:{vio_conf:.2f}")
                                        suspect_person_ids.add(det[6])
                                        alarm_key = (channel_name, vio_type)
                                        if alarm_key not in played_alarms:
                                            # 每次检测到违规都触发报警
                                            trigger_violation_alarm(channel_name, vio_type)
                                            # 保存证据和上传受时间窗口限制
                                            save_violation_evidence(
                                                cj=channel_name,
                                                category=vio_type,
                                                image=images[k + 2],
                                                video_frames=frames[int((k + 2) / channel_crt_count)],
                                                frame_count=getattr(dataset, "count", 0),
                                            )
                                            played_alarms.add(alarm_key)

                                # 检查是否检测到工衣/雨衣/皮裙（放在内层循环内）
                                if no_gongyi_traget and vio_type in ["gongyi_h", "gongyi_l", "gongyi_c", "yuyi", "piqun"] \
                                        and vio_conf > 0.5 and len(det) > 6 and det[6] not in settings.NO_ERCI_PERSONIDS["gongyi"]:
                                    no_gongyi_traget = False
                                    gongyi_detected = True

                        # 仅人员目标且存在追踪ID时，才进入未穿工衣补充判定
                        # 只有进行了有效的二次检测且确实未检测到工衣，才判定为未穿工衣
                        if no_gongyi_traget and gongyi_detected and det[5] in settings.DEEPSORT and len(det) > 6:
                            suspect_person_ids.add(det[6])
                            settings.NO_ERCI_PERSONIDS["gongyi"].add(det[6])
                            alarm_key = (channel_name, "noclothes")
                            if alarm_key not in played_alarms:
                                # 每次检测到违规都触发报警
                                trigger_violation_alarm(channel_name, "noclothes")
                                # 保存证据和上传受时间窗口限制
                                save_violation_evidence(
                                    cj=channel_name,
                                    category="noclothes",
                                    image=images[k + 2],
                                    video_frames=frames[int((k + 2) / channel_crt_count)],
                                    frame_count=getattr(dataset, "count", 0),
                                )
                                played_alarms.add(alarm_key)

                else:
                    for i, det in enumerate(v):
                        # 添加 det[5] in settings.ERCI 检查，确保只有二次检测类别才进行二次检测
                        if erci_enabled and det[5] in settings.ERCI and det[5] in settings.DEEPSORT and len(det) > 6 and det[
                            6] in suspect_person_ids and det[
                            4] > settings.ERCI_PERSON_THRESHOLD:
                            erci_count += 1
                            targets2 = seek_targets(model2, device, [images[k + 2][det[1]:det[3], det[0]:det[2]], ])
                            det.append(targets2[0])

                            no_gongyi_traget = True
                            gongyi_detected = False

                            for det2 in targets2[0]:
                                vio_type = det2[5]
                                vio_conf = det2[4]

                                if vio_type in threshold:
                                    chk_thr = threshold[vio_type]
                                else:
                                    chk_thr = settings.DIRECT_ALARM_THRESHOLDS.get(vio_type, 0.5)

                                if det[5] in settings.DEEPSORT and vio_type in settings.VIOLATION_ALARM_MAP:
                                    if vio_conf > chk_thr:
                                        alarm_key = (channel_name, vio_type)
                                        if alarm_key not in played_alarms:
                                            # 每次检测到违规都触发报警
                                            trigger_violation_alarm(channel_name, vio_type)
                                            # 保存证据和上传受时间窗口限制
                                            save_violation_evidence(
                                                cj=channel_name,
                                                category=vio_type,
                                                image=images[k + 2],
                                                video_frames=frames[int((k + 2) / channel_crt_count)],
                                                frame_count=getattr(dataset, "count", 0),
                                            )
                                            played_alarms.add(alarm_key)

                                # 检查是否检测到工衣/雨衣/皮裙
                                if no_gongyi_traget and vio_type in ["gongyi_h", "gongyi_l", "gongyi_c", "yuyi", "piqun"] \
                                        and vio_conf > 0.5 and len(det) > 6 and det[6] not in settings.NO_ERCI_PERSONIDS["gongyi"]:
                                    no_gongyi_traget = False
                                    gongyi_detected = True

                            # 未穿工衣补充判定
                            if no_gongyi_traget and gongyi_detected and det[5] in settings.DEEPSORT and len(det) > 6:
                                alarm_key = (channel_name, "noclothes")
                                if alarm_key not in played_alarms:
                                    trigger_violation_alarm(channel_name, "noclothes")
                                    save_violation_evidence(
                                        cj=channel_name,
                                        category="noclothes",
                                        image=images[k + 2],
                                        video_frames=frames[int((k + 2) / channel_crt_count)],
                                        frame_count=getattr(dataset, "count", 0),
                                    )
                                    played_alarms.add(alarm_key)

            s4_time = time_synchronized()

            cj_frame_targets = {}
            f = 0
            for k, cj in enumerate(channels_name):
                length = settings.VIO_COUNT.get(cj, settings.DEFAULT_VIO_COUNT)
                cj_frame_targets[cj] = {
                    "frame": images[f:(f + length)],
                    "targets": targets[f:(f + length)],
                    "video": frames[k],
                    "hks_count": getattr(dataset, "count", 0),
                    "start_time": start_time,
                    "end_time": end_time
                }
                f += length

            _s5_time = time.time()

            fx = Thread(target=save_fenxi, args=(channels_name, cj_frame_targets, getattr(dataset, "count", 0)))
            fx.start()

            settings.VIDOE_QUEUE.append(cj_frame_targets)
            _s6_time = time.time()

            time.sleep(settings.VIDEO_CRT_SECONDS)

            _fps1 = len(images) / (s1_time - s0_time) if (s1_time - s0_time) != 0 else 0
            _fps2 = erci_count / (s4_time - s3_time) if (s4_time - s3_time) != 0 else 0
            _pose_f = pose_count / (s3_time - s2_time) if (s3_time - s2_time) != 0 else 0

            disks = []
            s7_time = time.time()
            for i in psutil.disk_partitions():
                try:
                    disk_info = psutil.disk_usage(i.mountpoint)
                    if "/dev/sd" in i.device or "C:" in i.device or "D:" in i.device:
                        disks.append(f"{i.device}:{disk_info.used / disk_info.total:.2f}")
                except Exception:
                    pass
            s8_time = time.time()

            logger.info(
                f"{getattr(dataset, 'count', 0)} / memory used {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024:.2f}G {psutil.virtual_memory().percent}% /"
                f"磁盘占用 {disks} ,用时:{s8_time - s7_time:.2f}s /"
                f"GPU温度：{settings.MONITOR_DATA.get('gpu_temperature')} / "
                f" 一次{len(images)}张:{s1_time - s0_time:.2f}s /"
                f"人员追踪:{s2_time - s1_time:.2f}s / "
                f"姿态估计{pose_count}张：{s3_time - s2_time:.2f}s ("
                f"二次{erci_count}张：{s4_time - s3_time:.2f}s /"
                f"检测总共使用时间:{s8_time - s_time:.2f}s"
            )
            logger.info(f"[视频检测] 本轮疑似二次检测次数: {erci_count}")

    except Exception as e:
        logger.info(traceback.format_exc())
        logger.error(f"main err:{e}")
    finally:
        # 释放摄像头资源
        if dataset:
            try:
                dataset.release()
            except Exception as e:
                logger.error(f"释放摄像头资源失败: {e}")
    logger.info("main program exit!!!")


if __name__ == '__main__':
    main()