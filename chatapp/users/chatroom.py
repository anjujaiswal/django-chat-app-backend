from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UsersMapping, Session, ContactList, Privacy,  GroupMembers, Room# Chats, Messages,
from .serializers import  RoomSerializer, GroupMembersSerializer,GroupMembersgettingSerializer #MessagesSerializer,
import json
from rest_framework import status
from utils.helpers import json_response, error_response, get_tokens_for_user, serializer_error_format,serializer_error_list, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization

from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
import datetime
from common.constants import Constants, ErrMsg, ErrMsgCode, ROOM_TYPE,IS_ADMIN
import traceback
from django.db.models import Count
from django.core.paginator import Paginator
import uuid
import logging
logger_error = logging.getLogger('error_logger')
logger_info = logging.getLogger('info_logger')

class AddGroup(APIView):
    '''
    Api for creating room and adding its members in the group members table
    '''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def post(self, request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            # user_obj = request.user
            room_type = payload.get('room_type',None)
            #this variable is used to know that room is created or not usefull in case of individual room
            created_room = 0
            room_type_list = [ROOM_TYPE.INDIVIDUAL, ROOM_TYPE.GROUP] 
            if room_type not in room_type_list:
                return error_response(success=False,
                                      status_code= status.HTTP_400_BAD_REQUEST,
                                      message_code= ErrMsgCode.PAYLOAD_INCORRECT,
                                      error_msg=  ErrMsg.ROOM_TYPE_WRONG
                                      )

            # if room_type == ROOM_TYPE.INDIVIDUAL or room_type == ROOM_TYPE.GROUP:
            #    pass
            # else:
            #     return error_response(success=False,
            #                           status_code= status.HTTP_400_BAD_REQUEST,
            #                           message_code= ErrMsgCode.PAYLOAD_INCORRECT,
            #                           error_msg=  ErrMsg.ROOM_TYPE_WRONG
            #                           )
            group_picture = payload.get('group_picture', None)
            group_quotes = payload.get('group_quotes', None)
            group_name = payload.get('group_name', None)
            list_of_members = payload.get('list_of_members', [])
            # usermapping_obj = None
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            chat_user_id = usermapping_obj.chat_user_id
            # print('token person', chat_user_id)
            #checking list_of_members are in right format
            for member in list_of_members:
                input_uuid = member.get('chat_user_id', None)
                if input_uuid == None:
                    return error_response(success=False,
                                          message=Constants.PAYLOAD_INCORRECT,
                                          status_code=status.HTTP_400_BAD_REQUEST,
                                          message_code=ErrMsgCode.PAYLOAD_INCORRECT,
                                          error_msg=ErrMsg.PROVIDE_CHAT_USER_ID)
                # list of members should not contain your chat_user_id
                if input_uuid == str(chat_user_id):
                    return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.ROOM_CREATE_UNSUCCESSFULL,
                                        error_msg=ErrMsg.PROVIDE_CONTACT_CHAT_USER_ID,
                                        message_code=ErrMsgCode.PAYLOAD_INCORRECT
                                        )
                
                try:
                    uuid_obj = uuid.UUID(input_uuid)
                    print('txt',str(uuid_obj) == input_uuid)
                except:
                    return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.PROVIDE_UUID,
                                    error_msg=ErrMsg.PROVIDE_UUID,
                                    message_code=ErrMsgCode.PROVIDE_UUID
                                    )
            
            group_data = { 'room_type' : room_type,
                        'group_picture': group_picture, 
                        'group_quotes': group_quotes,
                        'group_name': group_name  }
            individual_data = { 'room_type' : room_type, }
            # flag variable is used to check the the existence of room after creation
            flag = 0
            # chat_obj = 0
            room_id = ''
            serialized_chat_data = {}
                
            if(room_type == ROOM_TYPE.INDIVIDUAL):
                if len(list_of_members)!=1:
                    return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.WRONG_LENGTH_OF_LIST_OF_MEMBERS,
                                        error_msg=  ErrMsg.WRONG_LENGTH_OF_LIST_OF_MEMBERS,
                                        message_code=  ErrMsgCode.PAYLOAD_INCORRECT
                                        )
                friend_chat_user_id = list_of_members[0].get('chat_user_id',None)
                try:
                    friend_user_mapping_obj = UsersMapping.objects.get(chat_user_id = friend_chat_user_id)
                except:
                    return error_response(success=False,
                                          status_code=status.HTTP_400_BAD_REQUEST,
                                          message=Constants.FRIEND_NOT_FOUND,
                                          error_msg=ErrMsg.FRIEND_NOT_FOUND,
                                          message_code=ErrMsgCode.FRIEND_NOT_FOUND
                                          )
                print('friend_user', friend_user_mapping_obj)
                # contactlist_obj = None
                try:
                    contactlist_obj = friend_user_mapping_obj.contactlist_contact_chat_user_id.get(chat_user_id =chat_user_id )
                except:
                    return error_response(success=False,
                                          status_code=status.HTTP_400_BAD_REQUEST,
                                          message= Constants.CONTACT_NOT_FOUND,
                                          message_code=ErrMsgCode.CONTACT_NOT_FOUND,
                                          error_msg=ErrMsg.CONTACT_NOT_FOUND
                                          )
                print('contactlist',contactlist_obj)
                # userstatus_obj = None
                try:
                    userstatus_obj = friend_user_mapping_obj.status_chat_user_id.get(chat_user_id = friend_chat_user_id)
                except:
                    return error_response(success=False,
                                          status_code=status.HTTP_400_BAD_REQUEST,
                                          message=Constants.USER_STATUS_NOT_FOUND,
                                          error_msg=ErrMsg.USER_STATUS_NOT_FOUND,
                                          message_code=ErrMsgCode.USER_STATUS_NOT_FOUND
                    )
                print('userstatus',userstatus_obj, type(userstatus_obj))
                # print(friend_user_mapping_obj.app_user_id.username)
               
                chat_user_ids = []
                # print(type(str(chat_user_id)),type(list_of_members[0].get('chat_user_id')))
                chat_user_ids.append(str(chat_user_id))
                chat_user_ids.append(list_of_members[0].get('chat_user_id'))
                # print(chat_user_ids)
                ##before creating need to check already exists or not room
                # chat_user_ids_str = "', '".join(chat_user_ids)
                # print(serializer_chat)
                # raw_sql_query = f"""
                #     SELECT room_id
                #     FROM group_members
                #     WHERE chat_user_id IN ('{chat_user_ids_str}')
                #     GROUP BY room_id
                #     HAVING COUNT(room_id) = 2
                #     """
                
                results = GroupMembers.objects.filter(chat_user_id__in=chat_user_ids, room_id__room_type = ROOM_TYPE.INDIVIDUAL).values('room_id').annotate(
                    user_count=Count('room_id')
                ).filter(user_count=2).values_list('room_id', flat=True)
                print("room_ids: ", results)
               # print(len(results))
                # print(results)
                if len(results) != 0:
                    created_room = 1
                    flag = 1
                #dont add in group yourself
                if str(chat_user_id) == list_of_members[0].get('chat_user_id'):
                    return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.ROOM_CREATE_UNSUCCESSFULL,
                                        error_msg=ErrMsg.PROVIDE_CONTACT_CHAT_USER_ID,
                                        message_code=ErrMsgCode.PAYLOAD_INCORRECT
                                        )
                serializer_chat = RoomSerializer(data = individual_data)
                if serializer_chat.is_valid():
                    if created_room == 0: 
                        flag = 1
                        # print("ff")
                        serializer_chat.save()
                        serialized_chat_data = serializer_chat.data
                else:
                    print(serializer_chat.errors)
                    return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.INDIVIDUAL_ROOM_NOT_CREATED,
                                        # message='ssfs',
                                        error_msg= serializer_error_format(serializer_chat.errors), 
                                        message_code= ErrMsgCode.VALIDATION_ERROR
                                        )
            else:
                if len(list_of_members)<1:
                    return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.WRONG_LENGTH_OF_LIST_OF_MEMBERS,
                                        error_msg=  ErrMsg.WRONG_LENGTH_OF_LIST_OF_MEMBERS,
                                        message_code=  ErrMsgCode.PAYLOAD_INCORRECT
                                        )
                #creating room -------> if room type is group so use group data

                #group
                serializer_chat = RoomSerializer(data = group_data)
                if serializer_chat.is_valid():
                    flag = 1
                    serializer_chat.save()
                    serialized_chat_data = serializer_chat.data
                else:
                    return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.ROOM_CREATE_UNSUCCESSFULL,
                                    error_msg= serializer_error_format(serializer_chat.errors),
                                    message_code= ErrMsgCode.VALIDATION_ERROR
                                    )
            if flag:
                if created_room == 1:
                    existed_room = str(results[0])
                room_id = serialized_chat_data.get('room_id')
            else:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.ROOM_CREATE_UNSUCCESSFULL,
                                    # message= 'sfsf',
                                    error_msg= serializer_error_format(serializer_chat.errors),
                                    message_code= ErrMsgCode.VALIDATION_ERROR
                                    )
            
            #this for adding members in group members table if room type ---------> individual
            if room_type == ROOM_TYPE.INDIVIDUAL:
                # print(chat_user_id)
                serializer = GroupMembersSerializer(data = [{'room_id':room_id, 
                                                            'chat_user_id': chat_user_id, 
                                                            'is_admin': IS_ADMIN.TRUE, 
                                                           
                                                            },

                                                            {'room_id':room_id,
                                                            'chat_user_id': list_of_members[0].get('chat_user_id'), 
                                                            'is_admin':IS_ADMIN.TRUE,
                                                           }
                                                            ], many= True)
                #if room already exists then checked and return the response no need to check for room_id and all
                if created_room == 1:
                    existed_room = str(results[0])
                    # logger_info.info('chat-room  -----get api')
                    return json_response(success=True,
                                            status_code=status.HTTP_200_OK,
                                            message=Constants.ROOM_FETCH,
                                            result = {
                                            'room_id': existed_room,
                                            'room_type': ROOM_TYPE.INDIVIDUAL,
                                            'chat_user_id':friend_user_mapping_obj.chat_user_id,
                                            'profile_picture': friend_user_mapping_obj.app_user_id.profile_picture,
                                            'phone_number':contactlist_obj.phone_number,
                                            'contact_name': contactlist_obj.contact_name,
                                            'status_quotes':userstatus_obj.status_quotes
                                            })
                if serializer.is_valid():
                   
                    serializer.save()
                    # logger_info.info('chat-room  -----get api')
                    return json_response(success=True, 
                                        status_code=status.HTTP_200_OK,
                                        message= Constants.ROOM_CREATE,
                                        # result=serialized_chat_data
                                        result={'room_id': room_id,
                                                'room_type': ROOM_TYPE.INDIVIDUAL,
                                                'chat_user_id':friend_user_mapping_obj.chat_user_id,
                                                'profile_picture': friend_user_mapping_obj.app_user_id.profile_picture,
                                                'phone_number':contactlist_obj.phone_number,
                                                'contact_name': contactlist_obj.contact_name,
                                                'status_quotes':userstatus_obj.status_quotes
                                            }
                                        )
                    
                
                else: 
                    return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
                                   error_msg=serializer_error_list(serializer.errors) ,
                                    message_code=ErrMsgCode.VALIDATION_ERROR
                                    )
                
            # if  room_type is -->group then adding members in groupmember table
            data_create = []
            member_data = {
                    "room_id": room_id,
                    "chat_user_id": chat_user_id,
                    "is_admin": IS_ADMIN.TRUE,
                   
            }
            data_create.append(member_data)
            for member in list_of_members:
                member_data = {
                    "room_id": room_id,
                    "chat_user_id": member.get('chat_user_id'),
                }
                data_create.append(member_data)
            serializer_room = GroupMembersSerializer(data = data_create, many=True)
            if serializer_room.is_valid():
                # print("room_cr")
                serializer_room.save()
            else:
                print(serializer_room.errors)
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
                                    error_msg=serializer_error_list(serializer_room.errors) ,
                                    message_code=ErrMsgCode.VALIDATION_ERROR
                                    )
            # logger_info.info('chat-room  -----get api')
            print(serialized_chat_data.get('is_archived',None))
            return json_response(success=True, 
                                        status_code=status.HTTP_200_OK,
                                        message=Constants.ROOM_CREATE,
                                        result ={'room_id': room_id,
                                                 'room_type': ROOM_TYPE.GROUP,
                                                 'group_name':group_data['group_name'],
                                                 'group_picture': group_data['group_picture'],
                                                  'is_archived': serialized_chat_data.get('is_archived',None)
                                                }
                                        )

        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg=str(err))   
        
