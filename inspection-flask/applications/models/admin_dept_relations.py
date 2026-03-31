from applications.extensions import db


class DeptRelations(db.Model):
    __tablename__ = 'admin_dept_relations'
    id = db.Column(db.Integer, primary_key=True, comment='ID')
    type = db.Column(db.Integer, comment='类型-0（区-部门-站点）类型1（区-部门）')
    station_id = db.Column(db.Integer, comment='站点的id')
    dept_id = db.Column(db.Integer, comment='单位的id')
    sub_id = db.Column(db.Integer, comment='上级id')
