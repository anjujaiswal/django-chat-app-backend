import socketio
# from utils import config
import json
from django.shortcuts import get_object_or_404
from users.models import User, Room, GroupMembers, Messages, MessageHistory,UsersMapping
# from chatting.models import Chat, ChatMessage
from chatting.serializers import RoomSerializer, MessageSerializer, MessageHistorySerializer
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from jose import jwt
from chatapp.settings import SECRET_KEY
from .utils import get_room_id

mgr = socketio.AsyncRedisManager('redis://127.0.0.1:6379')
sio = socketio.AsyncServer(
    async_mode="asgi", client_manager=mgr, cors_allowed_origins="*"
)
handle_socket_users = {}


async def join_room(sid, chat_user_id):
    try:
        # Assume you have a function get_room_ids in your code
        room_ids = await get_room_id(chat_user_id)
        print("join_room ~ room_ids:", room_ids)
        
        for element in room_ids:
            room_id_value = await database_sync_to_async(lambda: element.room_id)()
            await sio.enter_room(sid, room_id_value)
            print(f"User with id {sid} joined room {element.room_id}")
    except Exception as error:
        print("error->>>>>>>>>>>>>join_room", error)
        

@sio.event
async def connect(sid, environ):
    try:
        query_string = environ.get('QUERY_STRING', '')
        chat_user_id = query_string.split('&')[0].split('=')[1]
        print(f"User connected: {sid}, chat_user_id: {chat_user_id}")

        if not chat_user_id:
            raise ConnectionRefusedError('Invalid chat user id')
        
        await join_room(sid, chat_user_id)

    except Exception as error:
        print("error->>>>>>>>>>>>>connect", error)
    # handle_socket_users[sid] = "85bab8ff-8d06-4614-ad71-00c9c1c8330f"
@sio.event
async def check_rooms(sid):
    rooms = sio.rooms(sid)
    print(f"User with id {sid} is in rooms: {rooms}")
    
# @sio.event
# def connect(sid, environ):
#     token = environ.get('token')
#     if token:
#         try:
#             # Validate and decode the JWT token
#             decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
#             # Authentication successful - allow connection
#             print(f"user connected: {sid}")
#         except jwt.ExpiredSignatureError:
#             raise ConnectionRefusedError('Token expired')
#         except jwt.JWTError:
#             raise ConnectionRefusedError('Invalid token')
#     else:
#         raise ConnectionRefusedError('Authentication token not provided')


# logic for handling a user joining a room asynchronously
async def handle_user_join_room(user_id, room_id):
    # logic for handling the user joining the room...

    # Trigger the event to broadcast a message to the room
    await sio.emit('send_message_to_room', {'room_id': room_id, 'message': f'User {user_id} has joined the room.'})

# @sio.event
# async def join_room(sid, data):
#     print(get_room_id(),"=========room id-----")
#     user_id = data.get('user_id')  # Get user ID from data
#     room_id = data.get('room_id')

#     # Wrap database queries using sync_to_async
#     room_obj = await sync_to_async(Room.objects.filter(room_id=room_id).first)()
    
#     group_members_qs = await sync_to_async(GroupMembers.objects.filter)(room_id=room_id)
#     group_members_list = await sync_to_async(list)(group_members_qs)

#     await sio.enter_room(sid, room_id)

#     for members in group_members_list:
#         chat_user_id = await sync_to_async(lambda: str(members.chat_user_id.chat_user_id))()
#         handle_socket_users[sid] = chat_user_id  # Store user ID in handle_socket_users dictionary
#         # Trigger the event to broadcast a message to the room
#         await handle_user_join_room(chat_user_id, room_id)



