from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UsersMapping, Session, ContactList, Privacy,  GroupMembers, Room# Chats, Messages,
from .serializers import  RoomSerializer, GroupMembersSerializer #MessagesSerializer,
import json
from rest_framework import status
from utils.helpers import json_response, get_tokens_for_user, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization

from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
import datetime
 


class AddGroup(APIView):
    '''
    Api for creating room and adding its members in the group members table
    '''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def post(self, request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            room_type = payload.get('room_type',None)
            group_picture = payload.get('group_picture', None)
            group_quotes = payload.get('group_quotes', None)
            group_name = payload.get('group_name', None)
            list_of_members = payload.get('list_of_members', [])
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            group_data = { 'room_type' : room_type,
                        'group_picture': group_picture, 
                        'group_quotes': group_quotes,
                        'group_name': group_name  }
            individual_data = { 'room_type' : room_type, }

            flag = 0
            chat_obj = 0
            room_id = ''
            serialized_chat_data = {}
           #list of contacts who use chat app
            # contact_list = ContactList.objects.filter(user_id = user_id).exclude(contact_user_id=None).values('contact_user_id')
            # contact_list = list(contact_list.values_list('contact_user_id', flat=True))
            # contact_list = [str(uuid) for uuid in contact_list]
            
            group_members_objs = []
            #we can create group only with ppl who are in our contact list and chat app user
            #check for that
            # for member in list_of_members:
            #     member_id = member.get('user_id', None)

            #     if member.get('user_id', None) not in contact_list:
            #         return json_response(success=False,
            #                             status_code=status.HTTP_400_BAD_REQUEST,
            #                             message='List of members is not in contact list/send invitation')
                
                
            if(room_type == "individual"):
                if len(list_of_members)!=1:
                    return json_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message='List of members should be 1')
                
                #creating room if room type is individual ----use individual data
                serializer_chat = RoomSerializer(data = individual_data)
                # print(serializer_chat)
                if serializer_chat.is_valid():
                    flag = 1
                    # print("ff")
                    serializer_chat.save()
                    serialized_chat_data = serializer_chat.data
                else:
                    print(serializer_chat.errors)
                    return json_response(success=False,
                                         status_code=status.HTTP_400_BAD_REQUEST,
                                        message="Individual group not created")
            else:
                if len(list_of_members)<=1:
                    return json_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message='List of members should more than 1')
                #creating room -------> if room type is group so use group data
                serializer_chat = RoomSerializer(data = group_data)
                if serializer_chat.is_valid():
                    flag = 1
                    serializer_chat.save()
                    serialized_chat_data = serializer_chat.data
            if flag:
                # print("==",serialized_data)
                room_id = serialized_chat_data.get('room_id')
            else:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Chat room is not created')
            
            #this for adding members in group members table if room type ---------> individual
            if room_type == "individual":
                
                serializer = GroupMembersSerializer(data = [{'room_id':room_id, 
                                                            'chat_user_id': chat_user_id, 
                                                            'is_admin':"on", 
                                                            # "username": user_obj.username,
                                                            # "profile_picture": user_obj.profile_picture
                                                            },

                                                            {'room_id':room_id,
                                                            'chat_user_id': list_of_members[0].get('chat_user_id'), 
                                                            'is_admin':"on",
                                                            # "username":list_of_members[0].get('username',None),
                                                            # "profie_picture": list_of_members[0].get('profile_picture',None)
                                                            }
                                                            ], many= True)
                if serializer.is_valid():
                    serializer.save()
                    return json_response(success=True, 
                                        status_code=status.HTTP_201_CREATED,
                                        message='Individual group created',
                                        result=serialized_chat_data)
                else: 
                    return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Individual members not added')
                
            # if  room_type is -->group then adding members in groupmember table
            data_create = []
            dict = {
                    "room_id": room_id,
                    # "member_id": str(user_id),
                    "chat_user_id": chat_user_id,
                    "is_admin": "on",
                    # "username": user_obj.username,
                    # "profile_picture": user_obj.profile_picture
            }
            data_create.append(dict)
            for member in list_of_members:
                dict = {
                    "room_id": room_id,
                    "chat_user_id": member.get('chat_user_id'),
                    # "username": member.get('username',None),
                    # "profile_picture": member.get('profile_picture', None)
                }
                data_create.append(dict)
            serializer_room = GroupMembersSerializer(data = data_create, many=True)
            if serializer_room.is_valid():
                # print("room_cr")
                serializer_room.save()
            else:
                print(serializer_room.errors)
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message="Group not created")
            
            return json_response(success=True, 
                                        status_code=status.HTTP_201_CREATED,
                                        message='Group chat created',
                                        result = serialized_chat_data)

        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))   
        
