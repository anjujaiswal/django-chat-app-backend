from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UsersMapping, Session, ContactList, Privacy,BlockList,UserStatus
from .serializers import UserSerializer, UsersMappingSerializer, RegisterSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, BlockListSerializer, ContactListSyncSerializer,BlockingSerializer
from .serializers import GetContactListSerialzier
import json
from rest_framework import status
from utils.helpers import json_response,error_response, get_tokens_for_user, get_user_id_from_tokens, ApiKey, serializer_error_format, api_key_authorization,token_authorization, serializer_error_list

from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.paginator import Paginator

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
from django.db.models import Q
from common.constants import Constants ,ErrMsgCode, ErrMsg
import re
import traceback
import logging
from uuid import UUID
logger_error = logging.getLogger('error_logger')
logger_info = logging.getLogger('info_logger')

class Contacts(APIView):
    '''Contact getting and syncing apis'''
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        '''
        api to give details of the contactlist of the user
        '''
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
            user_status_objs_all = UserStatus.objects.all()
           
            user_status_quotes = []
            user_status_chat_user_id = []
            for user_status_obj in user_status_objs_all:
                user_status_quotes.append(user_status_obj.status_quotes)
                user_status_chat_user_id.append(str(user_status_obj.chat_user_id))

            ##need to do this to get only uuid string instead of complete object for further comparison
            user_status_chat_user_id = [re.search(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-\b[a-f0-9]{12}', item).group() for item in user_status_chat_user_id]
            #converted to <class 'uuid.UUID'>
            user_status_chat_user_id  =  [UUID(string) for string in user_status_chat_user_id]
            # print(user_status_chat_user_id)
            # chat_user_id = usermapping_obj.chat_user_id
            
            search = request.GET.get('search',None)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
            
            contact_objs = ContactList.objects.filter(chat_user_id = usermapping_obj)

            if search:
                contact_objs = contact_objs.filter(
                    Q(phone_number__icontains=search) |
                    Q(contact_name__icontains=search)
                )
            paginator = Paginator(contact_objs, limit)
            page_obj = paginator.get_page(page)
            final_data = []
            serializer = GetContactListSerialzier(page_obj, many=True)
            #here flag represents if the contact person is a whatsapp user then it must have userstatus row in the table
            #when we matched that row we update it to 1
            # flag = 0
            for index in range(len(serializer.data)):
                flag = 0
                for another_index in range(len(user_status_chat_user_id)):
                    if serializer.data[index]['contact_chat_user_id'] == user_status_chat_user_id[another_index]:
                        data = {}
                        serializer_dict = serializer.data[index]
                        status_dict = {'status_quotes': user_status_quotes[another_index]}
                        data.update(serializer_dict)
                        data.update(status_dict)
                        flag = 1
                        final_data.append(data)
                if flag == 0:
                    final_data.append(serializer.data[index])
                    
            # logger_info.info('contacts ---get api')
            
            return json_response(result= final_data,message=Constants.DETAILS)


        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )

    def post(self, request):
        '''
        Api for contactSync if given phonenumber exists then save contact_chat_user_id foreign key 
        otherwise store null
        '''
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            data = request.data
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
            contact_data = data.get('contacts',[])
            user_objs_all = User.objects.all()
            # usermapping_objs_all = UsersMapping.objects.all()
            user_phone_all = []
            # app_user_id_all = []
            # chat_user_id_all = []
            contact_phone_number_already_presents = []
            prev_objs = []
            user_contact_objs = ContactList.objects.filter(chat_user_id = usermapping_obj)

            #collecting the records of contacts phone number that already presents of the user

            for index in range(len(user_contact_objs)):
                prev_objs.append(user_contact_objs[index])
                contact_phone_number_already_presents.append(user_contact_objs[index].phone_number)

            #collecting all phonenumber records 
            for index in range(len(user_objs_all)):
                # if user_objs_all[index].phone_number == user.phone_number:
                #     continue
                user_phone_all.append(user_objs_all[index].phone_number)
                # app_user_id_all.append(user_objs_all[index].user_id)
                # print(type(user_objs_all[index].user_id)==type(usermapping_objs_all[index].app_user_id.user_id))
                # chat_user_id_all.append(usermapping_objs_all[index].chat_user_id)

            # print(app_user_id_all)
            # app_user_id_all = [str(uuid) for uuid in app_user_id_all]
            # chat_user_id_all = [str(uuid) for uuid in chat_user_id_all]

            # print(chat_user_id_all)
            serializer_list_dict = []
            create_phone_number = []

            #traversing the list of contact_data of payload
            for item in contact_data:
                phone_number = item.get('phone_number',None)
                contact_name = item. get('contact_name', None)
                if  contact_name is None or phone_number is None:
                    return error_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = Constants.NOT_SYNC,
                                    error_msg= ErrMsg.CONTACT_NAME_OR_NUMBER_MISSING,
                                    message_code=ErrMsgCode.PAYLOAD_MISSING
                                    )

                # flag var is used to determine that  given phone number already exists in our contactlist
                flag = 0
                # if phone_number in contact_phone_number_already_presents:
                for index in range(len(contact_phone_number_already_presents)):
                    # length_phone = len(contact_phone_number_already_presents[index])
                    length_phone = len(phone_number)
                    length_exist = len(contact_phone_number_already_presents[index])
                    if phone_number == contact_phone_number_already_presents[index][-length_phone:] or phone_number[-length_exist:] == contact_phone_number_already_presents[index]:
                        instance = prev_objs[index]
                        instance.contact_name = contact_name
                        # flag updated
                        flag = 1
                        #if given phone number is a whatsapp user then add contact chat user id as well
                        for another_index in range(len(user_objs_all)):
                            lenght_phone_number_user = len(user_phone_all[another_index])
                            lenght_phone_coming = len(phone_number)
                            if  phone_number[-lenght_phone_number_user:] == user_phone_all[another_index] or phone_number==user_phone_all[another_index][-lenght_phone_coming:]:
                                instance = prev_objs[index]
                                # print('existed user',user_objs_all[another_index],user_objs_all[another_index].mapping_user_id.get(app_user_id =user_objs_all[another_index]))#, usermapping_objs_all[another_index])
                                try:
                                    obj = user_objs_all[another_index].mapping_user_id.get(app_user_id = user_objs_all[another_index])
                                except:
                                    return error_response(success=False,
                                                          status_code=status.HTTP_400_BAD_REQUEST,
                                                          message=Constants.USERMAPPING_NOT_FOUND,
                                                          error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                                          message_code=ErrMsgCode.USERMAPPING_NOT_FOUND)
                                # obj = usermapping_objs_all[another_index]
                                # print(phone_number)
                                instance.contact_chat_user_id = obj
                #records those who are our new contacts and we need to create rows in contactlist table       
                if flag:
                    continue
                create_phone_number.append(phone_number)
            
                dict_contact_data= {
                    "chat_user_id": chat_user_id,
                    "contact_name":contact_name,
                    "phone_number": phone_number,
                    "contact_user_id": ''
                }
                serializer_list_dict.append(dict_contact_data)
            # to check if the new contact person is a whatsapp user then add contact_chat_user_id
            for index in range(len(create_phone_number)):
                for num in range(len(user_phone_all)):
                    #last digits should match 
                    length_ph = len(user_phone_all[num])
                    lenght_create_phone = len(create_phone_number[index])
                    if create_phone_number[index][-length_ph:] == user_phone_all[num] or create_phone_number[index] == user_phone_all[num][-lenght_create_phone:]:
                        try:
                            friend_chat_user_id_obj = user_objs_all[num].mapping_user_id.get(app_user_id =user_objs_all[num])
                            friend_chat_user_id = friend_chat_user_id_obj.chat_user_id
                        except:
                            # print("cccc")
                            return error_response(success=False,
                                                  status_code= status.HTTP_400_BAD_REQUEST,
                                                  message=Constants.USERMAPPING_NOT_FOUND,
                                                  error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                                  message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                                  )
                        # print('friend_Chat_user_id',friend_chat_user_id, type(friend_chat_user_id))# , type(chat_user_id_all[num]))
                        serializer_list_dict[index]['contact_chat_user_id'] = friend_chat_user_id
                        # serializer_list_dict[index]['contact_chat_user_id'] = chat_user_id_all[num]
            
            serializer_contact = ContactListSyncSerializer(data = serializer_list_dict,many = True)
            # print(serializer_contact)
    
            
            if serializer_contact.is_valid():
                # print("valide")
                serializer_contact.save()
            else:
                
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.NOT_SYNC,
                                    message_code= ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= serializer_error_list(serializer_contact.errors)
                                    )
            ContactList.objects.bulk_update(prev_objs, ["contact_name","contact_chat_user_id"])
            # logger_info.info('contacts -- post api')
            return json_response(success=True,
                                 status_code=status.HTTP_200_OK,
                                 message= Constants.SYNC,
                                #  result = serializer_contact.data
                                 )

        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )

    
    # permission_classes = [ApiKey, IsAuthenticated ]
    # def put(self, request):
    #     '''
    #     Api to update the contactsync
    #     '''
    #     try:
    #         user_id = request.user.user_id  # Get the user_id from the authentication token
    #         payload = request.data
    #         user_obj = request.user
    #         usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
    #         chat_user_id = usermapping_obj.chat_user_id
    #         contact_data = payload.get('contacts',[])
    #         prev_objs = []
    #         all_user_objs =  User.objects.all()
    #         usermapping_objs_all = UsersMapping.objects.all()
    #         user_contacts_objs = ContactList.objects.filter(chat_user_id = usermapping_obj)
    #         # print(user_contacts_objs)
    #         # print(user_contacts_objs[0].contact_name)
    #         for item in contact_data:
    #             # if item.get('id', None) is None:
    #             # user_id = user_id
    #             #id is chat_user_id of the person whose name we are updating
    #             id =  item.get('id',None)
    #             contact_name = item.get('contact_name',None)
    #             phone_number =  item.get('phone_number',None)

    #             if  contact_name is None or phone_number is None:
    #                 return error_response(success = False,
    #                                 status_code = status.HTTP_400_BAD_REQUEST,
    #                                 message = Constants.NOT_SYNC,
    #                                 error_msg= ErrMsg.CONTACT_NAME_OR_NUMBER_MISSING,
    #                                 message_code=ErrMsgCode.PAYLOAD_MISSING
    #                                 )
                
    #             for index in range(len(user_contacts_objs)):

    #                 if phone_number == user_contacts_objs[index].phone_number:
    #                     instance = user_contacts_objs[index]
    #                     instance.contact_name = contact_name
                        
    #                     if id:
    #                         for another_index in range(len(all_user_objs)):
    #                             if phone_number == all_user_objs[another_index].phone_number:
    #                                 # instance.contact_chat_user_id = id
    #                                 instance.contact_chat_user_id = usermapping_objs_all[another_index]
    #                     prev_objs.append(instance)

    #         ContactList.objects.bulk_update(prev_objs, ["contact_name","contact_chat_user_id"])
    #         serialized_data = ContactListSyncSerializer(prev_objs, many = True).data
    #         logger_info.info('contacts -------put api')
    #         return json_response(success=True, 
    #                              status_code=status.HTTP_200_OK,
    #                              message= Constants.UPDATE,
    #                              result=serialized_data)
            
    #     except Exception as err:
    #         logger_error.error('contacts ------put api')
    #         print("----------------------------------------------------")
    #         traceback.print_exc()
    #         print("----------------------------------------------------")
        
    #         return error_response(success = False,
    #                                 status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                                 message = Constants.INTERNAL_SERVER_ERROR,
    #                                 result = {},
    #                                 message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
    #                                 error_msg= str(err)
    #                                 )
    
    