class GiveAdminRights(APIView):
    '''
    api to make admin a user in a room
    '''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def patch(self, request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            user_obj = request.user
            # member_id = chat_user_id
            #getting app_user_id from using token user_id
            # usermapping_obj = None
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            chat_user_id = usermapping_obj.chat_user_id
            payload = request.data
            room_id = payload.get('room_id', None)
            member_id = payload.get('chat_user_id',None)
            
            if room_id is None or member_id is None:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.PAYLOAD_INCORRECT,
                                    error_msg= ErrMsg.ROOM_ID_MEMBER_ID_MISSING,
                                    message_code= ErrMsgCode.PAYLOAD_INCORRECT)
            
            if str(chat_user_id) == str(member_id):#without str it gives false 
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.CANT_MAKE_YOURSELF_ADMIN,
                                    error_msg= ErrMsg.CANT_MAKE_YOURSELF_ADMIN,
                                    message_code= ErrMsgCode.FORBIDDEN
                                    )
            # token_group_member_obj = None
            try:
                token_group_member_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = usermapping_obj, removed_by = None)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.USER_NOT_MEMBER_OF_THIS_GROUP,
                                    error_msg= ErrMsg.USER_NOT_MEMBER_OF_THIS_GROUP,
                                    message_code=ErrMsgCode.USER_NOT_MEMBER_OF_THIS_GROUP
                                    )
            if token_group_member_obj.is_admin == IS_ADMIN.FALSE:
                return error_response(success=False,
                                     status_code = status.HTTP_400_BAD_REQUEST,
                                     message=Constants.NOT_ADMIN,
                                     error_msg=ErrMsg.NOT_ADMIN,
                                     message_code=ErrMsgCode.NOT_ADMIN)
            
            # groupmember_obj = None
            #checking that given member is present in the group or not
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = member_id, removed_by = None)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                     status_code= status.HTTP_400_BAD_REQUEST,
                                     message= Constants.MEMBER_NOT_FOUND,
                                     message_code= ErrMsgCode.MEMBER_NOT_FOUND,
                                     error_msg= ErrMsg.MEMBER_NOT_FOUND
                                     )
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
            if groupmember_obj.is_admin == IS_ADMIN.TRUE:
                return error_response(success=False,
                                status_code=status.HTTP_400_BAD_REQUEST,
                                message= Constants.ALREADY_ADMIN,
                                error_msg= ErrMsg.ALREADY_ADMIN,
                                message_code=ErrMsgCode.ALREADY_ADMIN
                                )
            groupmember_obj.is_admin = IS_ADMIN.TRUE
            groupmember_obj.save()
            logger_info.info('admin      ---patch api')
            return json_response(success=True,
                                status_code=status.HTTP_200_OK,
                                message=Constants.UPDATED_AS_ADMIN
                                )
        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg=str(err))   
        

