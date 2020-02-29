from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ant_fortune.settings')

from django.conf import settings  # noqa

app = Celery('ant_fortune')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# from celery import shared_task

# @shared_task
# def add(x, y):
#     return x + y
