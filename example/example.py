import json
from flask import request, current_app, make_response
from jsonschema import validate, ValidationError
import sqlalchemy as sa
import sqlalchemy.orm as orm

from flask_mrest.mrest import Application
from flask_mrest.models import SABase, SuperModel, UserModel, query_to_json
from flask_mrest.errorhandlers import page_not_found, unauthorized_page
import example_cfg


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


example_cfg.MODELS = {'coin': CoinModel(),
                      'user': UserModel()}


if __name__ == '__main__':
    # run app directly for debugging
    Application(example_cfg).run(host='0.0.0.0', port=8002)