from rest_framework import serializers
from .models import User, ContactList, Session, Privacy, BlockList, Room, GroupMembers #, Messages #Users
from phonenumber_field.modelfields import PhoneNumberField

class UserSerializer(serializers.ModelSerializer):
    """serializer for user model"""
    class Meta:
        model = User
        # fields = '__all__'
        exclude = ('password','last_login')

class ContactListSerializer(serializers.ModelSerializer):
    """serializer for contactlist model"""
    contact_user_id = UserSerializer() ###for showing user details as well
    class Meta:
        model = ContactList
        fields = '__all__'

class ContactListSyncSerializer(serializers.ModelSerializer):
    """serializer for contactlist model"""
    # contact_user_id = UserSerializer() ###for showing user details as well
    class Meta:
        model = ContactList
        fields = '__all__'
    
class SessionSerializer(serializers.ModelSerializer):
    """serializer for session model"""
    class Meta:
        model = Session
        fields = '__all__'

class PrivacySerializer(serializers.ModelSerializer):
    """serializer for privacy model"""
    class Meta:
        model = Privacy
        fields = '__all__'

class BlockListSerializer(serializers.ModelSerializer):
    # to_user = UserSerializer(source='to_user_id', read_only=True)####to add user details to_user se ayega
    to_user_id = UserSerializer( read_only=True)####to add user details to_user_id se ayega
    
    class Meta:
        model = BlockList
        fields = '__all__'

class ChatsSerializer(serializers.ModelSerializer):
    class Meta:
        model =  Room
        fields = '__all__'

class GroupMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model =  GroupMembers
        fields = '__all__'

# class MessagesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model =  Messages
#         fields = '__all__'


class RegisteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','phone_number','profile_picture','status_quotes']
        def create(self, validated_data):
            """
            Create and return a new `User` instance, given the validated data.
            """
            return User.objects.create(**validated_data)
        

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['user_id','device_id','device_token', 'device_type', 'jwt_token']
        # def create(self, validated_data):
        #     """
        #     Create and return a new `User` instance, given the validated data.
        #     """
        #     return Session.objects.create(**validated_data)
        
        
        
