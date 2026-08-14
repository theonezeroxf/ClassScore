"""ASGI 部署入口，为异步服务器预留标准加载方式。"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.asgi import get_asgi_application

application = get_asgi_application()
