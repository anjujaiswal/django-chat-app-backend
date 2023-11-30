from rest_framework import serializers
from .models import User,UsersMapping,UserStatus, ContactList, Session, Privacy, BlockList, Room, GroupMembers,MessageHistory,Messages#, Messages #Users
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator
import re
class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user model."""

     # Validator for the phone number
    phone_regex = RegexValidator(
        regex= r'^\d{7,15}$',
        message="Please enter a valid phone number"
    )

    # Validator for the country code
    country_code_regex = RegexValidator(
        regex=r'^\+\d{1,3}$',
        message="Please enter a valid phone number"
    )

   
    phone_number = serializers.CharField(validators=[phone_regex])
    country_code = serializers.CharField(validators=[country_code_regex])

    class Meta:
        model = User
        fields = ['user_id','country_code', 'phone_number']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the user model."""

   
    class Meta:
        model = User
        fields = ['user_id','country_code', 'phone_number', 'username', 'profile_picture']


class UsersMappingSerializer(serializers.ModelSerializer):
    '''serializer for UsersMapping'''
   
    class Meta:
        model = UsersMapping
        fields = '__all__'

class UserStatusSerializer(serializers.ModelSerializer):
    '''
    serializer for user status 
    '''
    class Meta:
        model = UserStatus
        fields = '__all__'

#this serializer is useful in making getcontactlist api if to add details of the users
class UsersMappingcontactSerializer(serializers.ModelSerializer):
    '''serializer for UsersMapping'''
    user_details = UserSerializer(source = 'app_user_id')
    class Meta:
        model = UsersMapping
        fields = '__all__'



class ContactListSerializer(serializers.ModelSerializer):
    """
    serializer for contactlist model to include the information of users (used in get contactlist api)
    """
    # contact_user_id = UserSerializer() ###for showing user details as well
    # contact_chat_user_id = UsersMappingcontactSerializer()
    mapping_details = UsersMappingcontactSerializer(source = 'contact_chat_user_id')
    phone_regex = RegexValidator(
        regex=r'^\d{7,12}$^',
        message="Please enter a valid phone number"
    )
    phone_number = serializers.CharField(validators=[phone_regex])
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
        # fields = '__all__'
        exclude = ['setting_id','created_at','deleted_at', 'updated_at']

class BlockListSerializer(serializers.ModelSerializer):
    # to_user = UserSerializer(source='to_user_id', read_only=True)####to add user details
    # to_chat_user_id = UsersMappingcontactSerializer( read_only=True)####to add user details to_chat_user_id  
    # mapping_details = UsersMappingcontactSerializer(source = 'to_chat_user_id', read_only=True)
    class Meta:
        model = BlockList
        # fields = '__all__'
        exclude = ['created_at', 'deleted_at', 'updated_at']
    def to_representation(self, instance):
        representation =  super().to_representation(instance)
        # users_mapping_instance = instance.contact_chat_user_id
        representation['username'] = instance.to_chat_user_id.app_user_id.username
        representation['phone_number'] = instance.to_chat_user_id.app_user_id.phone_number
        representation['country_code'] = instance.to_chat_user_id.app_user_id.country_code
        if instance.to_chat_user_id.app_user_id.profile_picture:
            representation['profile_picture'] = instance.to_chat_user_id.app_user_id.profile_picture
        else:
            representation['profile_picture'] = None
        return representation
class BlockingSerializer(serializers.ModelSerializer): #use this serializer in blocking api
    '''serializer of block model'''
    class Meta:
        model = BlockList
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    '''serializer of room model'''
    class Meta:
        model =  Room
        fields = '__all__'

class GroupMembersSerializer(serializers.ModelSerializer):
    '''serializer of group member model'''
    class Meta:
        model =  GroupMembers
        fields = '__all__'

class GroupMembersgettingSerializer(serializers.ModelSerializer):
    '''serializer of group member model'''
    # chat_user_id = UsersMappingcontactSerializer( read_only=True)####to add user details to_chat_user_id  
    # mapping_details = UsersMappingcontactSerializer( source = 'chat_user_id',read_only=True)
    class Meta:
        model =  GroupMembers
        fields = ['id', 'chat_user_id', 'room_id', 'is_admin']

class UserstatuswithprofileSerializer(serializers.ModelSerializer):
    # app_user_id = UserSerializer()
    mapping_details = UsersMappingcontactSerializer(source  = 'chat_user_id')
    class Meta:
        model =  UserStatus
        fields = '__all__'

class Userstatusprofileserializer(serializers.ModelSerializer):
    class Meta:
        model = UserStatus
        fields = ['status_quotes','is_active']

class GetContactListSerialzier(serializers.ModelSerializer):
    class Meta:
        model = ContactList
        fields = ['id', 'chat_user_id', 'contact_name', 'phone_number','contact_chat_user_id']
    def to_representation(self, instance):
        representation =  super().to_representation(instance)
        # users_mapping_instance = instance.contact_chat_user_id
        if(instance.contact_chat_user_id):
            # print(instance.contact_chat_user_id.app_user_id)
            representation['username'] = instance.contact_chat_user_id.app_user_id.username #instance.contact_chat_user_id__app_user_id__username
            # representation['status_quotes'] = related_data
            if instance.contact_chat_user_id.app_user_id.profile_picture:
                representation['profile_picture'] = instance.contact_chat_user_id.app_user_id.profile_picture
            else:
                representation['profile_picture'] = None
        return representation

class MessageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageHistory
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    # message = MessageHistorySerializer(source = 'message_id')
    class Meta:
        model = Messages
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id','username','phone_number','profile_picture']
        # def create(self, validated_data):
        #     """
        #     Create and return a new `User` instance, given the validated data.
        #     """
        #     return User.objects.create(**validated_data)
        

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['user_id','device_id','device_token', 'device_type', 'jwt_token']
        # def create(self, validated_data):
        #     """
        #     Create and return a new `User` instance, given the validated data.
        #     """
        #     return Session.objects.create(**validated_data)
        