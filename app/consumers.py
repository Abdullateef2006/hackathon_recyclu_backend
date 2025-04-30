import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings
from channels.db import database_sync_to_async

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get token from query params
        logger.info("WebSocket connect request received")

        query_string = self.scope['query_string'].decode()
        token = None
        if 'token=' in query_string:
            token = query_string.split('token=')[-1]
        
        if not token:
            logger.warning("WebSocket connection rejected: no token")
            await self.close()
            return

        try:
            # Validate and decode the JWT token
            UntypedToken(token)
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")

            self.user = await database_sync_to_async(User.objects.get)(id=user_id)

            # Assign group name
            self.group_name = f"user_{self.user.id}"

            # Add connection to group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            logger.info(f"WebSocket connected: {self.user.username} (Group: {self.group_name})")
            await self.accept()

        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            logger.warning(f"WebSocket connection rejected: invalid token ({e})")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: {self.user.username} (Group: {self.group_name})")
        else:
            logger.info("WebSocket disconnected before joining a group.")

    async def send_notification(self, event):
        logger.info(f"Sending WebSocket notification to {self.user.username}: {event}")

        message = event['message']
        created_at = event['created_at']

        await self.send(text_data=json.dumps({
            'message': message,
            'created_at': created_at
        }))
