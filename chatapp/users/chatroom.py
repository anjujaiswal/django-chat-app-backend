from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User, Session, ContactList, Privacy,  GroupMembers # Chats, Messages,
from .serializers import ChatsSerializer, GroupMembersSerializer #MessagesSerializer,
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


class AddGroup(APIView):
    permission_classes = [ ApiKey, IsAuthenticated ]
    def post(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            room_type = payload.get('room_type',None)
            group_picture = payload.get('group_picture', None)
            group_quotes = payload.get('group_quotes', None)
            list_of_members = payload.get('list_of_members', [])
            group_data = { 'room_type' : 1, 'group_picture': group_picture, 'group_quotes': group_quotes}
            individual_data = { 'room_type' : 0, }

            flag = 0
            chat_obj = 0
            room_id = ''
            serialized_chat_data = {}
            # contact_objects = ContactList.objects.filter(user_id = user_id).exclude(contact_user_id=None)
            # print(contact_objects)
            # Extract the values of a particular field and create a list
            # print((contact_objects))
            # contact_list = [str(obj.contact_user_id) for obj in contact_objects]
            # for obj  in contact_objects:
                # print(str(obj.contact_user_id))
                # print(obj)
            # contact_list = contact_objects.values_list('contact_user_id', flat=True)
            contact_list = ContactList.objects.filter(user_id = user_id).exclude(contact_user_id=None).values('contact_user_id')
            contact_list = list(contact_list.values_list('contact_user_id', flat=True))
            contact_list = [str(uuid) for uuid in contact_list]
            # print(contact_list)
            # print('c1e5bf18-767f-41c8-944f-2bbd0c1afa21' in contact_list)
            group_members_objs = []
            # group_serialized_data = {}
            for member in list_of_members:
                if member.get('user_id', None) not in contact_list:
                    return json_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message='List of members is not in contact list')
                
                
            if(room_type == 0):
                if len(list_of_members)!=1:
                    return json_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message='List of members should be 1')
                serializer_chat = ChatsSerializer(data = individual_data)
                if serializer_chat.is_valid():
                    flag = 1
                    serializer_chat.save()
                    serialized_chat_data = serializer_chat.data
            else:
                if len(list_of_members)<=1:
                    return json_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message='List of members should more than 1')
                
                serializer_chat = ChatsSerializer(data = group_data)
                if serializer_chat.is_valid():
                    flag = 1
                    serializer_chat.save()
                    serialized_chat_data = serializer_chat.data
            if flag:
                # print("==",serialized_data)
                room_id = serialized_chat_data.get('id')
            else:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Chat room is not created')
            if room_type == 0:
               
                serializer = GroupMembersSerializer(data = [{'room_id':room_id, 'member_id': user_id, 'is_admin':1},
                                                            {'room_id':room_id, 'member_id': list_of_members[0].get('user_id'), 'is_admin':1}
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
                
            instance =GroupMembers(room_id = Chats(id = room_id), member_id = User(id = user_id), is_admin = 1)
            group_members_objs.append(instance)
            for member in list_of_members:
                user_id = member.get('user_id')
                instance = GroupMembers(room_id = Chats(id = room_id), member_id = User(id = user_id))
                group_members_objs.append(instance)
            
            GroupMembers.objects.bulk_create(group_members_objs)
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
    permission_classes = [ ApiKey, IsAuthenticated ]
    def patch(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            room_id = payload.get('room_id', None)
            member_id = payload.get('member_id', None)
            if room_id is None or member_id is None:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= 'room_id/ member_id is missing')
            
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))   
        





