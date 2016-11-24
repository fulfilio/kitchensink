# -*- coding: utf-8 -*-
"""Application configuration."""
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('SECRET', 'secret-key')  # TODO: Change me

    FULFIL_SUBDOMAIN = os.environ.get('FULFIL_SUBDOMAIN')
    FULFIL_API_KEY = os.environ.get('FULFIL_API_KEY')

    DEBUG = os.environ.get('ENV', 'prod') != 'prod'
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    #CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    #CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
