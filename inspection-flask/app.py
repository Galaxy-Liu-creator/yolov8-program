import logging

from applications import create_app, HKRecorderThreadManager
import settings

app = create_app()

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

if __name__ == '__main__':
    yolo_family = getattr(settings, "YOLO_FAMILY", "yolov8")
    app.logger.info(
        "加油站工服检测系统启动 (model=%s)，监听 0.0.0.0:8080", yolo_family,
    )
    app.run(threaded=True, host='0.0.0.0', port=8080)