class RemoveMember(APIView):
    '''
    api to remove member from the group only if user is admin in that group
    '''
    permission_classes = [ ApiKey, IsAuthenticated]
    def patch(self,request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            # user_obj = request.user
            payload = request.data
            # member_id = chat_user_id
            # usermapping_obj = None
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            chat_user_id = usermapping_obj.chat_user_id
            room_id = payload.get('room_id', None)
            member_id = payload.get('chat_user_id', None)

            if room_id is None or member_id is None:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.PAYLOAD_INCORRECT,
                                    error_msg= ErrMsg.ROOM_ID_MEMBER_ID_MISSING,
                                    message_code= ErrMsgCode.PAYLOAD_INCORRECT)
            
            # groupmember_obj = None# this represents to whom we want to remove
            #checking for member existence /soft delete
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = member_id, removed_by = None)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                    status_code= status.HTTP_400_BAD_REQUEST,
                                     message= Constants.MEMBER_NOT_FOUND,
                                     message_code= ErrMsgCode.MEMBER_NOT_FOUND,
                                     error_msg= ErrMsg.MEMBER_NOT_FOUND
                                    )
            # -----------------------
            if(str(chat_user_id) == str(member_id)):
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.CANT_REMOVE_YOURSELF,
                                    message_code=ErrMsgCode.CANT_REMOVE_YOURSELF,
                                    error_msg=ErrMsg.CANT_REMOVE_YOURSELF)
            #if token_user is himself admin or not check other wise can remove other 
            # token_group_member_obj = None
            try:
                token_group_member_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = usermapping_obj, removed_by = None)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                     status_code=status.HTTP_400_BAD_REQUEST,
                                     message= Constants.USER_NOT_MEMBER_OF_THIS_GROUP,
                                     error_msg=ErrMsg.USER_NOT_MEMBER_OF_THIS_GROUP,
                                     message_code=ErrMsgCode.USER_NOT_MEMBER_OF_THIS_GROUP)
            
            if token_group_member_obj.is_admin == IS_ADMIN.FALSE:
                return error_response(success=False,
                                     status_code = status.HTTP_400_BAD_REQUEST,
                                     message=Constants.NOT_ADMIN,
                                     error_msg=ErrMsg.NOT_ADMIN,
                                     message_code=ErrMsgCode.NOT_ADMIN)
            #if member is admin you cant remove another admin from the group
            # if groupmember_obj.is_admin == IS_ADMIN.TRUE:
            #     return error_response(success=False,
            #                          status_code = status.HTTP_400_BAD_REQUEST,
            #                          message=Constants.UNABLE_TO_REMOVE_MEMBER,
            #                          error_msg=ErrMsg.CANT_REMOVE_ANOTHER_ADMIN,
            #                          message_code=ErrMsgCode.FORBIDDEN)
            # #makin the soft delete and filling the date_time result

            # groupmember_obj.is_deleted = "on"
            groupmember_obj.deleted_at = datetime.datetime.now()
            groupmember_obj.removed_by = usermapping_obj
            groupmember_obj.is_admin = IS_ADMIN.FALSE
            groupmember_obj.save()
            # logger_info.info('remove  --- patch api')
            return json_response(success=True,
                                status_code= status.HTTP_200_OK,
                                message= Constants.MEMBER_REMOVED_SUCCESSFULLY)
        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg=str(err))  
        
