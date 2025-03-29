import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-secure'
    TEMPLATES_AUTO_RELOAD = True