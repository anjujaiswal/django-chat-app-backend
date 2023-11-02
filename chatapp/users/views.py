from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UserStatus, Session, ContactList, Privacy,UsersMapping
from .serializers import UserSerializer, UserstatuswithprofileSerializer,UserStatusSerializer, RegisterSerializer,UsersMappingSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, SessionSerializer
import json
from rest_framework import status
from utils.helpers import json_response,error_response, get_tokens_for_user, get_user_id_from_tokens, serializer_error_format,ApiKey, api_key_authorization,token_authorization

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
from common.constants  import Constants, ErrMsgCode, ErrMsg

from phonenumber_field.modelfields import PhoneNumberField

class AddUser(APIView):
    '''
    Api user does not exits first register(with default user status)  add a entry in usermapping table 
    '''
    permission_classes = [ApiKey]
    
    def post(self,request):

        try:
            payload = request.data
            
            # username = payload.get('username', None)
            phone_number = payload.get('phone_number', None)
            # print(phone_number)
            # if phone_number is None:
            #     return json_response(success = False, 
            #                         status_code=status.HTTP_400_BAD_REQUEST,
            #                         message=Constants.PHONE_MISSING)
            
            flag = 0
            usermapping_flag = 0
            user_data = {
                    # 'username' : username,
                    'phone_number': phone_number,
                    # 'profile_picture': payload.get('profile_picture', None),
                    }
            
            serializer_register = None
            
            user_obj = User.objects.filter(phone_number = phone_number)

                #creating the row in user table
                # print("err")
            if not user_obj.exists():
                serializer_register = UserSerializer(data=user_data)
                try:
                    serializer_register.is_valid()
                   
                    flag = 1
                    serializer_register.save()
                except :
                    return error_response(success=False,
                                status_code=status.HTTP_400_BAD_REQUEST, 
                                message= Constants.OTP_NOT_SENT, 
                                error_msg= serializer_error_format(serializer_register.errors),
                                message_code= ErrMsgCode.VALIDATION_ERROR
                                 )
    
            user_obj = User.objects.get(phone_number=phone_number)
           
            serialzed_data = UserSerializer(user_obj)
            #for first time user we create the row for usermapping table
            if flag:
                usersmapping_data = { "app_user_id":  user_obj.user_id}
                # usersmapping_data = { "app_user_id": user_obj.id}
                serializer_usermapping = UsersMappingSerializer(data = usersmapping_data)
                try: 
                    serializer_usermapping.is_valid()
                    #creating the row in usersmapping table
                    usermapping_flag = 1
                    # print('user_mapping',usermapping_flag)
                    serializer_usermapping.save()
                except:
                    print(serializer_usermapping.errors)
                    return error_response(success=False,
                                         status_code=status.HTTP_400_BAD_REQUEST,
                                         message= Constants.USER_MAPPING_NOT_CREATED,
                                         message_code=ErrMsgCode.VALIDATION_ERROR,
                                         error_msg= serializer_error_format(serializer_usermapping.errors)
                                         )
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj.user_id)
                if usermapping_flag:
                    user_status_data = {
                        "chat_user_id": usermapping_obj.chat_user_id,
                        "timestamp": datetime.datetime.now()
                        }
                    serializer_userstatus = UserStatusSerializer(data = user_status_data)
                    try:
                        serializer_userstatus.is_valid()
                        serializer_userstatus.save()
                    except:
                        # print(serializer_userstatus.errors)
                        return error_response(success=False,
                                             status_code=status.HTTP_400_BAD_REQUEST,
                                             message=Constants.USER_STATUS_NOT_CREATED,
                                             error_msg=serializer_error_format(serializer_userstatus.errors),
                                             message_code=ErrMsgCode.VALIDATION_ERROR
                                            )
            
            
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK, 
                                message= Constants.OTP_SENT_SUCCESSFULLY,
                                result= serialzed_data.data)
        
        except Exception as err:
            return error_response(success = False,
                                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    message = Constants.INTERNAL_SERVER_ERROR,
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )
        

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
            otp = payload.get('otp', None)
           
            phone_number = payload.get('phone_number', None)
            
            # if phone_number is None or device_id is None or device_token is None or device_type is None or otp is None:
            #     return json_response(success = False, 
            #                         status_code=status.HTTP_400_BAD_REQUEST,
            #                         message= Constants.PAYLOAD_MISSING)
            
            
            user_obj = None
            try:
                user_obj = User.objects.get(phone_number=phone_number)
            except:
                return error_response(success=False,
                                     status_code=status.HTTP_404_NOT_FOUND,
                                     message=Constants.OTP_NOT_VERIFIED,
                                     error_msg=ErrMsg.USER_NOT_FOUND,
                                     message_code=ErrMsgCode.USER_NOT_FOUND
                                    )
            if otp != config('OTP'):
                return error_response(success = False,
                                     status_code = status.HTTP_403_FORBIDDEN,
                                     message= Constants.WRONG_OTP,
                                     message_code= ErrMsgCode.WRONG_OTP,
                                     error_msg=ErrMsg.WRONG_OTP
                                
                                     )
            token = get_tokens_for_user(user_obj)
            session_data = {
                'chat_user_id': user_obj.user_id,
                'device_id':  device_id, 
                'device_token': device_token, 
                'device_type':   device_type,
                'jwt_token': token['refresh'],
                'deleted_at': None,
            }
            try:
                # session_obj = Session.objects.get(user_id = user_obj.id, device_id = device_id)
                #if device_id already exists 
                session_obj = Session.objects.get( device_id = device_id)
                
                serializer_session = SessionSerializer(instance=session_obj,data=session_data,partial=True)
                try: 
                    serializer_session.is_valid()
                    # print('ii')
                    serializer_session.save()
                except:
                    return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message= Constants.UNSUCCESSFULL , 
                                    message_code= ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= serializer_error_format(serializer_session.errors)
                                    )

            except Session.DoesNotExist:
                #if session does not exist then create one
            
                serializer_session = SessionSerializer(data=session_data)
                try: 
                    serializer_session.is_valid()
                    serializer_session.save()
                except:
                    return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message= Constants.SESSION_NOT_UPDATED , 
                                    error_msg= serializer_error_format(serializer_session.errors),
                                    message_code=ErrMsgCode.VALIDATION_ERROR
                                    )
            return json_response(success=True,
                                status_code=status.HTTP_200_OK,
                                message=Constants.OTP_VERIFIED,
                                result={'token': token})

        
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

