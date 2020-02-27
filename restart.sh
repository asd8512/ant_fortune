kill -HUP `supervisorctl -c /root/etc/supervisord.conf pid gunicorn`
supervisorctl -c /root/etc/supervisord.conf restart celery