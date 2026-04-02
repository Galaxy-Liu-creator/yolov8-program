from flask import current_app, session
from flask_login import current_user


def _load_template_permissions():
    permissions = session.get("ducha_permissions")
    if permissions is not None:
        return permissions

    role_items = getattr(current_user, "role", []) or []
    user_power = []
    for role in role_items:
        if getattr(role, "enable", 1) == 0:
            continue
        for permission in getattr(role, "power", []) or []:
            if getattr(permission, "enable", 1) == 0:
                continue
            code = getattr(permission, "code", None)
            if code:
                user_power.append(code)

    session["ducha_permissions"] = user_power
    return user_power


def init_template_directives(app):
    @app.template_global()
    def authorize(power):
        if not current_app.config.get("AUTH_ENABLED", False):
            return True

        if getattr(current_user, "username", None) == current_app.config.get("SUPERADMIN"):
            return True

        permissions = _load_template_permissions()
        return power in permissions