class BlockUser(APIView):
    
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        '''api to get the details of blocked users  '''
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
            # chat_user_id = usermapping_obj.chat_user_id
           
            blocked_users = BlockList.objects.filter(from_chat_user_id = usermapping_obj)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
           

            paginator = Paginator(blocked_users, limit)
            page_obj = paginator.get_page(page)
            serialized_data = BlockListSerializer(page_obj, many=True).data
            # logger_info.info('block user ----get api')
            return json_response(success=True,
                                 status_code= status.HTTP_200_OK,
                                 message= Constants.DETAILS,
                                 result=serialized_data)
        
        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )
        

    def post(self, request):
        '''
        APi collect to_chat_user_id if (exists in contact list and user then block/unblock)
        otherwise invite message
        '''
        try:
            user_id= request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
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
            to_chat_user_id = payload.get('chat_user_id', None)
            # print(to_user_id)
            if to_chat_user_id is None:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.NOT_ABLE_TO_BLOCK,
                                    message_code=ErrMsgCode.PAYLOAD_MISSING,
                                    error_msg=ErrMsg.TO_CHAT_USER_ID_MISSING
                                    )
            if to_chat_user_id == str(chat_user_id):
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.NOT_ABLE_TO_BLOCK,
                                    message_code=ErrMsgCode.FORBIDDEN,
                                    error_msg=ErrMsg.NOT_ABLE_TO_BLOCK_YOURSELF)
           
            block_data = {
                "to_chat_user_id" : to_chat_user_id,
                "from_chat_user_id" : chat_user_id
            }
            #you can block only your friends
            try:
                contact_obj = ContactList.objects.get(chat_user_id = usermapping_obj, contact_chat_user_id = to_chat_user_id)
            #means the give to_chat_user_id person is not your friend so you cant even block them
            except ContactList.DoesNotExist:
                return error_response(success= False,
                                    message= Constants.USER_NOT_FOUND,
                                    status_code=status.HTTP_404_NOT_FOUND,
                                    message_code= ErrMsgCode.USER_NOT_FOUND,
                                    error_msg= ErrMsg.USER_NOT_FOUND
                              )
            # serialized_data = ''
            try: 
                block_obj = BlockList.objects.get(from_chat_user_id = usermapping_obj, to_chat_user_id = to_chat_user_id)
                if block_obj:
                   
                    block_obj.delete()
                    return json_response(success=True,
                                    message= Constants.UNBLOCKED,
                                    status_code=status.HTTP_200_OK)
            except BlockList.DoesNotExist:
                serializer_block = BlockingSerializer(data = block_data)
                # print(serializer_block)
                if serializer_block.is_valid():
                    serializer_block.save()
                    # serialized_data = serializer_block.data
                else:
                    print(serializer_block.errors)
                    return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message= Constants.NOT_ABLE_TO_BLOCK, 
                                    message_code= status.HTTP_400_BAD_REQUEST,
                                    error_msg= serializer_error_format(serializer_block.errors)
                                   )
            # print(serializer_block.data)
            # logger_info.info('Block user -------post api')
            return json_response(
                # result= serialized_data, 
                                message= Constants.BLOCKED,
                                status_code=status.HTTP_200_OK)
           
        except Exception as err:
            logger_error.error(err, exc_info=True)
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )
