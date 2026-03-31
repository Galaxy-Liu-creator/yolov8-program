import datetime

from marshmallow import Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from applications.extensions import db, ma


class LogicalDeleteMixin(object):
    """
    class Test(db.Model,LogicalDeleteMixin):
    __tablename__ = 'admin_test'
    id = db.Column(db.Integer, primary_key=True, comment='角色ID')

    Test.query.filter_by(id=1).soft_delete()
    Test.query.logic_all()
    """
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='创建时间')
    delete_at = db.Column(db.DateTime, comment='删除时间')


def auto_model_jsonify(data, model: db.Model):
    def get_model():
        return model

    class AutoSchema(SQLAlchemyAutoSchema):
        class Meta(Schema):
            model = get_model()
            include_fk = True
            include_relationships = True
            load_instance = True

    common_schema = AutoSchema(many=True)
    output = common_schema.dump(data)
    return output


def model_to_dicts(schema: ma.Schema, data):
    common_schema = schema(many=True)
    output = common_schema.dump(data)
    return output


def get_one_by_id(model: db.Model, id):
    return model.query.filter_by(id=id).first()


def delete_one_by_id(model: db.Model, id):
    r = model.query.filter_by(id=id).delete()
    db.session.commit()
    return r


def logic_delete_one_by_id(model: db.Model, id):
    r = model.query.filter_by(id=id).update({"is_delete": 1})
    db.session.commit()
    return r


def enable_status(model: db.Model, id):
    enable = 1
    role = model.query.filter_by(id=id).update({"enable": enable})
    if role:
        db.session.commit()
        return True
    return False


def disable_status(model: db.Model, id):
    enable = 0
    role = model.query.filter_by(id=id).update({"enable": enable})
    if role:
        db.session.commit()
        return True
    return False
