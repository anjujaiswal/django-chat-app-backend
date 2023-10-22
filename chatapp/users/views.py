from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User, Session, ContactList, Privacy
from .serializers import UserSerializer, RegisteSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, SessionSerializer
import json
from rest_framework import status
from utils.helpers import json_response, get_tokens_for_user, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization


from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken

# from  import 
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView


class AddUser(APIView):
    '''
    Api user does not exits first register(with default privacy settings)
    '''
    permission_classes = [ApiKey]
    
    def post(self,request):

        try:
            payload = request.data
        
            username = payload.get('username', None)
            phone_number = payload.get('phone_number', None)
           
            if phone_number is None:
                return json_response(success = False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='PHONE_NUMBER IS MISSING')
        
            flag = 0
            user_data = {
                    'username' : username,
                    'phone_number': phone_number,
                    'profile_picture': payload.get('profile_picture', None),
                    'status_quotes' : payload.get('status_quotes', None),
                }
            serializer_register = RegisteSerializer(data=user_data)
            try:
                user_obj = User.objects.get(phone_number=phone_number)

            except User.DoesNotExist:
                if serializer_register.is_valid():
                    # print(1,"kkkk")
                    flag = 1
                    serializer_register.save()
                else:
                    json_response(success=False,
                                status_code=status.HTTP_400_BAD_REQUEST, 
                                message='NOT_REGISTERED', 
                                error=serializer_register.errors)
            
            user_obj = User.objects.get(phone_number=phone_number)
            serialzed_data = RegisteSerializer(user_obj)

            if flag:
                privacy_data = { "user_id": user_obj.id }
                serializer_privacy = PrivacySerializer(data=privacy_data)

                if serializer_privacy.is_valid():
                    # print("privacy")
                    serializer_privacy.save()
                else:
                    json_response(success=False,
                                status_code=status.HTTP_400_BAD_REQUEST,
                                message='Privacy is not set', 
                                error= serializer_privacy.errors)
           
            
            return json_response(success=True, 
                                status_code=status.HTTP_201_CREATED, 
                                message='CREATED',
                                result= serialzed_data.data)
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = 'INTERNAL_SERVER_ERROR',
                                    result = {},
                                    error = str(err))
        
class VerifyOtp(APIView):
    '''
    api for creating the session of the user
    '''
    permission_classes = [ApiKey]
    def post(self,request):
        try:
            payload = request.data
            device_id = payload.get('device_id',None)
            device_token = payload.get('device_token', None)
            device_type = payload.get('device_type', None)
            otp = payload.get('otp', config('OTP'))
            id = payload.get('id', None)

            if id is None or device_id is None or device_token is None or device_type is None:
                return json_response(success = False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='PROVIDE_DETAILS')
            
            user_obj = User.objects.get(id = id)
            token = get_tokens_for_user(user_obj)
            
            session_data = {
                'user_id': id,
                'device_id':  device_id, 
                'device_token': device_token, 
                'device_type':   device_type,
                'jwt_token': token['refresh']
            }
            try:
                # session_obj = Session.objects.get(user_id = user_obj.id, device_id = device_id)
                session_obj = Session.objects.get( device_id = device_id)
                
                serializer_session = SessionSerializer(instance=session_obj,data=session_data,partial=True)
                if serializer_session.is_valid():
                    # print('ii')
                    serializer_session.save()
                else:
                    json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message='Session not updated', 
                                    error= serializer_session.errors)

            except Session.DoesNotExist:
                # serializer_login = LoginSerializer(data=session_data)
                serializer_session = SessionSerializer(data=session_data)
                if serializer_session.is_valid():
                    print("ff")
                    serializer_session.save()
                else:
                    json_response(success=False,
                                 status_code=status.HTTP_400_BAD_REQUEST, 
                                 message='Session not created', error= serializer_session.errors)
                    
            return json_response(success=True,
                                status_code=status.HTTP_201_CREATED,
                                message='Session created',
                                result={'sesion_details':serializer_session.data, 'token': token})

        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))

class Update(APIView):
    # authentication_classes = [JWTAuthentication]
    permission_classes = [ApiKey, IsAuthenticated]
    def put(self, request):
        try:
            data = request.data
            id = request.user.id
            
            user_obj = User.objects.get(id=id)

            user_data = {
                    'username' : data.get('username', None),
                    'profile_picture': data.get('profile_picture', None),
                    'status_quotes' : data.get('status_quotes', None),
                    }
            #user-active thing does not updated via profile update
            serializer_user = RegisteSerializer(instance=user_obj,data=user_data, partial= True)
            if serializer_user.is_valid():
                serializer_user.save()
            
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message='UPDATED_SUCCESSFULLY',
                                result=serializer_user.data )
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))
class UserDetail(APIView):
    '''
    APi for getting particular user details
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    
    def get(self, request):
        try:
            payload = request.data
            user_obj = request.user
            id = request.user.id
            if id is not None:
                try:
                    # user_obj = User.objects.get(id=id)
                    serializer =  UserSerializer(user_obj)
                    return json_response(result=serializer.data)
                except User.DoesNotExist:
                    return json_response(success=False, 
                                        status_code=status.HTTP_404_NOT_FOUND, 
                                        message="User with the specified ID does not exist", 
                                        result={}, error={})
            
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message='',
                                result = serializer.data)
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = 'INTERNAL_SERVER_ERROR',
                                    result = {},
                                    error = str(err))

# class ContactSync(APIView):
#     '''
#     Api for contactSync
#     '''
#     permission_classes = [ApiKey, IsAuthenticated ]
#     def post(self, request):
#         try:
#             user_id = request.user.id  # Get the user_id from the authentication token
#             data = request.data
#             contact_data = data.get('contacts',[])
#             # print(contact_data)
#             user_obj = request.user
#             # # print(user_obj)
#             # # Create a list of ContactList objects with user_id and contact_data
#             contact_list_objects = []
#             # contact_list_objects = [
                
