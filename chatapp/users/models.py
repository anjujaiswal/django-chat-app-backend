import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractBaseUser
DEVICE_TYPE = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3")
]
DELETE = [
    ("me", "me"),
    ("all", "all"),
    ("None",None)
]
STATUS = [
    ("active", "active"),
    ("inactive", "inactive")
]
VISIBILITY = [
    ("nobody","nobody"),
    ("public", "public"),
    ("contacts", "contacts")
]

TYPE = [
   ( "on","on"),
   ("off","off")
]
ONLINE = [
    ("online","online"),
    ("offline", "offline")
]
ROOM_TYPE =[
    ("individual", "individual"),
    ("group", "group")
]
LAST_MSG_TYPE = [
    ("text","text"),
    ("image","image"),
    ("video","video"),
    ("location", "location"),
    ("contact","contact"),
    ("document","document"),
    ("None",None)
]
# DEVICE = [
#     ("ios","ios"),
#     ("android", "android"),
# ]

class User(AbstractBaseUser):
    """Records of all Users"""
    
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50 ,null= True, blank=True)
    country_code = models.CharField(max_length = 5, null = False, blank =False)
    phone_number = models.CharField( blank=False, null=False)
    # profile_picture = models.FileField(upload_to="uploads/", null=True, blank=True)
    profile_picture = models.CharField(max_length= 100, default=None, null = True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # REQUIRED_FIELDS = ['phone_number']
    
    USERNAME_FIELD = "user_id"

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return str(self.user_id)
    
class UsersMapping(models.Model):
    '''
    Intermediate model between third party user table and our chat application
    '''
    chat_user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_user_id = models.ForeignKey(User, on_delete= models.CASCADE, related_name='mapping_user_id', db_column='app_user_id')
    user_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.chat_user_id)
    
    class Meta:
        db_table = 'users_mapping'
        ordering = ['-created_at']

class ContactList(models.Model):
    '''
    records of contactlist of user
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name='contactlist_chat_user_id', db_column='chat_user_id')
    contact_chat_user_id = models.ForeignKey(UsersMapping, on_delete=models.CASCADE,related_name='contactlist_contact_chat_user_id', db_column ='contact_chat_user_id',null=True, blank=True)
    contact_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(blank=False, unique=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)
    
    class Meta:
        db_table = 'user_contact_list'
        ordering = ['-created_at']

class UserStatus(models.Model):
    '''Record of user status'''
    id =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_user_id =  models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name='status_chat_user_id', db_column='chat_user_id')
    status = models.CharField(max_length=100 , choices=ONLINE, default="offline")
    timestamp = models.DateTimeField(null=True, blank=True)
    status_quotes = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.BooleanField( default=True)  # Should default to Active.FALSE
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'user_status'
        ordering = ['-created_at']

#directed connected to user table because we are not using it 
class Session(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # chat_user_id = models.ForeignKey(User, on_delete= models.CASCADE, related_name='session_chat_user_id',db_column='chat_user_id')
    chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name='session_chat_user_id',db_column='chat_user_id')
    device_token = models.CharField(max_length=255, null= False, blank=False) 
    device_id = models.CharField(max_length=100, null= False, blank=False)
    device_type = models.CharField( max_length=5 , choices=DEVICE_TYPE, null= False, blank=False)  
    jwt_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.session_id)

    class Meta:
        db_table = 'session'
        ordering = ['-created_at']

class Privacy(models.Model):
    '''
    Records of privacy settings
    '''
    setting_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name= 'privacy_chat_user_id',db_column='chat_user_id')
    last_seen_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    profile_picture_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    status_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    message_receipts = models.CharField(max_length=50, choices=TYPE, default="on")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.setting_id)
    
    class Meta:
        db_table = 'privacy_settings'
        ordering = ['-created_at']

class BlockList(models.Model):
    '''
    records of blocked users
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name='blocked_from',db_column='from_chat_user_id')
    to_chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, related_name='blocked_to',db_column='to_chat_user_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.id)
    
    class Meta:
        db_table = 'user_blocked_list'
        ordering = ['-created_at']



class Room(models.Model):
    '''
    Room table records
    '''
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.CharField(max_length=50, choices= ROOM_TYPE, default="group")
    group_name = models.CharField(max_length=100, null=True, blank=True)
    # group_picture = models.FileField(upload_to="uploads/", null=True, blank=True)
    group_picture = models.CharField(max_length=100, default=None, null = True, blank=True)
    group_quotes = models.TextField(null= True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.room_id)
    
    class Meta:
        db_table = 'room'
        ordering = ['-created_at']

class GroupMembers(models.Model):
    '''
    records of group members
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_id = models.ForeignKey(Room, related_name='group_member', on_delete= models.CASCADE, db_column ='room_id')
    chat_user_id = models.ForeignKey(UsersMapping, on_delete=models.CASCADE, related_name='member_chat_user_id',db_column = 'chat_user_id')
    is_admin = models.BooleanField(default=False)
    removed_by = models.ForeignKey(UsersMapping, on_delete=models.CASCADE,related_name='removed_by', db_column = 'removed_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.id)
    
    class Meta:
        db_table = 'group_members'
        ordering = ['-created_at']

class Messages(models.Model):
    '''
    records of message
    '''
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_id = models.ForeignKey(Room, on_delete= models.CASCADE, db_column ='room_id',related_name='room_messages')
    sender_chat_user_id = models.ForeignKey(UsersMapping, on_delete= models.CASCADE, db_column='sender_chat_user_id')
    message_type = models.CharField(max_length=50, choices=LAST_MSG_TYPE, null=True, blank=True)
    message_content = models.TextField(null=True, blank=True)
    file_path = models.CharField(max_length= 150, default=None, null = True, blank=True)
    thumbnail_file_path = models.CharField(max_length= 100, default=None, null = True, blank=True)
    deleted_for = models.CharField(max_length=50, choices= DELETE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.message_id)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

class MessageHistory(models.Model):
    '''
    records of message history
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.ForeignKey(Messages, related_name='to_messages', on_delete= models.CASCADE, db_column ='message_id')
    read_by_chat_user_id = models.ForeignKey(UsersMapping,on_delete= models.CASCADE, related_name='read_by',db_column='read_by_chat_user_id',null=True, blank=True)
    delivered_to_chat_user_id = models.ForeignKey(UsersMapping, on_delete = models.CASCADE, related_name='delivered_to', db_column='delivered_to_chat_user_id',null=True, blank=True)
    receivers_id = models.ForeignKey(UsersMapping,on_delete=models.CASCADE, related_name='receivers_id', db_column='receivers_id', null=True, blank=True)
    room_id = models.ForeignKey(Room, on_delete = models.CASCADE, related_name='from_room', db_column='room_id', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return str(self.id)
    
    class Meta:
        db_table = 'message_history'
        ordering = ['-created_at']