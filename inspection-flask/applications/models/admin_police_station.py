import datetime

from sqlalchemy.orm import relationship

from applications.extensions import db


class Station(db.Model):
    __tablename__ = 'admin_police_station'
    id = db.Column(db.Integer, primary_key=True, comment="站点ID")
    parent_id = db.Column(db.Integer, db.ForeignKey('admin_police_station.id'), comment="父级编号")
    dept_name = db.Column(db.String(50), comment="站点名称")
    leader = db.Column(db.String(50), comment="负责人", default='')
    phone = db.Column(db.String(20), comment="联系方式", default='')
    is_delete = db.Column(db.Integer, comment='(1删除,0正常)', default=0)
    type = db.Column(db.Integer, comment='0-加油站 1-办公区 2-片区 3-总部', default=0)
    remark = db.Column(db.Text, comment="备注", default='')
    address = db.Column(db.String(255), comment="详细地址", default='')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    parent = relationship('Station', remote_side=[id], backref='children')
