from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UserStatus, Session, ContactList, Privacy,UsersMapping
from .serializers import UserSerializer,UserStatusSerializer, RegisterSerializer,UsersMappingSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, SessionSerializer
import json
from rest_framework import status
from utils.helpers import json_response, get_tokens_for_user, get_user_id_from_tokens, ApiKey, api_key_authorization,token_authorization

from phonenumber_field.modelfields import PhoneNumberField
import traceback
from decouple import config
from rest_framework_simplejwt.tokens import RefreshToken

# from  import 
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework.views import APIView
import datetime

class AddUser(APIView):
    '''
    Api user does not exits first register(with default user status)  add a entry in usermapping table 
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
            usermapping_flag = 0
            user_data = {
                    'username' : username,
                    'phone_number': phone_number,
                    'profile_picture': payload.get('profile_picture', None),
                    }
            # serializer_register = RegisterSerializer(data=user_data)
            serializer_register = UserSerializer(data=user_data)
            try:
                user_obj = User.objects.get(phone_number = phone_number)
                print(user_obj)
                # return 

            except User.DoesNotExist:
                #creating the row in user table
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
            # serialzed_data = RegisterSerializer(user_obj)
            serialzed_data = UserSerializer(user_obj)
            # print(user_obj.user_id, serialzed_data.data,"==============")
            #for first time user we create the row for usermapping table
            if flag:
                usersmapping_data = { "app_user_id": user_obj.user_id}
                # usersmapping_data = { "app_user_id": user_obj.id}
                serializer_usermapping = UsersMappingSerializer(data = usersmapping_data)
                if serializer_usermapping.is_valid():
                    #creating the row in usersmapping table
                    usermapping_flag = 1
                    serializer_usermapping.save()
                else:
                    print(serializer_usermapping.errors)
                    return json_response(success=False,
                                         status_code=status.HTTP_400_BAD_REQUEST,
                                         message='Users mapping is not created ',
                                         error = serializer_usermapping.errors
                                         )
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj.user_id)
                if usermapping_flag:
                    user_status_data = {
                        "chat_user_id": usermapping_obj.chat_user_id,
                        "timestamp": datetime.datetime.now()
                        }
                    serializer_userstatus = UserStatusSerializer(data = user_status_data)
                    if serializer_userstatus.is_valid():
                        serializer_userstatus.save()
                    else:
                        print(serializer_userstatus.errors)
                        return json_response(success=False,
                                             status_code=status.HTTP_400_BAD_REQUEST,
                                             message='User status not created',
                                             error = serializer_userstatus.errors)
                # privacy_data = { "user_id": user_obj.id }
                # serializer_privacy = PrivacySerializer(data=privacy_data)

                # if serializer_privacy.is_valid():
                #     # print("privacy")
                #     serializer_privacy.save()
                # else:
                #     json_response(success=False,
                #                 status_code=status.HTTP_400_BAD_REQUEST,
                #                 message='Privacy is not set', 
                #                 error= serializer_privacy.errors)
           
            
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
    api for creating the session of the user via verifying bypass otp
    '''
    permission_classes = [ApiKey]
    def post(self,request):
        try:
            payload = request.data
            device_id = payload.get('device_id',None)
            device_token = payload.get('device_token', None)
            device_type = payload.get('device_type', None)
            otp = payload.get('otp', config('OTP'))
            # id = payload.get('id', None)
           
            phone_number = payload.get('phone_number', None)
            
            if phone_number is None or device_id is None or device_token is None or device_type is None:
                return json_response(success = False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='PROVIDE_DETAILS')
            
            
            user_obj = User.objects.get(phone_number=phone_number)
            token = get_tokens_for_user(user_obj)
            session_data = {
                'user_id': user_obj.user_id,
                'device_id':  device_id, 
                'device_token': device_token, 
                'device_type':   device_type,
                'jwt_token': token['refresh']
            }
            try:
                # session_obj = Session.objects.get(user_id = user_obj.id, device_id = device_id)
                #if device_id already exists 
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
                #if session does not exist then create one
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
                                result={'sesion_details':serializer_session.data ,'token': token})

        except Exception as err:
            print("----------------------------------------------------")
            traceback.print_exc()
            print("----------------------------------------------------")
            return json_response(success = False,
                                    status_code = status.HTTP_400_BAD_REQUEST,
                                    message = 'SOMETHING_WENT_WRONG',
                                    result = {},
                                    error = str(err))


class Update(APIView):
    '''
    api to update user  
    '''
    # authentication_classes = [JWTAuthentication]
    permission_classes = [ApiKey, IsAuthenticated]
    def put(self, request):
        try:
            data = request.data
            user_id = request.user.user_id
            user_obj = request.user
            # user_obj = User.objects.get(user_id = user_id)

            user_data = {
                    'username' : data.get('username', None),
                    'profile_picture': data.get('profile_picture', None),
                   
                    }
            #user-active thing does not updated via profile update
            serializer_user = RegisterSerializer(instance=user_obj,data=user_data, partial= True)
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
            user_id = request.user.user_id
            if user_id is not None:
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


class PrivacyGet(APIView):
    '''
        Api for getting the privacy settings of particular user
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        try:
            user_id = request.user.user_id
            # print("xxxxx",user_id)
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            chat_user_id = usermapping_obj.chat_user_id
            serializer = None
            privacy_obj = None
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id )
                # print('cc',privacy_obj)
            except Privacy.DoesNotExist:
                # print("cccc")
                privacy_data = {"chat_user_id": chat_user_id}
                serializer = PrivacySerializer(data = privacy_data)
                if serializer.is_valid():
                    # print("@@@@@")
                    serializer.save()
                    return json_response(success=True,
                                         status_code=status.HTTP_201_CREATED,
                                         result=serializer.data,
                                         message='Privacy settings data')
                else:
                    return json_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    error=serializer.errors)
            
            serializer =  PrivacySerializer(privacy_obj)
            return json_response(success=True,
                                         status_code=status.HTTP_201_CREATED,
                                         result=serializer.data,
                                         message='Privacy settings data')
        
        except Exception as err:
            # print("----------------------------------------------------")
            # traceback.print_exc()
            # print("----------------------------------------------------")
            
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
            payload = request.data
            user_id = request.user.user_id
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            chat_user_id = usermapping_obj.chat_user_id
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id)
            except:
                return json_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message='Privacy setting for that user not found')
           
            serializer = PrivacySerializer(instance=privacy_obj,data= payload,partial=True)
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
        



class RefreshTokenApi(APIView):
    '''
        Api collection for creating a new access token,refresh token
        using the refresh token
    '''
    permission_classes = [ApiKey, IsAuthenticated]
    def post(self, request):
        '''
            Post api to send a new access token
        '''
        try:
        
            payload = request.data
            refresh_token = payload.get("refresh", None)
           
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
