from flask import Flask

from .init_sqlalchemy import db, ma, init_databases


def init_plugs(app: Flask) -> None:
    init_databases(app)