class LeaveGroup(APIView):
    '''api if user left the group'''
    permission_classes = [ ApiKey, IsAuthenticated]
    def patch(self,request):
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            # user_obj = request.user
            payload = request.data
            # usermapping_obj = None
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            chat_user_id = usermapping_obj.chat_user_id
            room_id = payload.get('room_id',None)
            if room_id is None:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.PAYLOAD_INCORRECT,
                                    error_msg= ErrMsg.PAYLOAD_INCORRECT,
                                    message_code= ErrMsgCode.PAYLOAD_INCORRECT)
            
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = chat_user_id, removed_by = None)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                     status_code=status.HTTP_400_BAD_REQUEST,
                                     message= Constants.YOU_ARE_NOT_PRESENT_IN_THE_GROUP,
                                     error_msg=ErrMsg.YOU_ARE_NOT_PRESENT_IN_THE_GROUP,
                                     message_code=ErrMsgCode.BAD_REQUEST)
            
            if groupmember_obj.is_admin == IS_ADMIN.TRUE:

                group_admin_objs = GroupMembers.objects.filter(room_id = room_id, is_admin = IS_ADMIN.TRUE, removed_by = None)
                group_admin_objs = group_admin_objs.exclude(chat_user_id = chat_user_id)
                # print(group_admin_objs)
                #checking is there any other admin in group or not if not
                # print(group_admin_objs)
                if len(group_admin_objs) == 0:
                    group_member_all_objs = GroupMembers.objects.filter(room_id = room_id, removed_by = None).order_by('created_at')
                    group_member_all_objs = group_member_all_objs.exclude(chat_user_id = chat_user_id)
                    print(group_member_all_objs)
                    #if one by one there is no member then we cant make anyone admin
                    if len(group_member_all_objs) > 0:
                        make_admin = group_member_all_objs[0]
                        make_admin.is_admin = IS_ADMIN.TRUE
                        make_admin.save()

            groupmember_obj.deleted_at = datetime.datetime.now()
            groupmember_obj.removed_by = usermapping_obj
            groupmember_obj.is_admin = IS_ADMIN.FALSE
            groupmember_obj.save()
            # logger_info.info('leave  ----patch api')
            return json_response(success=False,
                            status_code= status.HTTP_200_OK,
                            message= Constants.LEFT_SUCCESSFULLY)
        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg=str(err))   

