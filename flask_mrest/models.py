import base64
import json
from sqlalchemy.exc import IntegrityError, InvalidRequestError
import sqlalchemy as sa
from alchemyjsonschema import BaseModelWalker, SingleModelWalker, SchemaFactory
from errorhandlers import page_not_found
from flask import current_app, make_response, request
from jsonschema import validate, ValidationError
from sqlalchemy.ext.declarative import declarative_base
from mrest_client.auth import decode_auth_data
from flask_mrest.auth import mrest_authenticate, mrest_404
from hashlib import sha256

SABase = declarative_base()


def dictify_item(item, model):
    columns = [c.name for c in model.__table__.columns]
    columnitems = dict([(c, getattr(item, c)) for c in columns])
    return columnitems


def query_to_json(query, model):
    if isinstance(query, SABase):
        return json.dumps(dictify_item(query, model))
    else:
        items = []
        for item in query:
            items.append(dictify_item(item, model))
        return json.dumps(items)


class BaseModel(object):
    """
    An MREST model with no route handlers. A good base to use for private models which will require custom routes.
    See child SuperModel class for route handler examples.
    """
    def __init__(self, name, model_name, plain_methods=None, id_methods=None, sa_model=None, excludes=None,
                 walker=None):
        """
        :param str name: The display name of the model (typically capitalized)
        :param str model_name: The model name (lower case, for routing, tables, etc)
        :param list plain_methods: Methods to use for plain route
        :param list id_methods: Methods to use for id route
        :param SABase sa_model: The SQLAlchemy model
        :param list excludes: a list of excludes to pass to the walker
        :param BaseModelWalker walker:
        """
        if not excludes:
            excludes = []
        if not id_methods:
            id_methods = []
        if not plain_methods:
            plain_methods = []
        self.name = name
        self.model_name = model_name
        self.plain_methods = plain_methods
        self.id_methods = id_methods
        self._private_routes = None
        self._public_routes = None
        if sa_model is not None:
            self._sa_model = sa_model
        else:
            self._sa_model = None
        self.excludes = excludes
        if isinstance(walker, BaseModelWalker):
            self.walker = walker
        else:
            self.walker = SingleModelWalker
        self._json_schema = None

    @property
    def sa_model(self):
        """
        Provide the SQLAlchemy model as a separate object, so that it isn't cluttered with unnecessary attributes.

        :return: The SQLAlchemy model to use for this super model
        """
        if self._sa_model is None:
            self._sa_model = SABase  # This default is meaningless. Create your own class to inherit from Base.
        return self._sa_model

    @property
    def json_schema(self):
        """
        Provide the SQLAlchemy model as a separate object, so that it isn't cluttered with unnecessary attributes.

        :return: The json schema for this model
        """
        if self._json_schema is None:
            factory = SchemaFactory(self.walker)
            self._json_schema = factory.__call__(self.sa_model, excludes=self.excludes)
            # TODO change to custom route with valid json-reference as per
            # http://tools.ietf.org/html/draft-zyp-json-schema-04#section-6.2
            self._json_schema['$schema'] = "http://json-schema.org/draft-04/schema#"
            self._json_schema['private_routes'] = self.private_routes
            self._json_schema['public_routes'] = self.public_routes
            print self._json_schema

        return self._json_schema

    @property
    def private_routes(self):
        if self._private_routes is None:
            self._private_routes = {"/": [], "/:id": []}
            for method in ('get', 'post', 'put', 'delete'):
                name = getattr(self, method).__name__
                if name == 'authenticated_handler':
                    self._private_routes['/'].append(method.upper())
            for method in ('get', 'post', 'put', 'delete'):
                name = getattr(self, method + "_one").__name__
                if name == 'authenticated_handler':
                    self._private_routes['/:id'].append(method.upper())
        return self._private_routes

    @property
    def public_routes(self):
        if self._public_routes is None:
            self._public_routes = {"/": [], "/:id": []}
            for method in ('get', 'post', 'put', 'delete'):
                name = getattr(self, method).__name__
                if name != 'authenticated_handler' and name != 'pnf_handler':
                    self._public_routes['/'].append(method.upper())
            for method in ('get', 'post', 'put', 'delete'):
                name = getattr(self, method + "_one").__name__
                if name != 'authenticated_handler' and name != 'pnf_handler':
                    self._public_routes['/:id'].append(method.upper())
        return self._public_routes

    def route_plain(self):
        """
        Handler for /<model> routes.
        """
        if request.method == 'GET':
            return self.get()
        elif request.method == 'POST':
            return self.post()
        elif request.method == 'PUT':
            return self.put()
        elif request.method == 'DELETE':
            return self.delete()
        else:
            return "this server does not support %s requests" % request.method

    def route_id(self, itemid):
        """
        Handler for /<model>/<itemid> routes.
        """
        if request.method == 'GET':
            return self.get_one(itemid)
        elif request.method == 'POST':
            return self.post_one(itemid)
        elif request.method == 'PUT':
            return self.put_one(itemid)
        elif request.method == 'DELETE':
            return self.delete_one(itemid)
        else:
            return "this server does not support %s requests" % request.method

    @mrest_404
    def get(self):
        """
        Handler for GET /<model>
        """
        pass

    @mrest_404
    def post(self):
        """
        Handler for POST /<model>
        """
        pass

    @mrest_404
    def put(self):
        """
        Handler for PUT /<model>
        """
        pass

    @mrest_404
    def delete(self):
        """
        Handler for DELETE /<model>
        """
        pass

    @mrest_404
    def get_one(self, itemid):
        """
        Handler for GET /<model>/<id>
        """
        pass

    @mrest_404
    def post_one(self, itemid):
        """
        Handler for POST /<model>/<id>
        """
        pass

    @mrest_404
    def put_one(self, itemid):
        """
        Handler for PUT /<model>/<id>
        """
        pass

    @mrest_404
    def delete_one(self, itemid):
        """
        Handler for DELETE /<model>/<id>
        """
        pass


