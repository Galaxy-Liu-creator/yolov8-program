from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from marshmallow import fields

from applications.models import Station


class StationSchema(SQLAlchemyAutoSchema):
    parent_dept_name = fields.String(attribute="parent.dept_name")
    grand_parent_dept_name = fields.String(attribute="parent_parent.dept_name", dump_only=True, allow_none=True)

    class Meta:
        model = Station
        include_fk = True