class GiveAdminRights(APIView):
    '''
    api to make admin a user in a room
    '''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def patch(self, request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            user_obj = request.user
            #getting app_user_id from using token user_id
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            payload = request.data
           
            room_id = payload.get('room_id', None)
            member_id = payload.get('chat_user_id', None)
            
            if room_id is None or member_id is None:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= 'room_id/ member_id is missing')
            
            if str(chat_user_id) == str(member_id):#without str it gives false 
                return json_response(success=False,
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    message='You cant make yourself admin')
            token_group_member_obj = None
            try:
                token_group_member_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = usermapping_obj, removed_by = None)
            except GroupMembers.DoesNotExist:
                return json_response(success=False,
                                     status_code=status.HTTP_403_FORBIDDEN,
                                     message='You are not present in the group')
            if token_group_member_obj.is_admin == "off":
                return json_response(success=False,
                                     status_code = status.HTTP_403_FORBIDDEN,
                                     message='You are not admin you cant make other member admin')
            
            groupmember_obj = None
            #checking that given member is present in the group or not
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = member_id, removed_by = None)
            except GroupMembers.DoesNotExist:
                return json_response(success=False,
                                     status_code= status.HTTP_400_BAD_REQUEST,
                                     message='Member is not present in the group')
            # if groupmember_obj.is_admin == "on":
            #     groupmember_obj.is_admin = "off"
            #     groupmember_obj.save()
            #     return json_response(success=True,
            #                     status_code=status.HTTP_200_OK,
            #                     message='Updated as non-admin'
            #                     )
            # else:
            #     groupmember_obj.is_admin = "on"
            # groupmember_obj.save()
            if groupmember_obj.is_admin == "on":
                return json_response(success=True,
                                status_code=status.HTTP_200_OK,
                                message='Aready admin'
                                )
            groupmember_obj.is_admin = "on"
            groupmember_obj.save()
            return json_response(success=True,
                                status_code=status.HTTP_200_OK,
                                message='Updated as admin'
                                )
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = 'INTERNAL_SERVER_ERROR',
                                    result = {},
                                    error = str(err))   
        

class RemoveMember(APIView):
    '''
    api to remove member from the group only if user is admin in that group
    '''
    permission_classes = [ ApiKey, IsAuthenticated]
    def patch(self,request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            room_id = payload.get('room_id', None)
            member_id = payload.get('chat_user_id', None)
            if room_id is None or member_id is None:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= 'room_id/ member_id is missing')
            groupmember_obj = None# this represents to whom we want to remove
            #checking for member existence /soft delete
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = member_id, removed_by = None)
            except GroupMembers.DoesNotExist:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='This member is not in the group')
            #if user want to left the group
            if str(chat_user_id) == str(member_id):
               
                groupmember_obj.deleted_at = datetime.datetime.now()
                groupmember_obj.removed_by = usermapping_obj
                groupmember_obj.is_admin = "off"
                groupmember_obj.save()
                print(groupmember_obj.is_admin,"user left")
                group_admin_objs = GroupMembers.objects.filter(room_id = room_id, is_admin = "on", removed_by = None)
               
                #checking is there any other admin in group or not if not
                # print(group_admin_objs)
                if len(group_admin_objs) == 0:
                    group_member_all_objs = GroupMembers.objects.filter(room_id = room_id, removed_by = None).order_by('created_at')
                    
                    #if one by one there is no member then we cant make anyone admin
                    if len(group_member_all_objs) > 0:
                        make_admin = group_member_all_objs[0]
                        make_admin.is_admin = "on"
                        make_admin.save()
                return json_response(success=False,
                                status_code= status.HTTP_200_OK,
                                message= 'User left the room successfully')
        
            #if token_user is himself admin or not check other wise can remove other 
            token_group_member_obj = None
            try:
                token_group_member_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = usermapping_obj, removed_by = None)
            except GroupMembers.DoesNotExist:
                return json_response(success=False,
                                     status_code=status.HTTP_403_FORBIDDEN,
                                     message='You are not present in the group')
            if token_group_member_obj.is_admin == "off":
                return json_response(success=False,
                                     status_code = status.HTTP_403_FORBIDDEN,
                                     message='You are not admin you cant remove other member')
            
            #if member is admin you cant remove another admin from the group
            if groupmember_obj.is_admin == "on":
                return json_response(success=False,
                                     status_code=status.HTTP_403_FORBIDDEN,
                                     message="FORBIDDEN - Cant remove another admin")
            
            # #makin the soft delete and filling the date_time result

            # groupmember_obj.is_deleted = "on"
            groupmember_obj.deleted_at = datetime.datetime.now()
            groupmember_obj.removed_by = usermapping_obj
            groupmember_obj.is_admin = "off"
            groupmember_obj.save()
           
            return json_response(success=False,
                                status_code= status.HTTP_200_OK,
                                message= 'Member is removed successfully')
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = 'INTERNAL_SERVER_ERROR',
                                    result = {},
                                    error = str(err))   
        