class UserProfile(APIView):
    
    permission_classes = [ApiKey, IsAuthenticated]
    def get(self, request):
        '''
        APi for getting particular user details
        '''
        try:
            payload = request.data
            user_obj = request.user
            user_id = request.user.user_id
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            chat_user_id = usermapping_obj.chat_user_id
            userstatus_obj = None
            try:
                userstatus_obj = UserStatus.objects.get(chat_user_id = chat_user_id)
            except UserStatus.DoesNotExist:
                return error_response(success=False, 
                                        status_code=status.HTTP_404_NOT_FOUND, 
                                        message= Constants.USER_NOT_FOUND, 
                                        result={}, 
                                        message_code= ErrMsgCode.USER_NOT_FOUND,
                                        error_msg= ErrMsg.USER_NOT_FOUND
                                        )

            serializer = None
            if user_id is not None:
                try:
                    # user_obj = User.objects.get(id=id)
                    # serializer = UserSerializer(user_obj)
                    serializer = UserstatuswithprofileSerializer(userstatus_obj)
                except User.DoesNotExist:
                    return error_response(success=False, 
                                        status_code=status.HTTP_404_NOT_FOUND, 
                                        message= Constants.USER_NOT_FOUND, 
                                        result={}, 
                                        message_code= ErrMsgCode.USER_NOT_FOUND,
                                        error_msg= ErrMsg.USER_NOT_FOUND
                                        )
            
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message= Constants.USER_DETAILS,
                                result = serializer.data)
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
        
    def put(self, request):
        '''
        api to update user profile
        '''
        try:
            payload = request.data
            user_id = request.user.user_id
            user_obj = request.user
    
            # print(user_obj.profile_picture, "---")
            user_data = {
                "username": payload.get('username', user_obj.username),
                # "profile_picture": payload.get('profile_picture', user_obj.profile_picture)
            }
            
            # serializer_user = RegisterSerializer(instance=user_obj,data=data, partial= True)
            serializer_user = UserSerializer(instance=user_obj,data= user_data, partial= True)
            
            if serializer_user.is_valid():
                serializer_user.save()
            else:
                return error_response(success=False,
                                     status_code=status.HTTP_400_BAD_REQUEST,
                                     message=Constants.UPDATE_UNSUCCESSFULL,
                                     message_code=ErrMsgCode.VALIDATION_ERROR,
                                     error_msg=serializer_error_format(serializer_user.errors)
                                    )
            
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message= Constants.UPDATE,
                                result=serializer_user.data )
        
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
  
