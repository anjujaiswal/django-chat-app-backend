from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User, Session, ContactList, Privacy,BlockList
from .serializers import UserSerializer, RegisteSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, BlockListSerializer, ContactListSyncSerializer
import json
from rest_framework import status
from utils.helpers import json_response, get_tokens_for_user, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization

from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.paginator import Paginator

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
from django.db.models import Q

class GetContactList(APIView):
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            # search_key = request.GET.get('search_key',None)
            search = request.GET.get('search',None)
            # print(search)
            # print(search_key, search_value)
            # contact_objs  = ContactList.objects.filter(user_id = user_id)
            contact_objs = ContactList.objects.filter(user_id=user_id)

            if search:
                contact_objs = contact_objs.filter(
                    Q(phone_number__icontains=search) |
                    Q(contact_name__icontains=search)
                )

            # ContactList.objects.filter(Q(phone_number__icontains=search) | Q(contact_name__icontains = search))
            serializer = ContactListSerializer(contact_objs, many=True)
            # print(contact_objs)
            return json_response(result= serializer.data)

        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))

class ContactSyncser(APIView):
    '''
    Api for contactSync if given phonenumber exists then save contact_user_id foreign key 
    otherwise store null
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def post(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            data = request.data
            user = request.user
            contact_data = data.get('contacts',[])
            user_objs_all = User.objects.all()
            user_phone_all = []
            user_userid_all = []

            for phone in user_objs_all:
                if phone.phone_number == user.phone_number:
                    continue
                user_phone_all.append(phone.phone_number)
                user_userid_all.append(phone.id)
            # print(user_userid_all)
            user_userid_all = [str(uuid) for uuid in user_userid_all]
            # print(user_userid_all)
            serializer_list_dict = []
            create_phone_number = []
            for item in contact_data:
                phone_number = item.get('phone_number',None)
                contact_name = item. get('contact_name', None)
                if  contact_name is None or phone_number is None:
                    return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'Provide the correct contact_name, phone_number',
                                    )
                create_phone_number.append(phone_number)
            
                dict = {
                    "user_id": user_id,
                    "contact_name":contact_name,
                    "phone_number": phone_number,
                    "contact_user_id": ''
                }
                serializer_list_dict.append(dict)
            for index in range(len(create_phone_number)):
                for num in range(len(user_phone_all)):
                    if create_phone_number[index] == user_phone_all[num]:
                        serializer_list_dict[index]['contact_user_id'] = user_userid_all[num]
           
            # serializer_contact = ContactListSerializer(data = serializer_list_dict,many = True)
            serializer_contact = ContactListSyncSerializer(data = serializer_list_dict,many = True)
            # print(serializer_contact)
            if serializer_contact.is_valid():
                # print("valide")
                serializer_contact.save()
            else:
                # print(serializer_contact.errors)
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Contact not synced')
            
            return json_response(success=True,
                                 status_code=status.HTTP_201_CREATED,
                                 message='Contact_synced',
                                 result = serializer_contact.data)

        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))
    
 
class ContactUpdate(APIView):
    '''
    Api to update the contactsync
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def put(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            data = request.data
            user_obj = request.user
            contact_data = data.get('contacts',[])
            prev_objs = []
            all_user_objs =  User.objects.all()
            user_contacts_objs = ContactList.objects.filter(user_id = user_id)
            # print(user_contacts_objs)
            print(user_contacts_objs[0].contact_name)
            for item in contact_data:
                # if item.get('id', None) is None:
                user_id = user_id
                id =  item.get('id',None)
                contact_name = item.get('contact_name',None)
                phone_number =  item.get('phone_number',None)

                if  contact_name is None or phone_number is None:

                    return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'Provide the id, contact_name, phone_number',
                                    )
                
                for index in range(len(user_contacts_objs)):

                    if phone_number == user_contacts_objs[index].phone_number:
                        instance = user_contacts_objs[index]
                        instance.contact_name = contact_name
                        # instance.contact_user_id = 
                        if id:

                            for another_index in range(len(all_user_objs)):
                                if phone_number == all_user_objs[another_index].phone_number:
                                    instance.contact_user_id = all_user_objs[another_index]
                        prev_objs.append(instance)
            ContactList.objects.bulk_update(prev_objs, ["contact_name","contact_user_id"])
            serialized_data = ContactListSyncSerializer(prev_objs, many = True).data
            return json_response(success=True, status_code=status.HTTP_201_CREATED,message='Contacts Updated',
                                 result=serialized_data)
            
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))
        
        
class BlockUser(APIView):
    '''
    APi collect to_user_id if (exists in contact list and user then block/unblock)
    otherwise invite message
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def post(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
           
            to_user_id = payload.get('to_user_id', None)
            if to_user_id is None:
                return json_response(success=False,
                                    message= 'SEND_THE_TO_USER_ID',
                                    )
            block_data = {
                'to_user_id' : to_user_id,
                'from_user_id' : user_id
            }
            try:
                contact_obj = ContactList.objects.get(contact_user_id = User(id = to_user_id))
            except ContactList.DoesNotExist:
                return json_response(success= False,
                                    message='Invite User',
            
                              )
            serialized_data = ''
            try: 
                block_obj = BlockList.objects.get(from_user_id = user_id, to_user_id= to_user_id)#
                if block_obj:
                    # print("ene")
                    block_obj.delete()
                    return json_response(success=True,
                                    message='User is unblocked',
                                    status_code=status.HTTP_400_BAD_REQUEST)
            except:
                serializer_block = BlockListSerializer(data = block_data)
                if serializer_block.is_valid():
                    serializer_block.save()
                    serialized_data = serializer_block.data
                else:
                    return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message='User is UnBlocked', error= serializer_block.errors)
            # print(serializer_block.data)
            return json_response(result= serialized_data, message='User blocked')
           
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))   
        
class BlockDetails(APIView):
    permission_classes = [ ApiKey, IsAuthenticated ]
    def get(self, request):
        try:
            user_id = request.user.id  # Get the user_id from the authentication token
            payload = request.data
            user_obj = request.user
            # blocked_users = User.objects.filter(blocked_to__from_user_id=user_id)###yeshi 
            ##trying new
            blocked_users = BlockList.objects.filter(from_user_id=user_id)
            search = request.GET.get('search',None)
            limit = request.GET.get('limit',100)
            page = request.GET.get('page',1)
            # if search:#purana wala shi hai serialiser ki wjhse error aya
            #     blocked_users = blocked_users.filter(
            #         Q(phone_number__icontains=search) |
            #         Q(username__icontains=search)
            #     )
            if search:##new wala according to the serializer
                blocked_users = blocked_users.filter(
                    Q(to_user_id__username__icontains=search) |
                    Q(to_user_id__phone_number__icontains=search)
                )

            paginator = Paginator(blocked_users, limit)
            page_obj = paginator.get_page(page)
            # serialized_data = UserSerializer(blocked_users, many=True).data
            # serialized_data = UserSerializer(page_obj, many=True).data#yeshi
            serialized_data = BlockListSerializer(page_obj, many=True).data#new try
            return json_response(success=True, result=serialized_data)
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))   
        


      
# class ContactUpdatebb(APIView):
#     '''
#     Api to update the contactsync
#     '''
#     permission_classes = [ApiKey, IsAuthenticated ]
#     def put(self, request):
#         try:
#             user_id = request.user.id  # Get the user_id from the authentication token
#             data = request.data
#             user_obj = request.user
#             contact_data = data.get('contacts',[])
#             prev_objs = []
            
