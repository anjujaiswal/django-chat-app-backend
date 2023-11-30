from rest_framework import serializers
from users.models import Room, Messages, MessageHistory


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

    def to_representation(self, obj):       
        representation = super().to_representation(obj)
        return {
            "room_id": str(representation['room_id']),
            "room_type": representation['room_type'],
            "group_name": representation['group_name'],
            "group_picture": representation['group_picture'],
            "group_quotes": representation['group_quotes'],
            "is_archived": representation['is_archived'],
            "created_at": representation['created_at'],
            "updated_at": representation['updated_at'],
            "deleted_at": representation['deleted_at'],
        }

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        fields = '__all__'
    
    def to_representation(self, obj):       
        representation = super().to_representation(obj)
        print(representation['thumbnail_file_path'])
        # Convert empty strings to None for file paths
        if representation['file_path'] == "":
            representation['file_path'] = None

        if representation['thumbnail_file_path'] == "":
            print("comming")
            representation['thumbnail_file_path'] = None
        return {
            "message_id": str(representation.get('message_id', None)),
            "room_id": str(representation['room_id']),
            "sender_chat_user_id": str(representation['sender_chat_user_id']),
            "message_type": representation['message_type'],
            "message_content": representation['message_content'],
            "file_path": representation['file_path'],
            "thumbnail_file_path": representation['thumbnail_file_path'],
            "deleted_for": representation['deleted_for'],
            "created_at": representation['created_at'],
            "updated_at": representation['updated_at'],
            "deleted_at": representation['deleted_at']
        }


class MessageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageHistory
        fields = '__all__'

    def to_representation(self, obj):       
        representation = super().to_representation(obj)
        return {
            'id': str(representation['id']),
            'message_id': str(representation['message_id']),
            'read_by_chat_user_id': str(representation['read_by_chat_user_id']),
            'delivered_to_chat_user_id': str(representation['delivered_to_chat_user_id']),
            'created_at': representation['created_at'],
            'updated_at': representation['updated_at'],
            'deleted_at': representation['deleted_at']
        }