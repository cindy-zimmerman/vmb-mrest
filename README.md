# Flask mrest
An API server framework for a heavily structured (Model) REST API. Using [Flask](http://flask.pocoo.org/).

Part of a 4 component architecture, the REST and MVC components here are respectively mirrored in [API clients](https://bitbucket.org/deginner/flask-mrest/wiki/Clients) and web application boilerplates.

For more information about MREST, please visit its [wiki](https://bitbucket.org/deginner/flask-mrest/wiki/Home).


## Installation
From source:

`python setup.py install`


## Example
The example directory contains a full example server, including configuration file with comments.

To run the example, first you must install flask-mrest. Then run example/example.py.

`python example.py`


To test visit this page in a browser:

> http://0.0.0.0:8002/

You should see server info, including the schemas for example models 'coin' and 'user':

```
{
  "curve": "SECP256k1",
  "name": "Coin collection",
  "pub_pem": "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE31O8+NaE+QS6ehXbXkPdN62rW1/vV1dB\n2/UhgV4/c47FhaIiINOuKka1rb93dmsIJhAjdh54PICjdvSF2EKdVQ==\n-----END PUBLIC KEY-----\n",
  "user_model": "user",
  "schemas": {
    "coin": {
      "$schema": "http://json-schema.org/draft-04/schema#",
      "description": "model for coin",
      "private_routes": {
        "/": [],
        "/:id": [
          "GET",
          "PUT",
          "DELETE"
        ]
      },
      "properties": {
        "metal": {
          "maxLength": 255,
          "type": "string"
        },
        "mint": {
          "maxLength": 255,
          "type": "string"
        }
      },
      "public_routes": {
        "/": [
          "GET",
          "POST"
        ],
        "/:id": []
      },
      "required": [
        "metal",
        "mint"
      ],
      "title": "CoinSA",
      "type": "object"
    },
    "user": {
      "$schema": "http://json-schema.org/draft-04/schema#",
      "description": "model for an api user or item user",
      "private_routes": {
        "/": [],
        "/:id": [
          "GET"
        ]
      },
      "properties": {
        "id": {
          "description": "primary key",
          "maxLength": 120,
          "type": "string"
        },
        "pubpem": {
          "maxLength": 255,
          "type": "string"
        }
      },
      "public_routes": {
        "/": [
          "POST"
        ],
        "/:id": []
      },
      "required": [
        "id",
        "pubpem"
      ],
      "title": "UserSA",
      "type": "object"
    }
  }
}
```

This is success! It is showing that the server is running and will accept requests for the example models. Note that the schemas each contain two custom properties: public_routes and private_routes. These indicate the authentication rules for the model's routes. The "/" and "/:id" subsets indicate whether the restriction applies to the /:model/ route or to the /:model/:id route.


### Client Registration
The example server has a user model named 'user' and uses SECP256k1 keys. This means that a client can register by POSTing to the '/user' with his public key. Official MREST clients come with a .register() method to assist with this process. Registration and authentication are required to access private routes. For more information about authentication, visit [Authentication](https://bitbucket.org/deginner/flask-mrest/wiki/Authentication)


## Server Development Quickstart
Flask-mrest servers are driven by models. There are 3 distict types of models in an mrest ecosystem: SQLAlchemy, json schema, and BaseModel.


### SQLAlchemy Model
At the heart of the BaseModel is an SQLAlchemy model. This is the model used to create your database tables/collections, as well as the basis for the json schemas used for validation and client configuration. These are no different from standard SQLAlchemy models, so it is best to just read their [docs](http://docs.sqlalchemy.org/en/latest/orm/tutorial.html).


```
class CoinSA(SABase):
    """model for coin"""
    __tablename__ = "coin"

    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    metal = sa.Column(sa.String(255), nullable=False)
    mint = sa.Column(sa.String(255), nullable=False)
    user_id = sa.Column(sa.String(120), sa.ForeignKey('user.id'), nullable=False)
    user = orm.relationship("UserSA")

    def __repr__(self):
        return "<Coin(id=%s, metal='%s', mint='%s', user='%s')>" % (self.id, self.metal, self.mint, self.user_id)
```


### JSON Schema Model
JSON Schema models are automatically generated using [alchemyjsonschema](https://github.com/podhmo/alchemyjsonschema). These are the same as are available via your server's / route.

### BaseModel
The BaseModel is the class that ties the different models together. It provides access to the SQLAlchemy model, generates json schemas, and also defines flask routes for handling requests to the model.

In addition to the BaseModel, Flask-mrest includes a SuperModel class with pre-defined route handlers. These are extremely open, however, so do not use SuperModel as a base for private models.

Whether you are using BaseModel or SuperModel, the way to customize behavior is by overwriting the parent functions. Specifically, you will be interested in implementing the route handler methods: get, put, post, delete, get_one, put_one, post_one, delete_one. These correspond to the various HTTP methods and whether the route includes the unique id field. To require authentication for a route, simply wrap its method in @mrest_authenticate.

*It is important to note that Flask does not allow multiple handlers for a single route, so the various handlers (i.e. get, put, post, delete, get_one, put_one, post_one, delete_one) are overloaded into the route_plain and route_id handler methods. You probably don't need to muck with these.*

The example server uses an open SuperModel base and overrides the post function to provide custom behavior for POST requests to the '/coin' route.


```
class CoinModel(SuperModel):
    def __init__(self, **kwargs):
        if 'plain_methods' in kwargs:
            del kwargs['plain_methods']
        if 'id_methods' in kwargs:
            del kwargs['id_methods']
        super(SuperModel, self).__init__('Coin', 'coin', plain_methods=['GET', 'POST'],
                                         id_methods=['GET', 'PUT', 'DELETE'], sa_model=CoinSA,
                                         excludes=['id', 'user_id'])

    def post(self):
        """
        Override SuperModel handler for POST.
        """
        args = json.loads(request.data)
        try:
            validate(args, current_app.json_schemas[self.model_name])
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return page_not_found()
        if not 'x-mrest-pubhash' in request.headers:
            return unauthorized_page()
        item = self.sa_model(metal=args['metal'], mint=args['mint'], user_id=request.headers['x-mrest-pubhash'])
        current_app.sa['session'].add(item)
        current_app.sa['session'].commit()
        return make_response(query_to_json(item, self.sa_model), 200)
```


## Authentication
MREST authentication uses Elyptical Curve Cryptography (ECC) to sign requests and responses. The [authentication documentation](https://bitbucket.org/deginner/flask-mrest/wiki/Authentication) details the signing and authentication instructions, which will be required for all private routes.


## Kong
This server works well when paired with Kong. For more information, read our [wiki](https://bitbucket.org/deginner/flask-mrest/wiki/Kong) page about it.


## Clients
MREST clients are thinly strapped together [Unirest](http://unirest.io/) and [json schema](http://json-schema.org/). This makes it extremely easy to develop compatible clients. Official ones are listed below, but we encourage anyone looking at a language not yet supported to consider [implementing one](https://bitbucket.org/deginner/flask-mrest/wiki/Clients).

+ [Node.js](https://bitbucket.org/deginner/mrest-client-nodejs)
+ [Python](https://bitbucket.org/deginner/mrest-client-python)
