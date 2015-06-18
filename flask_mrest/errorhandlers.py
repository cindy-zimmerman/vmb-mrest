import traceback
from flask import make_response, jsonify, current_app, g
import time


def unauthorized_page(e=None):
    return make_response(jsonify(error='unauthorized'), 401)


def forbidden_page(e=None):
    return make_response(jsonify(error='forbidden'), 403)


def page_not_found(e=None):
    return make_response(jsonify(error='not found'), 404)


def ratelimit_exceeded(e=None):
    return make_response(jsonify(error='rate limit exceeded'), 429)


def server_error(e=None):
    diff = time.time() - g.start
    current_app.logger.error("! 500 ERROR %ss (%s) @ %s" % (diff, e, g.start))
    return make_response(jsonify(error='unable to process request'), 500)


def generic_code_error(e=None):
    current_app.logger.error('!! %s' % traceback.format_exc())
    return make_response(jsonify(error='unable to process request'), 500)
