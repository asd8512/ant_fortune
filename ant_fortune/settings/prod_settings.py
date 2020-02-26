import os

from ant_fortune.settings.local_settings import *

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
