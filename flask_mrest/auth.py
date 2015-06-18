import hashlib
import json
from flask import current_app, request
from errorhandlers import unauthorized_page, page_not_found
from mrest_client.auth import _load_ecpub_pem, create_sign_str


def mrest_404(cb):
    """
    Always return 404. Different from an empty handler, this is one which explicitly does not exist. Importantly,
    the json schema will not include the wrapped route in its public_routes property.

    :param cb: an unused callback
    :return: 404 error response
    """
    def pnf_handler(*args, **kwargs):
        """
        Do not change the name of this function! (pnf_handler) It is used to mark empty routes.
        """
        return page_not_found()
    return pnf_handler


def mrest_authenticate(cb):
    def authenticated_handler(*args, **kwargs):
        """
        Do not change the name of this function! (authenticated_handler) It is used to check whether or not a route requires
        authentication.
        """
        raw_data = request.get_data()
        if len(raw_data) > 0:
            data = json.loads(raw_data)
            if not 'data' in data:
                current_app.logger.exception("incorrectly formatted authenticated request")
                return unauthorized_page()
            datastr = data['data']
        else:
            datastr = ""
        if not 'x-mrest-sign' in request.headers or \
                not 'x-mrest-pubhash' in request.headers or \
                not 'x-mrest-time' in request.headers:
            current_app.logger.exception("incorrectly formatted authenticated request")
            return unauthorized_page()
        try:
            sign = request.headers['x-mrest-sign'].decode('hex')
        except Exception as e:
            current_app.logger.exception(e)
            return unauthorized_page()
        try:
            user = current_app.sa['session'].query(current_app.mrest['models']['user'].sa_model)\
                .filter(current_app.mrest['models']['user'].sa_model.id == request.headers['x-mrest-pubhash']).one()
        except Exception as e:
            current_app.logger.exception(e)
            return unauthorized_page()
        client_pub_key, err = _load_ecpub_pem(user.pubpem)
        if err:
            current_app.logger.exception(err)
            return unauthorized_page()
        try:
            client_pub_key.verify(sign, create_sign_str(datastr, request.method, request.headers['x-mrest-time']),
                                  hashlib.sha256)
        except Exception, e:
            # Typically this will be ecdsa.keys.BadSignatureError, but broken
            # programs might produce invalid values for r or s which causes
            # verify(...) to return False.
            current_app.logger.exception(e)
            return unauthorized_page()
        return cb(*args, **kwargs)
    return authenticated_handler
