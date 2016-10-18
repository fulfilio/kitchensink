# -*- coding: utf-8 -*-
"""Application configuration."""
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('SHOP_SECRET', 'secret-key')  # TODO: Change me

    FULFIL_SUBDOMAIN = os.environ.get('FULFIL_SUBDOMAIN')
    FULFIL_API_KEY = os.environ.get('FULFIL_API_KEY')
