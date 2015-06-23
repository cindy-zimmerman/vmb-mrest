pkill unicorn
gunicorn flask_mrest.mrest:gunicorn_app -b 0.0.0.0:8090