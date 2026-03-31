import os
from datetime import timedelta

import settings


class BaseConfig:
    SYSTEM_NAME = '加油站工服检测'

    UPLOADED_PHOTOS_DEST = 'vio_data'
    UPLOADED_FILES_ALLOW = ['gif', 'jpg', 'png']
    UPLOADS_AUTOSERVE = True

    UPLOADED_VIOLATE_PHOTOS_DEST_ABS = settings.VIO_IMAGE_PATH

    JSON_AS_ASCII = False
    SECRET_KEY = "inspection-flask"

    HOSTNAME = 'localhost'
    PORT = '5432'
    USERNAME = 'postgres'
    PASSWORD = '123456'
    DATABASE = 'ducha'
    DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 100,
        'max_overflow': 20
    }

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
