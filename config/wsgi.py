"""WSGI 部署入口，供 Gunicorn 等同步应用服务器加载。"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
