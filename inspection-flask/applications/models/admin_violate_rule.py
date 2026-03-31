import datetime
from applications.extensions import db


class ViolateRule(db.Model):
    __tablename__ = 'admin_violate_rule'
    id = db.Column(db.Integer, primary_key=True, comment='ID', autoincrement=True)
    name = db.Column(db.String(255), comment='名称')
    photo = db.Column(db.String(100), comment='图片名')
    details = db.Column(db.String(255), comment='详情')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    is_delete = db.Column(db.Integer, default=0, comment='0-正常 1-删除')
