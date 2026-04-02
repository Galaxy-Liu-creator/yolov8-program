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
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_app.config.get("AUTH_ENABLED", False):
                return func(*args, **kwargs)

            @login_required
            def protected():
                if getattr(current_user, "username", None) == current_app.config.get("SUPERADMIN"):
                    return func(*args, **kwargs)
                permissions = session.get('ducha_permissions', None)
                if permissions is None:
                    role = getattr(current_user, "role", []) or []
                    user_power = []
                    for item in role:
                        if getattr(item, "enable", 1) == 0:
                            continue
                        for permission in getattr(item, "power", []) or []:
                            if getattr(permission, "enable", 1) == 0:
                                continue
                            code = getattr(permission, "code", None)
                            if code:
                                user_power.append(code)
                    session['ducha_permissions'] = user_power
                if power not in session.get('ducha_permissions', []):
                    if request.method == 'GET':
                        abort(403)
                    return jsonify(success=False, msg="权限不足!")
                return func(*args, **kwargs)

            return protected()

        return wrapper

    return decorator
