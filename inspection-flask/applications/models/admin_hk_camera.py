import datetime
from applications.extensions import db


class HKCamera(db.Model):
    __tablename__ = 'admin_hk_camera'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    name = db.Column(db.String(50), comment='摄像头名')
    ip = db.Column(db.String(50), comment='摄像头ip', default='')
    port = db.Column(db.String(30), comment='摄像头port', default='8000')
    username = db.Column(db.String(100), comment='用户名', default='')
    password = db.Column(db.String(150), comment='密码', default='')
    enable = db.Column(db.Integer, default=0, comment='1-开启 0-关闭')
    is_delete = db.Column(db.Integer, default=0, comment='0-正常 1-删除')
    station_id = db.Column(db.Integer, comment='具体地点的id')
    type = db.Column(db.Integer, comment='0-正常地点 1-值班室 2-枪库')
    dept_id = db.Column(db.Integer, db.ForeignKey("admin_police_station.id"), comment='部门ID')
    channel = db.Column(db.Integer, comment='channel')
    channel_type = db.Column(db.Integer, default=0, comment='channel')
    sub_id = db.Column(db.Integer, comment='subID')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    station = db.relationship('Station', backref=db.backref('hk_camera_station'))
