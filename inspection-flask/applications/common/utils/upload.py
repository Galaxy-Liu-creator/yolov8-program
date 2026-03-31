"""最小空壳 — hk_camera.py 有 import 但当前未调用。
证据图保存走 save_violate_photo() 内部的 cv2.imwrite，不走 Flask-Upload。
"""


def upload_one_with_name(photo):
    raise NotImplementedError("upload 扩展尚未引入，当前不支持此功能")


def upload_one(photo, mime=None):
    raise NotImplementedError("upload 扩展尚未引入，当前不支持此功能")
