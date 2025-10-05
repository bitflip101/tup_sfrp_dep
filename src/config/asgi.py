import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()


# --- IMPORTANT: If you *later* add Django Channels ---
# You would modify this file to include ProtocolTypeRouter, URLRouter, etc.
# For example, if you had an 'abode' app with a 'routing.py' for WebSockets:
#
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.security.websocket import AllowedHostsOriginValidator
# import abode.routing # Assuming your app 'abode' has a routing.py
#
# application = ProtocolTypeRouter(
#     {
#         "http": get_asgi_application(),
#         "websocket": AllowedHostsOriginValidator(
#             AuthMiddlewareStack(URLRouter(abode.routing.websocket_urlpatterns))
#         ),
#     }
# )