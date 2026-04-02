from flask import Flask

from .init_sqlalchemy import db, ma, init_databases
from .init_template_directives import init_template_directives


def init_plugs(app: Flask) -> None:
    init_databases(app)
    init_template_directives(app)
