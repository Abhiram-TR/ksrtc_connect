import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from communication.models import Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Set unique room name for each user
        self.room_name = f"user_{self.user.id}"
        self.room_group_name = f"chat_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json.get('message')
            receiver_id = text_data_json.get('receiver_id')
            
            if message and receiver_id:
                # Save message to database
                message_obj = await self.save_message(receiver_id, message)
                
                # Send message to receiver's room group
                receiver_room_group_name = f"chat_user_{receiver_id}"
                await self.channel_layer.group_send(
                    receiver_room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name() or self.user.username,
                        'message_id': message_obj.id,
                        'timestamp': message_obj.timestamp.isoformat(),
                    }
                )
                
                # Send confirmation back to sender
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_sent',
                        'message': message,
                        'receiver_id': receiver_id,
                        'message_id': message_obj.id,
                        'timestamp': message_obj.timestamp.isoformat(),
                    }
                )
        
        elif message_type == 'mark_read':
            message_id = text_data_json.get('message_id')
            if message_id:
                await self.mark_message_read(message_id)

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    # Confirm message sent
    async def message_sent(self, event):
        # Send confirmation to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message_sent',
            'message': event['message'],
            'receiver_id': event['receiver_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, receiver_id, content):
        try:
            receiver = User.objects.get(id=receiver_id)
            message = Message.objects.create(
                sender=self.user,
                receiver=receiver,
                content=content,
                is_read=False,
                is_announcement=False
            )
            return message
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id, receiver=self.user)
            message.is_read = True
            message.save(update_fields=['is_read'])
            return True
        except Message.DoesNotExist:
            return False