from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UsersMapping, Session, ContactList, Privacy,  GroupMembers, Room , Messages,MessageHistory# Chats, Messages,
from .serializers import  UserSerializer,ContactListSerializer,RoomSerializer,UserProfileSerializer, ContactListSyncSerializer,GroupMembersSerializer,GroupMembersgettingSerializer ,MessageSerializer,MessageHistorySerializer
import json
from rest_framework import status
from utils.helpers import json_response, error_response, search_list_of_dicts,get_tokens_for_user, serializer_error_format,serializer_error_list, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization

from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
import datetime
from common.constants import Constants, ErrMsg, ErrMsgCode, ROOM_TYPE,IS_ADMIN
from django.core.paginator import Paginator
import traceback
import re
from uuid import UUID
from datetime import datetime, timezone
import logging
logger_error = logging.getLogger('error_logger')
logger_info = logging.getLogger('info_logger')

class MessageHistoryApis(APIView):
    '''API for related to message table'''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def get(self,request):
        '''API to fetch the data from  the messsage table'''
        try:
          
            user_obj = request.user
            room_id = request.GET.get('room_id',None)
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            # print(usermapping_obj)
            token_chat_user_id = usermapping_obj.chat_user_id
            # print(token_chat_user_id)
            if room_id is None:
                return error_response(
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message= Constants.PAYLOAD_INCORRECT,
                    error_msg=ErrMsg.ROOM_ID_IS_MISSING,
                    message_code=ErrMsgCode.VALIDATION_ERROR
                )
            page = request.GET.get('page',1)
            limit = request.GET.get('limit',10)
            messages = Messages.objects.filter(room_id = room_id)
            
            paginator = Paginator(messages, limit)
            page_obj = paginator.get_page(page)
            final_data = []
            serializer = MessageSerializer(page_obj, many = True)
            # print(serializer.data)
            
            try:
                room_obj = Room.objects.get(room_id = room_id)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      message=Constants.ROOM_NOT_FOUND,
                                      error_msg=ErrMsg.ROOM_NOT_FOUND,
                                      message_code=ErrMsgCode.ROOM_NOT_FOUND)
            # print(room_obj.room_type)
            for index in range(len(serializer.data)):
                
                sender_chat_user_id = page_obj[index].sender_chat_user_id #obj
                # print(serializer.data[index].get('sender_chat_user_id'),sender_chat_user_id)
                room_obj = page_obj[index].room_id
                group_members_list_except_sender = room_obj.group_member.all().exclude(chat_user_id = sender_chat_user_id)
                
                message_id = page_obj[index].message_id
                # print('message_id',message_id)

                #list of users to whom message is delivered
                delivered_to_users = room_obj.from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None)
                 #list of users who read the message
                # read_by_users = room_obj.from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None).exclude(read_by_chat_user_id = None)
                read_by_users = delivered_to_users.exclude(read_by_chat_user_id = None)
                message_status = 'sent'
                if (len(group_members_list_except_sender) == len(delivered_to_users)):
                    message_status = 'delivered'
                if (len(group_members_list_except_sender) == len(read_by_users)):
                    message_status = 'read'
               
                data = {
                    'room_id': serializer.data[index].get('room_id',None),
                    'sender_chat_user_id': serializer.data[index].get('sender_chat_user_id',None),
                    'message_id': serializer.data[index].get('message_id',None),
                    'message_type': serializer.data[index].get('message_type',None),
                    'message_content': serializer.data[index].get('message_content', None),
                    'created_at': serializer.data[index].get('created_at',None),
                    'message_status': message_status
                    # 'profile_picture':mes
                }
                # contact_name = None
                # contact_number = None
                try:
                    contact_details = sender_chat_user_id.contactlist_contact_chat_user_id.get(chat_user_id=token_chat_user_id)
                    contact_name = contact_details.contact_name
                    contact_number = contact_details.phone_number
                except:
                    contact_name = None
                    contact_number = sender_chat_user_id.app_user_id.phone_number
                if(room_obj.room_type == ROOM_TYPE.GROUP):
                    #adding the details of room in which the message is present
                    data['room_type'] = ROOM_TYPE.GROUP
                    data['group_picture'] = room_obj.group_picture
                    data['group_name'] = room_obj.group_name
                    data['username'] = sender_chat_user_id.app_user_id.username
                    data['contact_name'] = contact_name
                    data['phone_number'] = contact_number
                    data['profile_picture'] =  sender_chat_user_id.app_user_id.profile_picture
                else:
                    
                    data['room_type'] = ROOM_TYPE.INDIVIDUAL
                    data['group_picture'] = None
                    data['group_name'] = None
                    data['username'] = sender_chat_user_id.app_user_id.username
                    data['contact_name'] = contact_name
                    data['phone_number'] = contact_number
                    data['profile_picture'] =  sender_chat_user_id.app_user_id.profile_picture
                
                final_data.append(data)
            return json_response(message=Constants.DETAILS,
                                 status_code= status.HTTP_200_OK,
                                 result= final_data
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
        
    
# class RecentChats(APIView):
#     '''API for recent chats '''
#     permission_classes = [ ApiKey, IsAuthenticated ]
#     def get(self, request):
#         '''This api will give the details of recent chats that ser'''
#         try:
#             user_obj = request.user
#             limit = request.GET.get('limit',100)
#             page = request.GET.get('page',1)
#             search = request.GET.get('search',None)
#             limit = int(limit)
#             page = int(page)

#             try:
#                 usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
#             except:
#                 return error_response(success=False,
#                                       status_code=status.HTTP_400_BAD_REQUEST,
#                                       error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
#                                       message=Constants.USERMAPPING_NOT_FOUND,
#                                       message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
#                                       )
#             # print(usermapping_obj)
#             chat_user_id = usermapping_obj.chat_user_id#obj of token from usermapping table

#             #related name (group_member)to handle the reverse lookup scenarios
#             #find all the rooms in which the token person is present
#             rooms = Room.objects.filter(group_member__chat_user_id=usermapping_obj).order_by('created_at')
            
#             # response_data = []
#             #list of group memebers that are present in the rooms of above room_list
#             group_members = GroupMembers.objects.filter(room_id__in = rooms).exclude(chat_user_id = usermapping_obj).select_related('chat_user_id__app_user_id')
#             # print(len(group_members))
#             # print("members_Data" ,group_members[0].group_name)
#             # final_data = []
#             final_data_with_msg = []
#             final_data_without_msg = []
#             complete_room = []
#             for index in range(len(rooms)):
#                 for member in group_members:
#                     # print(rooms[index], member.room_id,rooms[index] == member.room_id )
#                     #multiple members in group same room_id remove duplicacy
#                     if(rooms[index] == member.room_id):
#                         if rooms[index] in complete_room:
#                             continue
#                         else:
#                             complete_room.append(rooms[index])
#                         # print('memberchatuser-------',member.chat_user_id)
#                         #reverse lookup using the related name in models of messages
#                         messages_details = rooms[index].room_messages.all().order_by('-created_at').first()
#                         # message_id  = None
#                         if(messages_details):
#                             message_id = messages_details.message_id
#                         # print('mesafe id',message_id)
                
#                         #reverse lookup using the related_name in models of contactlist
#                         #member.chat_user_id gives the contact_chat_user_id
                        
#                         # print('contact_details',contact_details)
#                         # print('contenct-=======',contact_details.contact_name)
#                         # print('message details -----------------',messages_details)
#                         data_room = {
#                             "room_id": rooms[index].room_id,
#                             "group_name": rooms[index].group_name,
#                             "group_picture": rooms[index].group_picture,
#                             "room_type":rooms[index].room_type, 
#                         }
#                         message_his_obj_read = rooms[index].from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None).exclude(read_by_chat_user_id = None)
#                         message_his_obj_delivered = rooms[index].from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None)
                        
#                         # message_his_obj = MessageHistory.objects.filter(room_id = rooms[index].room_id, message_id= message_id).exclude(read_by_chat_user_id = None)
#                         number_of_members_in_room = len(group_members.filter(room_id = rooms[index].room_id))
                        
#                         message_status = 'sent'
#                         if(len(message_his_obj_delivered) == number_of_members_in_room):
#                             # if(messages_details):
#                             #     print('cc', len(message_his_obj_delivered))
#                             message_status = 'delivered'
#                         if(len(message_his_obj_read) == number_of_members_in_room):
#                             # if(messages_details):
#                             #     print(messages_details.message_id,message_his_obj_read[0].read_by_chat_user_id)
#                             #     print('cc', len(message_his_obj_read))
#                             message_status = 'read'
#                         # print(message_status)
#                         #concept of count of unread messages
#                         unread_msgs = rooms[index].from_room.filter(room_id = rooms[index], delivered_to_chat_user_id = chat_user_id, read_by_chat_user_id = None)
#                         count = str(len(unread_msgs))
#                         # print(type(count))
#                         #if there is any message in the room then add the message type and message content
#                         if(messages_details):
#                             # print('mesg deta',type(messages_details))
#                             data_msg = {
#                             "message_id": messages_details.message_id,
#                             "message_type":  messages_details.message_type,
#                             "message_content":messages_details.message_content or None,
#                             "message_time": messages_details.created_at,
#                             "updated_at":messages_details.updated_at,
#                             "deleted_for":messages_details.deleted_for,
#                             "message_file_path": messages_details.file_path,
#                             "message_thumbnail_file_path":messages_details.thumbnail_file_path,
#                             "message_status": message_status,
#                             "unread_messages":count
#                             }
#                             data_room.update(data_msg)
#                         else:
#                             if(rooms[index].room_type == ROOM_TYPE.INDIVIDUAL):
#                                 continue
#                             data_msg = {
#                             "message_id": None,
#                             "message_type":  None,
#                             "message_content": None,
#                             "message_time":None,
#                             "updated_at": None,
#                             "deleted_for":None,
#                             "message_file_path": None,
#                             "message_thumbnail_file_path":None,
#                             "message_status": message_status,
#                             "unread_messages": count
#                             }
#                             data_room.update(data_msg)

#                         #if room_type is individual then we need to give contacted person username,profile_pic
#                         if rooms[index].room_type == ROOM_TYPE.INDIVIDUAL:
#                             try:
#                                 contact_details = member.chat_user_id.contactlist_contact_chat_user_id.get(chat_user_id=chat_user_id)
#                                 contact_name = contact_details.contact_name
#                                 contact_number = contact_details.phone_number
#                             except:
#                                 contact_number = member.chat_user_id.app_user_id.phone_number
#                                 contact_name = None
                                
#                             data_user = {
#                             "username":member.chat_user_id.app_user_id.username,
#                             "profile_picture": member.chat_user_id.app_user_id.profile_picture,
#                             "contact_name": contact_name,
#                             "phone_number": contact_number,
#                             }
#                             data_room.update(data_user)
#                         else:
#                             data_user = {
#                             "username":None,
#                             "profile_picture": None,
#                             "contact_name": None,
#                             "phone_number": None,
#                             }
#                             # print(data_room)
#                             data_room.update(data_user)
#                         if(messages_details):
#                             final_data_with_msg.append(data_room)
#                         else:
#                             final_data_without_msg.append(data_room)
#                         # final_data.append(data_room)
            
#             # Sort the list of dict based on the message_time 
#             result_data = sorted(final_data_with_msg, key=lambda x: x.get('message_time', datetime.min), reverse=True)
#             result_data = result_data + final_data_without_msg
#             search_keys = ["group_name", "contact_name", "username","phone_number"]
#             if search:
#                 result_data = search_list_of_dicts(result_data, search, search_keys)
#             # print('len',len(result_data),len(final_data))
#             result_data = result_data[limit*(page-1): limit*(page-1) + limit]
#             # print('len', len(result_data))
#             return json_response( result= result_data,status_code=status.HTTP_200_OK, message=Constants.DETAILS)
#         except Exception as err:
#             logger_error.error(err, exc_info=True)
#             print("----------------------------------------------------")
#             traceback.print_exc()
#             print("----------------------------------------------------")
        
#             return error_response(success = False,
#                                     status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
#                                     message = Constants.INTERNAL_SERVER_ERROR,
#                                     message_code= ErrMsgCode.INTERNAL_SERVER_ERROR,
#                                     error_msg=str(err)) 

#---------------------MessageInfo api-------------------------------------------

class MessageInfo(APIView):
    permission_classes = [ ApiKey, IsAuthenticated ]
    def get(self, request):
        '''API to get the info of messages that has been read by peoples'''
        try:
            user_obj = request.user
            # room_id = payload.get('room_id',None)
            message_id = request.GET.get('message_id',None)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            token_chat_user_id = usermapping_obj.chat_user_id
            messages_obj = MessageHistory.objects.filter(message_id = message_id).exclude(read_by_chat_user_id = None)
            paginator = Paginator(messages_obj, limit)
            page_obj = paginator.get_page(page)
            serializer_messagehistory = MessageHistorySerializer(page_obj,many = True)
            final_data = []
            serializer_data = serializer_messagehistory.data
            print('token_chat_user_id',token_chat_user_id)
            for index in range(len(serializer_data)):
                read_by_obj = messages_obj[index].read_by_chat_user_id
                # print('read_by_obj',read_by_obj, type(read_by_obj) )
                # contact_obj = None
               
                
                try:
                    contact_obj = read_by_obj.contactlist_contact_chat_user_id.get(chat_user_id = token_chat_user_id)
                    # print('contact_obj', contact_obj)
                    contact_name = contact_obj.contact_name
                    contact_number = contact_obj.phone_number
                    profile_picture = read_by_obj.app_user_id.profile_picture
                    username = read_by_obj.app_user_id.username
                except:
                    contact_number = read_by_obj.app_user_id.phone_number
                    contact_name = None
                    profile_picture = read_by_obj.app_user_id.profile_picture
                    username = read_by_obj.app_user_id.username
                    
                data_msg = {
                    "message_id": serializer_data[index].get('message_id',None),
                    "read_by_chat_user_id": serializer_data[index].get('read_by_chat_user_id',None),
                    "message_status": "read",
                    "delivered_to_chat_user_id": serializer_data[index].get('delivered_to_chat_user_id',None),
                    "username": username,
                    "contact_name": contact_name,
                    "phone_number": contact_number,
                    "profile_picture": profile_picture
                    
                }
                final_data.append(data_msg)
            # logger_info.info('message info -----get api')
            return json_response(success=True,
                                 status_code=status.HTTP_200_OK,
                                 message=Constants.DETAILS,
                                 result= final_data)
            
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

#---------------------------new recent chats api -----------------------------------------

class RecentChatsNew(APIView):
    '''API for recent chats '''
    permission_classes = [ ApiKey, IsAuthenticated ]
    def get(self, request):
        '''This api will give the details of recent chats that ser'''
        try:
            user_obj = request.user
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
            search = request.GET.get('search',None)
            limit = int(limit)
            page = int(page)

            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            except:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                      message=Constants.USERMAPPING_NOT_FOUND,
                                      message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                      )
            # print(usermapping_obj)
            chat_user_id = usermapping_obj.chat_user_id#obj of token from usermapping table

            #related name (group_member)to handle the reverse lookup scenarios
            #find all the rooms in which the token person is present
            rooms = Room.objects.filter(group_member__chat_user_id=usermapping_obj).order_by('created_at')
            
            # response_data = []
            #list of group memebers that are present in the rooms of above room_list
            group_members = GroupMembers.objects.filter(room_id__in = rooms).exclude(chat_user_id = usermapping_obj).select_related('chat_user_id__app_user_id')
        
            final_data_with_msg = []
            final_data_without_msg = []
            # final_data = []
            for index in range(len(rooms)):
                # print(rooms[index].room_type)
                
                messages_details = rooms[index].room_messages.all().first()
                message_id  = None
                # print('message_details',messages_details)
                if(messages_details):
                    # print('sss')
                    message_id = messages_details.message_id
                # print('message_id',message_id)
                data_room = {
                    "room_id": rooms[index].room_id,
                    "group_name": rooms[index].group_name,
                    "group_picture": rooms[index].group_picture,
                    "room_type":rooms[index].room_type, 
                }
                # message_his_obj_read = rooms[index].from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None).exclude(read_by_chat_user_id = None)
                message_his_obj_delivered = rooms[index].from_room.filter(message_id = message_id).exclude(delivered_to_chat_user_id = None)
                message_his_obj_read = message_his_obj_delivered.exclude(read_by_chat_user_id = None)
                # message_his_obj = MessageHistory.objects.filter(room_id = rooms[index].room_id, message_id= message_id).exclude(read_by_chat_user_id = None)
                number_of_members_in_room = len(group_members.filter(room_id = rooms[index].room_id))
                
                message_status = 'sent'
                if(len(message_his_obj_delivered) == number_of_members_in_room):
                    message_status = 'delivered'
                if(len(message_his_obj_read) == number_of_members_in_room):
                    message_status = 'read'
                
                unread_msgs = rooms[index].from_room.filter(room_id = rooms[index], delivered_to_chat_user_id = chat_user_id, read_by_chat_user_id = None)
                count = str(len(unread_msgs))
                
                #if there is any message in the room then add the message type and message content
                if(messages_details):
                    # print('mesg deta',type(messages_details))
                    data_msg = {
                    "message_id": messages_details.message_id,
                    "message_type":  messages_details.message_type,
                    "message_content":messages_details.message_content or None,
                    "message_time": messages_details.created_at,
                    "updated_at":messages_details.updated_at,
                    "deleted_for":messages_details.deleted_for,
                    "message_file_path": messages_details.file_path,
                    "message_thumbnail_file_path":messages_details.thumbnail_file_path,
                    "message_status": message_status,
                    "unread_messages":count
                    }
                    data_room.update(data_msg)
                else:
                    if(rooms[index].room_type == ROOM_TYPE.INDIVIDUAL):
                        continue
                    data_msg = {
                    "message_id": None,
                    "message_type":  None,
                    "message_content": None,
                    "message_time":None,
                    "updated_at": None,
                    "deleted_for":None,
                    "message_file_path": None,
                    "message_thumbnail_file_path":None,
                    "message_status": message_status,
                    "unread_messages": count
                    }
                    data_room.update(data_msg)

                if rooms[index].room_type == ROOM_TYPE.INDIVIDUAL:
                    try:
                        group_member_obj  = rooms[index].group_member.exclude(chat_user_id = chat_user_id).first()
                        # print('group_member obj', group_member_obj)
                        member_obj = group_member_obj.chat_user_id
                    except:
                        return error_response(success=False,
                                              status_code=status.HTTP_400_BAD_REQUEST,
                                              message=Constants.MEMBER_NOT_FOUND,
                                              message_code=ErrMsgCode.MEMBER_NOT_FOUND,
                                              error_msg=ErrMsg.MEMBER_NOT_FOUND
                        )
                    try: 
                        print('member_obj',member_obj)
                        contact_details = member_obj.contactlist_contact_chat_user_id.get(chat_user_id=chat_user_id)
                        contact_name = contact_details.contact_name
                        contact_number = contact_details.phone_number
                        username = member_obj.app_user_id.phone_number
                        profile_picture = member_obj.app_user_id.profile_picture
                    except:
                        contact_number = member_obj.app_user_id.phone_number
                        username = member_obj.app_user_id.phone_number
                        contact_name = None
                        profile_picture = member_obj.app_user_id.profile_picture
                    data_user = {
                    "username": username,
                    "profile_picture": profile_picture,
                    "contact_name": contact_name,
                    "phone_number": contact_number,
                    }
                    data_room.update(data_user)
                else:
                    data_user = {
                    "username":None,
                    "profile_picture": None,
                    "contact_name": None,
                    "phone_number": None,
                    }
                    data_room.update(data_user)
                if(messages_details):
                    final_data_with_msg.append(data_room)
                else:
                    final_data_without_msg.append(data_room)
                # final_data.append(data_room)
            
            # Sort the list of dict based on the message_time 
            result_data = sorted(final_data_with_msg, key=lambda x: x.get('message_time', datetime.min), reverse=True)
            result_data = result_data + final_data_without_msg
            search_keys = ["group_name", "contact_name", "username","phone_number"]
            if search:
                result_data = search_list_of_dicts(result_data, search, search_keys)
            # print('len',len(result_data),len(final_data))
            result_data = result_data[limit*(page-1): limit*(page-1) + limit]
            # print('len', len(result_data))
            return json_response( result= result_data,status_code=status.HTTP_200_OK, message=Constants.DETAILS)
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