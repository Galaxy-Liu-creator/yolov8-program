from applications.view.system.hk_camera import bp as hk_camera_bp


def init_bps(app):
    app.register_blueprint(hk_camera_bp)
