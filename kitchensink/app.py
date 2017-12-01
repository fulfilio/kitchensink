from flask import Flask
from .extensions import babel, toolbar, login_manager, sentry
from .settings import Config
from flask_sslify import SSLify
from .utils import client_url


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # register extensions
    babel.init_app(app)
    toolbar.init_app(app)
    login_manager.init_app(app)
    sentry.init_app(app)

    # Initialize the celery app
    # celery.init_app(app)
    if not app.debug:
        SSLify(app)

    app.jinja_env.filters['client_url'] = client_url

    # register blueprints
    from kitchensink.shipment import shipment, move
    app.register_blueprint(shipment)
    app.register_blueprint(move)
    from kitchensink.user import blueprint, public, error_500
    app.register_error_handler(500, error_500)
    app.register_blueprint(blueprint)
    app.register_blueprint(public)
    from kitchensink.product import product
    app.register_blueprint(product)

    return app