#             #     {
#             #         "user_id": user_id,
#             #         "contact_name": item['contact_name'],
#             #         "phone_number": item['phone_number']
#             #     }
#             #     for item in contact_data
#             # ]
#             for item in contact_data:
#                 print(user_id)
#                 dict = {
#                     "user_id": user_id,
#                     "contact_name": item.get('contact_name'),
#                     "phone_number": item.get('phone_number')
#                 }
#                 print(dict)
#                 contact_list_objects.append(dict)

#             print((contact_list_objects))
            
#             serializer = ContactListSerializer(data=contact_list_objects, many=True)
#             # print(serializer.errors)
#             if serializer.is_valid():
#                 print("ff")
#                 serializer.save()
        
#             return json_response(success=True, status_code=status.HTTP_201_CREATED,message='')
#         except Exception as err:
#             return json_response(success = False,
#                                     status_code = status.HTTP_400_BAD_REQUEST,
#                                     message = 'SOMETHING_WENT_WRONG',
#                                     result = {},
#                                     error = str(err))
class PrivacyGet(APIView):
    '''
        Api for getting the privacy settings of particular user
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        try:
            user_id = request.user.id
            try:
                privacy_obj = Privacy.objects.get(user_id=user_id)
            except:
                return json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Privacy setting for that user not found')
            
            serializer =  PrivacySerializer(privacy_obj)
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message='Privacy setting',
                                result = serializer.data)
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))

class PrivacyUpdate(APIView):
    '''
        Api for updating the privacy settings of particular user
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def put(self, request):
        
        try:
            data = request.data
            user_id = request.user.id
            try:
                privacy_obj = Privacy.objects.get(user_id=user_id)
            except:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Privacy setting for that user not found')
           
            serializer = PrivacySerializer(instance=privacy_obj,data=data,partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Privacy setting not updated', 
                                    error=serializer.errors)
            return json_response(status_code=status.HTTP_200_OK,message='Privacy setting  updated', result=serializer.data)
            
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))
class Logout(APIView):
    '''
        Api for Logout collect user_id, device_id and remove that particular session
    '''
    permission_classes = [ApiKey, IsAuthenticated]
    def post(self, request):
        
        try:
            data = request.data
            user_id = request.user.id
            
            device_id = data.get('device_id', None)
            if device_id is None:
                return json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Provide the device_id')
            try:
                session_obj = Session.objects.get(user_id = user_id, device_id = device_id)
                session_obj.delete()
            except:
                return json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Session does not exist')
            
            
            refresh_token = session_obj.jwt_token
            print(refresh_token)
            # token = RefreshToken(base64_encoded_token_string)
            RefreshToken(refresh_token).blacklist()

            # RefreshToken(refresh_token).blacklist()
            return json_response(status_code=status.HTTP_200_OK,message='LOGOUT SUCCESSFULLY')
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))

class RefreshTokenApi(APIView):
    '''
        Api collection for creating a new access token
        using the refresh token
    '''
    permission_classes = [ApiKey, IsAuthenticated]
    def post(self, request):
        '''
            Post api to send a new access token
        '''
        try:
        
            data = request.data
            refresh_token = data.get("refresh", None)
           
            if refresh_token is None:
                return json_response(success = False,
                                         status_code = status.HTTP_400_BAD_REQUEST,
                                         message = "Provide refresh token.",
                                         result = {},
                                        )
            refresh_token_object = RefreshToken(refresh_token)
            access_token = refresh_token_object.access_token
            return json_response(success = True,
                                     status_code = status.HTTP_200_OK,
                                     message = "New access token provided.",
                                     result = {"refresh": str(refresh_token),
                                               "access": str(access_token)},
                                     )
        
        except Exception as err:
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))












# class Register(GenericAPIView):
#     def post(self,request):
#         try:
#             data = (request.data)
#             username = data.get('username', None)
#             phone_number = data.get('phone_number', None)
#             profile_picture = data.get('profile_picture', None)
#             user_status = data.get('user_status', None)
#             status_quotes = data.get('status_quotes', None)
#             if(phone_number is None):
#                 return json_response(success = True, status_code=status.HTTP_400_BAD_REQUEST,message='PHONE_NUMBER IS MISSING')
#             serializer = RegisteSerializer(data=data)
#             # print(serializer.is_valid(),serializer.errors,phone_number)
#             user_obj = User.objects.get(phone_number=phone_number)
#             if user_obj:
#                 return json_response(success=False, status_code=status.HTTP_400_BAD_REQUEST, message='ALready registered' )
#             if serializer.is_valid():
#                 serializer.save()
#             return json_response(success=True, status_code=status.HTTP_201_CREATED, message='',result = serializer.data)
#         except json.JSONDecodeError:
#             return json_response(success=False, status_code=status.HTTP_400_BAD_REQUEST, message='Invalid JSON data')
