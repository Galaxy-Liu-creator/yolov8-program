from functools import wraps
from flask import abort, request, jsonify, session, current_app
from flask_login import login_required, current_user


def authorize(power: str, log: bool = False):
    """用户权限判断，用于判断目前会话用户是否拥有访问权限

    :param power: 权限标识
    :type power: str
    :param log: 是否记录日志, defaults to False
    :type log: bool, optional
    """

    def decorator(func):
        @login_required
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.username == current_app.config.get("SUPERADMIN"):
                return func(*args, **kwargs)
            permissions = session.get('ducha_permissions', None)
            if permissions is None:
                role = current_user.role
                user_power = []
                for i in role:
                    if i.enable == 0:
                        continue
                    for p in i.power:
                        if p.enable == 0:
                            continue
                        user_power.append(p.code)
                session['ducha_permissions'] = user_power
            if not power in session.get('ducha_permissions'):
                if request.method == 'GET':
                    abort(403)
                else:
                    return jsonify(success=False, msg="权限不足!")
            return func(*args, **kwargs)

        return wrapper

    return decorator