class PrivacySettings(APIView):
    '''
    Apis for getting privacy settings details and updating privacy settings details
    '''
    permission_classes = [ApiKey, IsAuthenticated ]
    def get(self, request):
        '''
        Api for getting the privacy settings of particular user
        '''
        try:
            user_id = request.user.user_id
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            chat_user_id = usermapping_obj.chat_user_id
            serializer = None
            privacy_obj = None
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id )
               
            except Privacy.DoesNotExist:
               
                privacy_data = {"chat_user_id": chat_user_id}
                serializer = PrivacySerializer(data = privacy_data)
                try:
                    serializer.is_valid()
                  
                    serializer.save()
                    return json_response(success=True,
                                         status_code=status.HTTP_200_OK,
                                         result=serializer.data,
                                         message=Constants.DETAILS
                                         )
                except:
                    return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.CREATE_UNSUCCESFFULL,
                                    message_code=ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= serializer_error_format(serializer.errors)
                                    )
            
            serializer =  PrivacySerializer(privacy_obj)
            return json_response(success=True,
                                         status_code=status.HTTP_200_OK,
                                         result=serializer.data,
                                         message=Constants.DETAILS)
        
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
    def put(self, request):
        '''
        Api for updating the privacy settings of particular user
        '''
        try:
            payload = request.data
            user_id = request.user.user_id
            usermapping_obj = UsersMapping.objects.get(app_user_id = user_id)
            chat_user_id = usermapping_obj.chat_user_id
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id)
            except:
                return error_response(success=False,
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.UPDATE_UNSUCCESSFULL,
                                    message_code=ErrMsgCode.USER_NOT_FOUND,
                                    error_msg= ErrMsg.USER_NOT_FOUND)
           
            serializer = PrivacySerializer(instance=privacy_obj,data= payload,partial=True)
            try:
                serializer.is_valid()
                serializer.save()
            except:
                return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.UPDATE_UNSUCCESSFULL, 
                                    error_msg=serializer_error_format(serializer.errors),
                                    message_code= ErrMsgCode.VALIDATION_ERROR
                                    )
            return json_response(status_code=status.HTTP_200_OK,
                                 message= Constants.UPDATE, 
                                 result=serializer.data)
            
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
                return error_response(success = False,
                                         status_code = status.HTTP_400_BAD_REQUEST,
                                        #  message = Constants.,
                                         error_msg= ErrMsg.REFRESH_TOKEN_MISSING,
                                         message_code=ErrMsgCode.PAYLOAD_INCORRECT
                                        )
            try:
                refresh_token_object = RefreshToken(refresh_token)
            except Exception as err:
                return error_response(success=False,
                                      message= Constants.CANT_CREATE_REFRESH_TOKEN,
                                      status_code= status.HTTP_400_BAD_REQUEST,
                                      error_msg= str(err),
                                      message_code=ErrMsgCode.BLACKLISTED_TOKEN              
                )
            access_token = refresh_token_object.access_token
            return json_response(success = True,
                                     status_code = status.HTTP_200_OK,
                                     message = Constants.SUCCESSFULL,
                                     result = {"refresh": str(refresh_token),
                                               "access": str(access_token)},
                                     )
        
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




class Logout(APIView):
    '''
        Api for Logout collect user_id, device_id and remove that particular session
    '''
    permission_classes = [ApiKey, IsAuthenticated]
    def post(self, request):
        
        try:
            payload = request.data
            user_id = request.user.user_id
            
            device_id = payload.get('device_id', None)
            if device_id is None:
                return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.PAYLOAD_MISSING,
                                    error_msg=ErrMsg.DEVICE_ID_MISSING,
                                    message_code=ErrMsgCode.PAYLOAD_MISSING
                                    )
            try:
                session_obj = Session.objects.get(chat_user_id = user_id, device_id = device_id)
                # session_obj.delete()
                session_obj.deleted_at = datetime.datetime.now()
                session_obj.save()
            except:
                return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.SESSION_NOT_FOUND,
                                    message_code= ErrMsgCode.SESSION_NOT_FOUND,
                                    error_msg=ErrMsg.SESSION_NOT_FOUND
                                    )
            
            refresh_token = session_obj.jwt_token
           
            RefreshToken(refresh_token).blacklist()

            # RefreshToken(refresh_token).blacklist()
            return json_response(status_code=status.HTTP_200_OK,message= Constants.LOGOUT)
        
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