@sio.event
async def send_message(sid, data):
    print("=========0",data)
    room_id = data.get('room_id')
    msg_serializer = MessageSerializer(data=data)
    if await is_valid_async(msg_serializer):
        # Save the validated data to the database asynchronously
        saved_data = await save_message_async(msg_serializer.validated_data)
        
        # Serialize the saved data to obtain the complete representation
        serialized_data = MessageSerializer(saved_data).data
        
        #serializer the save data into the Message history
        # # print("save data ",saved_data.message_id)
        # saved_msg_history = await saved_message_history_async(saved_data)
        
        # # Serialize the saved data to obtain the complete representation
        # # msg_history_serializer = MessageHistorySerializer(saved_msg_history).data
        # # Emit an acknowledgment event to the sender
        # await sio.emit('acknowledge_message', {'room_id': room_id, 'message_id': serialized_data['message_id'], 'status': 'delivered'}, room=sid)
        # event = await sio.receive()
        # print(f'received event: "{event[0]}" with arguments {event[1:]}')
        print("===room id",room_id)
        await sio.emit('recieve_message', serialized_data,room=room_id)
    else:
        # await sio.emit('acknowledge_message', {'room_id': room_id, 'message_id': "", 'status': 'Not Delivered'}, room=sid)
        print(msg_serializer.errors)  # Handle validation errors

@sync_to_async
def save_message_async(validated_data):
    return Messages.objects.create(**validated_data)

@sync_to_async
def is_valid_async(serializer):
    return serializer.is_valid()

# Server-side event to send a message to a specific room
@sio.event
async def send_message_to_room(data):
    room_id = data.get('room_id')
    message = data.get('message')
    await sio.emit('new_message', message, room=room_id)
    
#save history message 
@sync_to_async
def saved_message_history_async(data):
    message = Messages.objects.get(message_id=data.message_id)
    return MessageHistory.objects.create(message_id=message,delivered_to_chat_user_id=data.sender_chat_user_id)
    
#acknowledgemnt status function
@sio.event
async def acknowledge_message(sid, data):
    room_id = data.get('room_id')
    message_id = data.get('message_id')
    status = data.get('status')
    print(sid)
    # You can handle the acknowledgment status as needed
    if status == 'delivered':
        print(f"Message {message_id} in room {room_id} has been delivered.")
    else:
        print(f"Failed to deliver message {message_id} in room {room_id}.")
        
@sio.event
async def mark_message_seen(sid, data):
    room_id = data.get('room_id')
    message_id = data.get('message_id')
    read_by_chat_user = data.get('user_id')
    read_by_user = UsersMapping.objects.get(chat_user_id=read_by_chat_user)
    # Implement logic to mark the message as seen in your database
    # For example, you can update a field in your Messages model
    await sync_to_async(MessageHistory.objects.filter(message_id=message_id).update)(read_by_chat_user_id=read_by_user)

    # Broadcast the seen status to other clients in the room
    await sio.emit('message_seen_status', {'room_id': room_id, 'message_id': message_id, 'seen': True}, room=room_id)

# Event for disconnecting from the socket
@sio.on("disconnect")
async def disconnect(sid):
    print("SocketIO disconnect")
    


# @sio.event
# async def receive_message(sid, data):
#     print('Received message111111:', data)
#     room_id = data.get('room_id')
#     await sio.emit('receive_message', data, room=room_id, skip_sid=sid)

# @sio.event
# async def receive_message(sid, data):
#     print('Received message:', data)
#     print("receive_message sid: ", sid)
#     room_id = data.get('room_id')
#     await sio.emit('receive_message', data, room=room_id, skip_sid=sid)

# @sio.event
# def send_message(sid, data):
#     print(data)
#     # Save chat message (Replace with your logic)
#     # msg_details = save_chat_msg(data)
#     # print("->>>>>>>>>1", msg_details)
#     room_id = data.get('room_id')
#     sio.emit('receive_message', data, room=room_id, skip_sid=sid)




# Example implementation for fetching chat messages based on chat_short_id
# @sio.event
# def get_chat_messages(sid, chat_short_id):
#     try:
#         messages = ChatMessage.objects.filter(chat__short_id=chat_short_id)
#         serialized_messages = [
#             {
#                 'sender': str(message.sender),
#                 'text': message.text,
#                 # Add other fields as needed
#             }
#             for message in messages
#         ]
#         sio.emit('chat_messages', serialized_messages, room=sid)
#     except Exception as e:
#         print(f"Error fetching messages: {e}")
#         sio.emit('chat_messages', [], room=sid)

