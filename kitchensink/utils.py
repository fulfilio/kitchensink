import flask

from fulfil_client.oauth import Session
from .app import Config
from urllib import urlencode
from fulfil_client.client import dumps


def get_oauth_session():
    return Session(Config.FULFIL_SUBDOMAIN)


def client_url(model, id=None, domain=None):
    """
    A filter for template engine to generate URLs that open
    on fulfil client of the instance::
        <a href="{{ 'product.product'|client_url }}">Product List</a>
        <a href="{{ 'product.product'|client_url(product.id) }}">{{ product.name }}</a>
    A more sophisticated example with filter
        <a href="{{ 'product.product'|client_url(domain=[('salable', '=', True)]) }}">
            Salable Products
        </a>
    """
    subdomain = Config.FULFIL_SUBDOMAIN
    url = 'https://{subdomain}.fulfil.io/client/#/model/{model}'.format(
        subdomain=subdomain,
        model=model
    )
    if id:
        url += '/%d' % id
    elif domain:
        url += '?' + urlencode({'domain': dumps(domain)})
    return url
