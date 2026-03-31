import traceback

from flask import Flask


def handle_global_exceptions(app: Flask):
    @app.errorhandler(Exception)
    def handle_exceptions(e):
        trace = traceback.format_exc()
        app.logger.error('Unhandled Exception: %s\n%s', e, trace)
        return 'An internal server error occurred', 500
