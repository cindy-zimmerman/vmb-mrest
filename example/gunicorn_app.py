# An example of how an MREST app could be run using gunicorn
# to run:
#
# gunicorn gunicorn_app:gunicorn_app -b 0.0.0.0:8002

from example import Application, example_cfg


_gunicorn_app = None


def gunicorn_app(environ, start_response):
    global _gunicorn_app
    if _gunicorn_app is None:
        _gunicorn_app = Application(example_cfg)
    return _gunicorn_app(environ, start_response)
