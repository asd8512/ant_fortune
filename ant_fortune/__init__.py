import pymysql
pymysql.install_as_MySQLdb()

from .celery import app
