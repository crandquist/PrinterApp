import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'not-ready-to-add-a-key'