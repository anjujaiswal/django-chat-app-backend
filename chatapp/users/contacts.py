from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UsersMapping, Session, ContactList, Privacy,BlockList
from .serializers import UserSerializer, UsersMappingSerializer, RegisterSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, BlockListSerializer, ContactListSyncSerializer,BlockingSerializer
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

class Contacts(APIView):
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        '''
        api to give details of the contactlist of the user
        '''
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            
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
            # ContactList.objects.filter(Q(phone_number__icontains=search) | Q(contact_name__icontains = search))
            # serializer = ContactListSerializer(contact_objs, many=True)
            serializer = ContactListSerializer(page_obj, many=True)
            # print(contact_objs)
            return json_response(result= serializer.data,message=Constants.DETAILS)

        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
        
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
            user = request.user
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            contact_data = data.get('contacts',[])
            user_objs_all = User.objects.all()
            usermapping_objs_all = UsersMapping.objects.all()
            user_phone_all = []
            app_user_id_all = []
            chat_user_id_all = []
            contact_phone_number_already_presents = []
            user_contact_objs = ContactList.objects.filter(chat_user_id = usermapping_obj)
            
            for index in range(len(user_contact_objs)):
                contact_phone_number_already_presents.append(user_contact_objs[index].phone_number)

            for index in range(len(user_objs_all)):
                if user_objs_all[index].phone_number == user.phone_number:
                    continue
                user_phone_all.append(user_objs_all[index].phone_number)
                app_user_id_all.append(user_objs_all[index].user_id)
                chat_user_id_all.append(usermapping_objs_all[index].chat_user_id)
            # print(app_user_id_all)
            app_user_id_all = [str(uuid) for uuid in app_user_id_all]
            chat_user_id_all = [str(uuid) for uuid in chat_user_id_all]

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
                if phone_number in contact_phone_number_already_presents:
                    continue
                create_phone_number.append(phone_number)
            
                dict = {
                    "chat_user_id": chat_user_id,
                    "contact_name":contact_name,
                    "phone_number": phone_number,
                    "contact_user_id": ''
                }
                serializer_list_dict.append(dict)
            for index in range(len(create_phone_number)):
                for num in range(len(user_phone_all)):
                    if create_phone_number[index] == user_phone_all[num]:
                        serializer_list_dict[index]['contact_chat_user_id'] = chat_user_id_all[num]
           
            # serializer_contact = ContactListSerializer(data = serializer_list_dict,many = True)
            serializer_contact = ContactListSyncSerializer(data = serializer_list_dict,many = True)
            # print(serializer_contact)
    
            # try:
            if serializer_contact.is_valid():
                # print("valide")
                serializer_contact.save()
            # except:
            else:
                
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.NOT_SYNC,
                                    message_code= ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= serializer_error_list(serializer_contact.errors)
                                    )
            
            return json_response(success=True,
                                 status_code=status.HTTP_201_CREATED,
                                 message= Constants.SYNC,
                                 result = serializer_contact.data)

        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )

    
    # permission_classes = [ApiKey, IsAuthenticated ]
    def put(self, request):
        '''
        Api to update the contactsync
        '''
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            contact_data = payload.get('contacts',[])
            prev_objs = []
            all_user_objs =  User.objects.all()
            usermapping_objs_all = UsersMapping.objects.all()
            user_contacts_objs = ContactList.objects.filter(chat_user_id = usermapping_obj)
            # print(user_contacts_objs)
            # print(user_contacts_objs[0].contact_name)
            for item in contact_data:
                # if item.get('id', None) is None:
                # user_id = user_id
                #id is chat_user_id of the person whose name we are updating
                id =  item.get('id',None)
                contact_name = item.get('contact_name',None)
                phone_number =  item.get('phone_number',None)

                if  contact_name is None or phone_number is None:
                    return error_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = Constants.NOT_SYNC,
                                    error_msg= ErrMsg.CONTACT_NAME_OR_NUMBER_MISSING,
                                    message_code=ErrMsgCode.PAYLOAD_MISSING
                                    )
                
                for index in range(len(user_contacts_objs)):

                    if phone_number == user_contacts_objs[index].phone_number:
                        instance = user_contacts_objs[index]
                        instance.contact_name = contact_name
                        # print(instance.contact_name)
                        # instance.contact_user_id = 
                        if id:
                            for another_index in range(len(all_user_objs)):
                                if phone_number == all_user_objs[another_index].phone_number:
                                    # instance.contact_chat_user_id = id
                                    instance.contact_chat_user_id = usermapping_objs_all[another_index]
                        prev_objs.append(instance)

            ContactList.objects.bulk_update(prev_objs, ["contact_name","contact_chat_user_id"])
            serialized_data = ContactListSyncSerializer(prev_objs, many = True).data
            return json_response(success=True, 
                                 status_code=status.HTTP_200_OK,
                                 message= Constants.UPDATE,
                                 result=serialized_data)
            
        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )
        
# class ContactUpdate(APIView):
    
        
class BlockUser(APIView):
    
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        '''api to get the details of blocked users  '''
        try:
            user_id = request.user.user_id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
           
            blocked_users = BlockList.objects.filter(from_chat_user_id = usermapping_obj)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
           

            paginator = Paginator(blocked_users, limit)
            page_obj = paginator.get_page(page)
            serialized_data = BlockListSerializer(page_obj, many=True).data
            return json_response(success=True,
                                 status_code= status.HTTP_200_OK,
                                 message= Constants.DETAILS,
                                result=serialized_data)
        
        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
        
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
            user_obj = request.user
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            chat_user_id = usermapping_obj.chat_user_id
            to_chat_user_id = payload.get('to_chat_user_id', None)
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
                # contact_obj = ContactList.objects.get(contact_user_id = User(id = to_user_id))
                contact_obj = ContactList.objects.get(chat_user_id = usermapping_obj, contact_chat_user_id = to_chat_user_id)
            
            except ContactList.DoesNotExist:
                return error_response(success= False,
                                    message= Constants.INVITE_USER,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message_code= ErrMsgCode.USER_NOT_FOUND,
                                    error_msg= ErrMsg.USER_NOT_FOUND
                              )
            serialized_data = ''
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
                    serialized_data = serializer_block.data
                else:
                    print(serializer_block.errors)
                    return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message= Constants.NOT_ABLE_TO_BLOCK, 
                                    message_code= status.HTTP_400_BAD_REQUEST,
                                    error_msg= serializer_error_format(serializer_block.errors)
                                   )
            # print(serializer_block.data)
            return json_response(result= serialized_data, 
                                message= Constants.BLOCKED,
                                status_code=status.HTTP_200_OK)
           
        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
        
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )
