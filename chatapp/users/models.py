import uuid
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractBaseUser

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
ROOM_TYPE =[
    ("individual", "individual"),
    ("group", "group")
]
LAST_MSG_TYPE = [
    ("text","text"),
    ("image","image"),
    ("video","video")
]
# DEVICE = [
#     ("ios","ios"),
#     ("android", "android"),
# ]

class User(AbstractBaseUser):
    """Records of all Users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50 ,null= True, blank=True)
    phone_number = PhoneNumberField(unique =True, blank=False, null=False)
    profile_picture = models.FileField(upload_to="uploads/", null=True, blank=True)
    status_quotes = models.CharField(max_length=150, null=True, blank=True)
    user_active = models.CharField( max_length=50,choices=STATUS, default="active")  # Should default to Active.FALSE
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # REQUIRED_FIELDS = ['phone_number']
    
    USERNAME_FIELD = "phone_number"

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

class ContactList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete= models.CASCADE, related_name='user_id', db_column='user_id')
    contact_user_id = models.ForeignKey(User, on_delete=models.CASCADE,related_name='contact_user_id', db_column ='contact_user_id',null=True, blank=True)
    contact_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = PhoneNumberField(blank=False, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_contact_list'
        ordering = ['-created_at']


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete= models.CASCADE, db_column='user_id')
    device_token = models.CharField(max_length=255,null=True, blank=True) 
    device_id = models.CharField(max_length=100, null=True, blank=True)
    device_type = models.CharField( max_length=50)  
    jwt_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'session'
        ordering = ['-created_at']

class Privacy(models.Model):
    """Users privacy settings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete= models.CASCADE, db_column='user_id')
    last_seen_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    profile_picture_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    status_visibility = models.CharField(max_length=50, choices=VISIBILITY, default="public")
    message_receipts = models.CharField(max_length=50, choices=TYPE, default="on")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'privacy_settings'
        ordering = ['-created_at']

class BlockList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user_id = models.ForeignKey(User, on_delete= models.CASCADE, related_name='blocked_from',db_column='from_user_id')
    to_user_id = models.ForeignKey(User, on_delete= models.CASCADE, related_name='blocked_to',db_column='to_user_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_blocked_list'
        ordering = ['-created_at']



class Room(models.Model):
    '''
    Room table records
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.CharField(max_length=50, choices= ROOM_TYPE, default="group")
    group_name = models.CharField(max_length=100, null=True, blank=True)
    group_picture = models.FileField(upload_to="uploads/", null=True, blank=True)
    group_quotes = models.TextField(null= True, blank=True)
    last_msg_sender_id = models.ForeignKey(User, on_delete= models.CASCADE, db_column='last_msg_sender_id')
    last_msg_sent_by = models.CharField(max_length=100)
    last_msg = models.TextField()
    last_msg_type = models.CharField(max_length=50, choices=LAST_MSG_TYPE, default="text")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'room'
        ordering = ['-created_at']

class GroupMembers(models.Model):
    '''
    records of group members
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_id = models.ForeignKey(Room, on_delete= models.CASCADE, db_column ='room_id')
    member_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column = 'member_id')
    group_picture = models.FileField(upload_to="uploads/", null=True, blank=True)
    is_admin = models.CharField(max_length=50,choices=TYPE, default ="off")
    # removed_by = models.ForeignKey(User)
    is_deleted = models.CharField(max_length=50, choices=TYPE, default= "off")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'group_members'
        ordering = ['-created_at']

# class Messages(models.Model):
#     '''
#     records of message
#     '''
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     room_id = models.ForeignKey(Room, on_delete= models.CASCADE, db_column ='room_id')
#     sender_id = models.ForeignKey(User, on_delete= models.CASCADE, db_column='user_id')
#     message_type = models.CharField(choices=Status.choices, default =  Status.SENT)
#     file_path = models.FileField(upload_to="uploads/", null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
#     deleted_at = models.DateTimeField(null=True, blank=True)
    
#     class Meta:
#         db_table = 'messages'
#         ordering = ['-created_at']