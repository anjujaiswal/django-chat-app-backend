from users.models import User, Room, GroupMembers, Messages, MessageHistory,UsersMapping
# from chatting.models import Chat, ChatMessage
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from chatting.serializers import RoomSerializer, MessageSerializer, MessageHistorySerializer

@sync_to_async
def get_user_id(chat_user_id):
    return UsersMapping.objects.get(chat_user_id=chat_user_id)

@sync_to_async
def get_room_ids(chat_user):
    return list(GroupMembers.objects.filter(chat_user_id=chat_user))

async def get_room_id(chat_user_id):
    try:
        chat_user = await get_user_id(chat_user_id)
        room_ids = await get_room_ids(chat_user)
        return room_ids

    except UsersMapping.DoesNotExist:
        print(f"User with chat_user_id {chat_user_id} does not exist.")
        return []

    except Exception as error:
        print("Error in get_room_id:", error)
        return []
