from flask_login import current_user
from sqlalchemy import or_

from applications.models import Station, DeptRelations


def judge_station_generate_auth(code):
    roles = ['common', 'dept', 'sub', 'city']
    if code in roles:
        return roles[:roles.index(code)]
    return []


def detect_auth():
    if current_user.role[0].code == "admin":
        return True
    return False


def stations_auth():
    station_ids = []
    filters = [(DeptRelations.type == 0) | (DeptRelations.type == 1)]

    if current_user.role[0].code == "sub":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
    if current_user.role[0].code == "dept" or current_user.role[0].code == "common":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
        filters.append(DeptRelations.dept_id == current_user.dept_id)

    _ids = DeptRelations.query.filter(*filters).with_entities(
        DeptRelations.station_id).all()
    station_ids = [id_ for (id_,) in _ids]
    return station_ids


def dept_auth():
    dept_ids = []
    filters = [DeptRelations.type == 1]

    if current_user.role[0].code == "sub":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
    if current_user.role[0].code == "dept" or current_user.role[0].code == "common":
        filters.append(DeptRelations.sub_id == current_user.sub_id)
        filters.append(DeptRelations.dept_id == current_user.dept_id)

    _ids = DeptRelations.query.filter(*filters).with_entities(
        DeptRelations.dept_id).all()
    dept_ids = [id_ for (id_,) in _ids]
    return dept_ids


def sub_auth():
    sub_ids = []
    filters = [Station.type == 3]

    if current_user.role[0].code == "sub" or current_user.role[0].code == "dept" or current_user.role[
        0].code == "common":
        filters.append(Station.id == current_user.sub_id)
        filters.append(Station.is_delete == 0)
    if current_user.role[0].code == "city":
        filters.append(Station.is_delete == 0)
    _ids = Station.query.filter(*filters).with_entities(
        Station.id).all()
    sub_ids = [id_ for (id_,) in _ids]
    return sub_ids