#             for item in contact_data:
#                 # if item.get('id', None) is None:
#                 user_id = user_id
#                 id =  item.get('id',None)
#                 contact_name = item.get('contact_name',None)
#                 phone_number =  item.get('phone_number',None)

#                 if id is None or contact_name is None or phone_number is None:

#                     return json_response(success = False,
#                                     status_code = status.HTTP_400_BAD_REQUEST,
#                                     message = 'Provide the id, contact_name, phone_number',
#                                     )
#                 instance = ContactList.objects.get(user_id =str(user_id), phone_number= phone_number, )
#                 instance.contact_name = contact_name
#                 instance.contact_user_id = User(id = id)
#                 prev_objs.append(instance)
#             print(prev_objs)
#             ContactList.objects.bulk_update(prev_objs, ["contact_name","contact_user_id"])
#             return json_response(success=True, status_code=status.HTTP_201_CREATED,message='Contacts Updated')
            
#         except Exception as err:
#             return json_response(success = False,
#                                     status_code = status.HTTP_400_BAD_REQUEST,
#                                     message = 'SOMETHING_WENT_WRONG',
#                                     result = {},
#                                     error = str(err))
        

# class ContactSync(APIView):
#     '''
#     Api for contactSync if given phonenumber exists then save contact_user_id foreign key 
#     otherwise store null
#     '''
#     permission_classes = [ApiKey, IsAuthenticated ]
#     def post(self, request):
#         try:
#             user_id = request.user.id  # Get the user_id from the authentication token
#             data = request.data
#             contact_data = data.get('contacts',[])
#             # print(contact_data)
#             user_obj = request.user
#             # print(request.user.phone_number)
#             new_objs = []###create krne ke liye serializer data
#             user_objs_all = User.objects.all()#.exclude(id = user_id)
#             user_phone_all = []
#             for number in user_objs_all:
#                 user_phone_all.append(number.phone_number)
#             # print(user_phone_all)
#             # print("+14155552672" in user_phone_all)
#             # print(request.user.phone_number in user_phone_all,"token")
#             # return json_response()
#             for item in contact_data:
#                 # if item.get('id', None) is None:
#                 user_id = user_id
#                 # id =  genUUID()
#                 contact_name = item.get('contact_name',None)
#                 phone_number =  item.get('phone_number',None)
#                 if  contact_name is None or phone_number is None:
#                     return json_response(success = False,
#                                     status_code = status.HTTP_400_BAD_REQUEST,
#                                     message = 'Provide the correct contact_name, phone_number',
#                                     )
#                 try:                    
#                     contact_obj = User.objects.get(phone_number = phone_number)

#                 except User.DoesNotExist:
#                     contact_obj = None
#                 # contact_obj = ''
#                 # if phone_number is not request.user.phone_number and phone_number in user_objs_all:
#                     # contact_obj = User(phone_number = phone_number)
               
#                 instance =  ContactList(user_id=User(id=user_id),contact_name = contact_name, phone_number=phone_number, contact_user_id = contact_obj)
#                 # instance = ContactList.objects.create(id=id)
#                 new_objs.append(instance)
#             ContactList.objects.bulk_create(new_objs)
        
#             return json_response(success=True, status_code=status.HTTP_201_CREATED,message='Contacts Synced')
#         except Exception as err:
#             return json_response(success = False,
#                                     status_code = status.HTTP_400_BAD_REQUEST,
#                                     message = 'SOMETHING_WENT_WRONG',
#                                     result = {},
#                                     error = str(err))
   
  