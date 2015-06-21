import hashlib
import logging
import ecdsa
import sqlalchemy as sa
import sqlalchemy.orm as orm
import time

from bson import json_util
from flask import Flask, request, make_response, jsonify, g, session
from flask.ext.login import LoginManager, current_user
import SupportUser
from errorhandlers import unauthorized_page, forbidden_page, page_not_found, ratelimit_exceeded, \
    server_error, generic_code_error
from logger import setupLogHandlers
# from models import BaseModel
# from mrest_client.auth import add_mrest_headers, construct_auth_data
# from flask.ext.kvsession import KVSessionExtension

from db import loadUserByID, loadUserByUsername
from vmb_db.conf import getModule
configVMB = getModule('config')

from actions import authentication, homepage, client, invoice


class Application(Flask):
    """
    A wrapper for the main Flask application. Adds MREST routes, functions
    and configuration.
    """

    def __init__(self, cfg):
        """
        :return: an MREST app instance
        """
        super(Application, self).__init__(__name__)
        self.config.from_object(cfg)

        self.before_request(self.__augment_request)
        self.after_request(self.__augment_response)

        self.session_interface.serializer = json_util

        # SQLAlchemy initialization use sqlite memory by default
        self.sa = {'engine': sa.create_engine(self.config.get('SA_ENGINE_URL', 'sqlite:///:memory:'))}

        # Setup logger.
        self.logger.setLevel(logging.INFO)
        log_dir = self.config.get('LOG_DIR', './')
        log_name = self.config.get('LOG_NAME', 'MREST-app.log')
        use_gelf = self.config.get('USE_GELF', False)

        for h in setupLogHandlers(log_name, log_dir=log_dir, use_gelf=use_gelf):
            self.logger.addHandler(h)

        # Authentication setup
        self.mrest = {'name': self.config.get('PUBLIC_NAME', "MREST Application"),
                      'default_auth': self.config.get('DEFAULT_AUTH', True),
                      'ecc_curve': self.config.get('ECC_CURVE', 'SECP256k1'),
                      'privkey': '', 'pubkey': '', 'pubpem': '', 'pubhash': ''}
        priv_key = self.config.get('ECC_PRIV_KEY', None)
        if priv_key is not None and 'BEGIN EC PRIVATE KEY' in priv_key:
            self.mrest['privkey'] = ecdsa.SigningKey.from_pem(priv_key)
            self.mrest['pubkey'] = self.mrest['privkey'].get_verifying_key()
            self.mrest['pubpem'] = self.mrest['pubkey'].to_pem()
            self.mrest['pubhash'] = hashlib.sha256(self.mrest['pubpem']).hexdigest()

        # The mrest models to add
        self.mrest['models'] = self.config.get('MODELS', {})
        self.mrest['json_schemas'] = {}

        self.__init_db()
        self.__routes()
        self.logger.info("mrest app created")

        self.session_cookie_name = 'vmb-session'
        self.secret_key = configVMB.SECRET_KEY
        self.config['SESSION_TYPE'] = 'filesystem'

        self.config['UPLOAD_FOLDER'] = configVMB.UPLOAD_FOLDER

        self.__initLoginManager()

        self.debug = True
        self.run(host='0.0.0.0')
        session.init_app(self)

    def __augment_request(self):
        g.start = time.time()
        request.app = self

    # def __augment_response(self, response):
    #     if self.config.get('SIGN_RESPONSES', False) and 300 > response.status_code >= 200:
    #         adata = construct_auth_data(response.data)
    #         add_mrest_headers(self.mrest['pubhash'], 'RESPONSE', data=adata['data'], privkey=self.mrest['privkey'],
    #                           headers=response.headers, auth=True)
    #     return response

    def __augment_response(self, response):
        # Log response.
        diff = time.time() - g.start
        self.logger.info("> %s %ss (%s) @ %s" % (response.status, diff,
                         response.content_type, g.start))
        return response


    def __initLoginManager(self):
        login_manager = LoginManager()
        login_manager.anonymous_user = SupportUser.Anonymous
        login_manager.login_view = '/login'
        login_manager.login_message = ''
        login_manager.user_loader(loadUserByID)
        login_manager.init_app(self)

    def __routes(self):
        self.errorhandler(401)(unauthorized_page)
        self.errorhandler(403)(forbidden_page)
        self.errorhandler(404)(page_not_found)
        self.errorhandler(405)(forbidden_page)
        self.errorhandler(429)(ratelimit_exceeded)
        self.errorhandler(500)(server_error)
        self.errorhandler(Exception)(generic_code_error)

        self.url_map.strict_slashes = False


        self.route('/login', methods=['GET', 'POST'])(authentication.login)

        self.route('/', methods=['GET', 'POST'])(homepage.go)


        self.route('/clients/view/<cid>', methods=['GET', 'POST'])(client.viewClient)
        self.route('/clients/edit/<cid>', methods=['GET', 'POST'])(client.editClient)
        # self.route('/clients/edit/<cid>', methods=['POST'])(client.editClient)

        self.route('/invoices/view', methods=['GET', 'POST'])(invoice.viewInvoice)
        self.route('/invoices/', methods=['POST'])(invoice.packageArrived)


        self.__model_routes()



    def __model_routes(self, name=None):
        for mod in self.mrest['models']:
            if name is None or mod == name:
                # add flask routes for models
                if hasattr(self.mrest['models'][mod], 'route_plain') and \
                        len(self.mrest['models'][mod].plain_methods) > 0:
                    self.add_url_rule('/%s' % mod, '%s_plain' % mod, self.mrest['models'][mod].route_plain,
                                      methods=self.mrest['models'][mod].plain_methods)
                if hasattr(self.mrest['models'][mod], 'route_id') and len(self.mrest['models'][mod].id_methods) > 0:
                    self.add_url_rule('/%s/<itemid>' % mod, '%s_id' % mod, self.mrest['models'][mod].route_id,
                                      methods=self.mrest['models'][mod].id_methods)

    # def add_model(self, model):
    #     if not isinstance(model, BaseModel):
    #         raise TypeError("expected model to be an instance of BaseModel, got %s" % (type(model)))
    #     self.mrest['models'][model.model_name] = model
    #     self.__model_routes(model.model_name)

    def __init_db(self):
        # TODO close/clean up existing session
        for mod in self.mrest['models']:
            # TODO do we always want to call create_all?
            self.mrest['models'][mod].sa_model.metadata.create_all(self.sa['engine'])
        self.sa['session'] = orm.sessionmaker(bind=self.sa['engine'])()

    @property
    def json_schemas(self):
        if len(self.mrest['json_schemas']) != len(self.mrest['models']):
            for mod in self.mrest['models']:
                self.mrest['json_schemas'][mod] = self.mrest['models'][mod].json_schema
        return self.mrest['json_schemas']

    def get_info_route(self):
        """
        Get info about the server itself. What authentication requirements does it have? Which ECC curve should
        the client use? What schemas are available?
        """
        info = {'name': self.mrest['name'],
                'user_model': 'user',
                'curve': self.mrest['ecc_curve'], 'pub_pem': self.mrest['pubpem'],
                'schemas': self.json_schemas}
        return make_response(jsonify(info), 200)


if __name__ == '__main__':
    # app.run()
    appy = Application(Flask)