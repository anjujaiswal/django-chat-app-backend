from rest_framework import serializers
from .models import User,UsersMapping,UserStatus, ContactList, Session, Privacy, BlockList, Room, GroupMembers #, Messages #Users
from phonenumber_field.modelfields import PhoneNumberField

class UserSerializer(serializers.ModelSerializer):
    """serializer for user model"""
    class Meta:
        model = User
        # fields = '__all__'
        # fields = ['user_id','username','phone_number','profile_picture']
        fields = ['user_id','username','phone_number','profile_picture']
        # exclude = ('password','last_login')

    # def validate_phone_number(self, value):
    #     print(value)
    #     if  len(value)!=10:
    #         raise serializers.ValidationError("Phone number must be a 10-digit number.")
    #     return value  
    # def create(self, validated_data):
    #     return User.objects.create(**validated_data)

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
    # to_user = UserSerializer(source='to_user_id', read_only=True)####to add user details
    # to_chat_user_id = UsersMappingcontactSerializer( read_only=True)####to add user details to_chat_user_id  
    mapping_details = UsersMappingcontactSerializer(source = 'to_chat_user_id', read_only=True)
    class Meta:
        model = BlockList
        fields = '__all__'

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
    mapping_details = UsersMappingcontactSerializer( source = 'chat_user_id',read_only=True)
    class Meta:
        model =  GroupMembers
        fields = '__all__'

class UserstatuswithprofileSerializer(serializers.ModelSerializer):
    # app_user_id = UserSerializer()
    mapping_details = UsersMappingcontactSerializer(source  = 'chat_user_id')
    class Meta:
        model =  UserStatus
        fields = '__all__'


# class MessagesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model =  Messages
#         fields = '__all__'


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
        