class SuperModel(BaseModel):
    """
    An MREST model with all route handlers defined with default behavior.
    A good base to use for completely public models which need the generic REST functionality.
    """
    def __init__(self, name, model_name, **kwargs):
        if 'plain_methods' in kwargs:
            del kwargs['plain_methods']
        if 'id_methods' in kwargs:
            del kwargs['id_methods']
        super(SuperModel, self).__init__(name, model_name, plain_methods=['GET', 'POST'],
                                         id_methods=['GET', 'PUT', 'DELETE'], **kwargs)

    def get(self):
        items = current_app.sa['session'].query(self.sa_model).all()
        current_app.sa['session'].commit()
        return make_response(query_to_json(items, self.sa_model), 200)

    @mrest_authenticate
    def post(self):
        args = decode_auth_data(request.data)
        try:
            validate(args, current_app.json_schemas[self.model_name])
        except ValidationError:
            return page_not_found()
        item = self.sa_model(**args)
        current_app.sa['session'].add(item)
        current_app.sa['session'].commit()
        return make_response(query_to_json(item, self.sa_model), 200)

    @mrest_authenticate
    def get_one(self, itemid):
        try:
            item = current_app.sa['session'].query(self.sa_model).filter(self.sa_model.id == itemid).one()
        except Exception as e:
            return page_not_found()
        return make_response(query_to_json(item, self.sa_model), 200)

    @mrest_authenticate
    def put_one(self, itemid):
        try:
            item = current_app.sa['session'].query(self.sa_model).filter(self.sa_model.id == itemid).one()
        except Exception as e:
            return page_not_found()
        args = decode_auth_data(request.get_data())
        # delete unsafe values
        if 'id' in args:
            del args['id']
        # override existing values
        dictitem = dictify_item(item, self.sa_model)
        for arg in args:
            if arg in dictitem:
                dictitem[arg] = args[arg]
        try:
            validate(dictitem, current_app.json_schemas[self.model_name])
        except ValidationError as ve:
            current_app.logger.info("ValidationError received %s" % ve)
            return page_not_found()
        cid = dictitem['id']
        del dictitem['id']
        try:
            current_app.sa['session'].query(self.sa_model).filter(self.sa_model.id == cid).update(dictitem)
        except Exception as e:
            return page_not_found()
        current_app.sa['session'].commit()
        return make_response(query_to_json(item, self.sa_model), 201)

    @mrest_authenticate
    def delete_one(self, itemid):
        try:
            item = current_app.sa['session'].query(self.sa_model).filter(self.sa_model.id == itemid).one()
        except Exception as e:
            return page_not_found()
        current_app.sa['session'].delete(item)
        current_app.sa['session'].commit()
        return make_response("", 204)


class UserSA(SABase):
    """model for an api user or item user"""
    __tablename__ = "user"

    id = sa.Column(sa.String(120), primary_key=True, nullable=False, doc="primary key")
    pubpem = sa.Column(sa.String(255), nullable=False)

    def __repr__(self):
        return "<User(id='%s')>" % self.id


class UserModel(BaseModel):
    """
    The ECC auth user object. Override with your user model, if you wish.
    """
    def __init__(self):
        super(UserModel, self).__init__('User', 'user', plain_methods=['POST'],
                                        id_methods=['GET'], sa_model=UserSA)

    def post(self):
        args = decode_auth_data(request.data)
        try:
            validate(args, current_app.json_schemas[self.model_name])
        except ValidationError:
            return page_not_found()
        pubpem = base64.b64decode(args['pubpem'])
        pubhash = sha256(pubpem).hexdigest()
        item = self.sa_model(id=pubhash, pubpem=pubpem)
        current_app.sa['session'].add(item)
        try:
            current_app.sa['session'].commit()
        except IntegrityError as ie:
            current_app.logger.info("user already existed %r" % pubhash)
            current_app.sa['session'].rollback()
            return make_response(query_to_json(item, self.sa_model), 200)
        except InvalidRequestError as ire:
            current_app.logger.info("user already existed %r" % pubhash)
            current_app.sa['session'].rollback()
            return make_response(query_to_json(item, self.sa_model), 200)
        current_app.logger.info("created user %r" % item)
        return make_response(query_to_json(item, self.sa_model), 200)

    @mrest_authenticate
    def get_one(self, itemid):
        """
        Handler for /user/<itemid> routes.
        """
        try:
            item = current_app.sa['session'].query(self.sa_model).filter(self.sa_model.id == itemid).one()
        except Exception as e:
            return page_not_found()
        return make_response(query_to_json(item, self.sa_model), 200)
