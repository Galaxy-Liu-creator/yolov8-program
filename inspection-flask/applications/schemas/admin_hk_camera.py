from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from marshmallow import fields

from applications.models import HKCamera
from applications.schemas.admin_police_station import StationSchema


class HkCameraOutSchema(SQLAlchemyAutoSchema):
    station = fields.Nested(StationSchema)

    class Meta:
        model = HKCamera
        include_relationships = True
        include_fk = True
