import os
from datetime import timedelta

import settings


class BaseConfig:
    SUPERADMIN = 'admin'
    AUTH_ENABLED = settings.AUTH_ENABLED
    DB_STRICT_STARTUP = settings.DB_STRICT_STARTUP
    ENABLE_BACKGROUND_SCHEDULER = settings.ENABLE_BACKGROUND_SCHEDULER

    SYSTEM_NAME = '加油站工服检测'

    UPLOADED_PHOTOS_DEST = 'vio_data'
    UPLOADED_FILES_ALLOW = ['gif', 'jpg', 'png']
    UPLOADS_AUTOSERVE = True

    UPLOADED_VIOLATE_PHOTOS_DEST_ABS = settings.VIO_IMAGE_PATH

    JSON_AS_ASCII = False
    SECRET_KEY = "inspection-flask"

    HOSTNAME = os.getenv('DB_HOST', 'localhost')
    PORT = os.getenv('DB_PORT', '5432')
    USERNAME = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', '123456')
    DATABASE = os.getenv('DB_NAME', 'ducha')
    DB_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
    )
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 100,
        'max_overflow': 20
    }

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
