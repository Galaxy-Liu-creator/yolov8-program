from flask_login import current_user
from sqlalchemy import or_

from applications.models import Station, DeptRelations


def _auth_enabled():
    try:
        from flask import current_app
        return current_app.config.get("AUTH_ENABLED", False)
    except Exception:
        return False


def _role_code():
    roles = getattr(current_user, "role", None) or []
    if not roles:
        return None
    return getattr(roles[0], "code", None)


def judge_station_generate_auth(code):
    roles = ['common', 'dept', 'sub', 'city']
    if code in roles:
        return roles[:roles.index(code)]
    return []


def detect_auth():
    if not _auth_enabled():
        return True
    if _role_code() == "admin":
        return True
    return False


def stations_auth():
    if not _auth_enabled():
        return None
    station_ids = []
    filters = [(DeptRelations.type == 0) | (DeptRelations.type == 1)]

    role_code = _role_code()
    if role_code == "sub":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
    if role_code == "dept" or role_code == "common":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
        filters.append(DeptRelations.dept_id == current_user.dept_id)

    _ids = DeptRelations.query.filter(*filters).with_entities(
        DeptRelations.station_id).all()
    station_ids = [id_ for (id_,) in _ids]
    return station_ids


def dept_auth():
    if not _auth_enabled():
        return None
    dept_ids = []
    filters = [DeptRelations.type == 1]

    role_code = _role_code()
    if role_code == "sub":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
    if role_code == "dept" or role_code == "common":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
        filters.append(DeptRelations.dept_id == current_user.dept_id)

    _ids = DeptRelations.query.filter(*filters).with_entities(
        DeptRelations.dept_id).all()
    dept_ids = [id_ for (id_,) in _ids]
    return dept_ids


def sub_auth():
    if not _auth_enabled():
        return None
    sub_ids = []
    filters = [Station.type == 3]

    role_code = _role_code()
    if role_code == "sub" or role_code == "dept" or role_code == "common":
        filters.append(Station.id == current_user.sub_id)
        filters.append(Station.is_delete == 0)
    if role_code == "city":
        filters.append(Station.is_delete == 0)
    _ids = Station.query.filter(*filters).with_entities(
        Station.id).all()
    sub_ids = [id_ for (id_,) in _ids]
    return sub_ids