class GroupMembersApi(APIView):
    
    permission_classes = [ ApiKey, IsAuthenticated]
    def get(self, request,room_id):
        '''API to collect all the members details present in a group'''
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            # payload = request.data
            # user_obj = request.user
            # usermapping_obj = None
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            chat_user_id = usermapping_obj.chat_user_id
            print('token',chat_user_id)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
            # room_id = payload.get('room_id', None)
            if room_id is None:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.CANT_FETECH_DETAILS,
                                    error_msg= ErrMsg.ROOM_ID_IS_MISSING,
                                    message_code= ErrMsgCode.PAYLOAD_INCORRECT)
            final_data = []
            # groupmember_obj = None
            try:
                groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = chat_user_id)
                # groupmember_obj = GroupMembers.objects.get(room_id = room_id)
            except GroupMembers.DoesNotExist:
                return error_response(success=False,
                                     status_code=status.HTTP_404_NOT_FOUND,
                                     message= Constants.USER_NOT_MEMBER_OF_THIS_GROUP,
                                     error_msg=ErrMsg.USER_NOT_MEMBER_OF_THIS_GROUP,
                                     message_code=ErrMsgCode.USER_NOT_MEMBER_OF_THIS_GROUP)
            
            member_objs =  GroupMembers.objects.filter(room_id = room_id, removed_by = None)
            paginator = Paginator(member_objs, limit)
            page_obj = paginator.get_page(page)
            serializer_groupmember  = GroupMembersgettingSerializer(page_obj, many = True)
            
            for index in range(len(serializer_groupmember.data)):
                # contact_obj = None
                # contact_name = None
                # contact_number = None
                # profile_picture = None
                # username = None
                friend_obj = member_objs[index].chat_user_id
                try:
                    contact_obj =  friend_obj.contactlist_contact_chat_user_id.get(chat_user_id = chat_user_id )
                    # print('ccxxxxxxxxxxccccccc',contact_obj.contact_name, contact_obj.phone_number)
                    contact_name = contact_obj.contact_name
                    contact_number = contact_obj.phone_number
                    username = friend_obj.app_user_id.username
                    profile_picture = friend_obj.app_user_id.profile_picture
                except:
                    # print('xxx')
                    contact_name = None
                    contact_number = friend_obj.app_user_id.phone_number
                    profile_picture = friend_obj.app_user_id.profile_picture
                    username = friend_obj.app_user_id.username
                    
                data = {
                    'chat_user_id':serializer_groupmember.data[index].get('chat_user_id',None),
                    # 'room_id': serializer_groupmember.data[index].get('room_id',None),
                    'is_admin':serializer_groupmember.data[index].get('is_admin',None),
                    'contact_name':contact_name,
                    'phone_number': contact_number,
                    'profile_picture': profile_picture,
                    'username': username
                }
                final_data.append(data)
            result_data = {
                'room_id': room_id,
                'members': final_data
            }
            # logger_info.info('members ----get api')
            return json_response(success=True,
                                 status_code=status.HTTP_200_OK,
                                 message=Constants.DETAILS,
                                #  result= serializer_groupmember.data,
                                result=result_data)
                                # )

        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg=str(err))   
        
    # def post(self, request):
    #     '''api to add signle member at a time in an existing group'''
    #     try:
    #         user_id = request.user.user_id  # Get the user_id from the authentication token
    #         payload = request.data
    #         # user_obj = request.user
    #         member_id = payload.get('chat_user_id', None)
    #         room_id = payload.get('room_id', None)
    #         # usermapping_obj = None
    #         try:
    #             usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
    #         except:
    #             return error_response(success=False,
    #                                   status_code=status.HTTP_400_BAD_REQUEST,
    #                                   error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
    #                                   message=Constants.USERMAPPING_NOT_FOUND,
    #                                   message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
    #                                   )
    #         # chat_user_id = usermapping_obj.chat_user_id

    #         # room_id = payload.get('room_id', None)
    #         if room_id is None or member_id is None:
    #             return error_response(success=False,
    #                                 status_code=status.HTTP_400_BAD_REQUEST,
    #                                 message= Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
    #                                 error_msg= ErrMsg.ROOM_ID_MEMBER_ID_MISSING,
    #                                 message_code= ErrMsgCode.PAYLOAD_INCORRECT)
            
    #         # token_group_member_obj = None
    #         try:
    #             token_group_member_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = usermapping_obj, removed_by = None)
    #         except GroupMembers.DoesNotExist:
    #             return error_response(success=False,
    #                                  status_code=status.HTTP_403_FORBIDDEN,
    #                                  message= Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
    #                                  error_msg=ErrMsg.YOU_ARE_NOT_PRESENT_IN_THE_GROUP,
    #                                  message_code=ErrMsgCode.FORBIDDEN)
            
    #         if token_group_member_obj.is_admin == "off":
    #             return error_response(success=False,
    #                                  status_code = status.HTTP_403_FORBIDDEN,
    #                                  message=Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
    #                                  error_msg=ErrMsg.YOU_ARE_NOT_ADMIN,
    #                                  message_code=ErrMsgCode.FORBIDDEN)
    #         # groupmember_obj = None# this represents to whom we want to add
    #         #checking for member existence /soft delete\
    #         serialized_data = None
    #         try:
    #             groupmember_obj = GroupMembers.objects.get(room_id = room_id, chat_user_id = member_id)
    #             #if member was previously present in the group then we just patch the details
    #             if groupmember_obj.removed_by != None  and groupmember_obj.deleted_at != None:
    #                 groupmember_obj.deleted_at = None
    #                 groupmember_obj.removed_by = None
    #                 groupmember_obj.save()

    #         except GroupMembers.DoesNotExist:
    #             dict = {
    #                 "room_id": room_id,
    #                 "chat_user_id": member_id
    #             }
    #             serializer_member = GroupMembersSerializer(data = dict)
                
    #             if serializer_member.is_valid():
    #                 # print("room_cr")
                    
    #                 serializer_member.save()
    #                 serialized_data = serializer_member.data
    #             else:
    #                 print(serializer_member.errors)
    #                 return error_response(success=False,
    #                                     status_code=status.HTTP_400_BAD_REQUEST,
    #                                     message = Constants.GROUP_MEMBERS_ADDITION_UNSUCCESSFULL,
    #                                     error_msg =serializer_error_format(serializer_member.errors),
    #                                     message_code =ErrMsgCode.VALIDATION_ERROR
    #                                     )
    #         # logger_info.info('members  ------post api')
    #         return json_response(success=True,
    #                              status_code=status.HTTP_201_CREATED,
    #                              message = Constants.SUCCESSFULL,
    #                              result=serialized_data)
                
    #     except Exception as err:
    #         logger_error.error('members     ----post api')
    #         print("----------------------------------------------------")
    #         traceback.print_exc()
    #         print("----------------------------------------------------")
        
    #         return error_response(success = False,
    #                                 status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                                 message = Constants.INTERNAL_SERVER_ERROR,
    #                                 message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
    #                                 error_msg=str(err))