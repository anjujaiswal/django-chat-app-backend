from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import User,UserStatus, Session, ContactList, Privacy,UsersMapping
from .serializers import UserSerializer, UserstatuswithprofileSerializer,UserStatusSerializer, RegisterSerializer,UsersMappingSerializer, LoginSerializer, ContactListSerializer, PrivacySerializer, SessionSerializer
from .serializers import UserProfileSerializer, Userstatusprofileserializer
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
import re
import logging
logger_error = logging.getLogger('error_logger')
logger_info = logging.getLogger('info_logger')
class AddUser(APIView):
    '''
    Api user does not exits first register(with default user status)  add a entry in usermapping table 
    '''
    permission_classes = [ApiKey]
    
    def post(self,request):

        try:
            #payload data
            payload = request.data
            country_code = payload.get('country_code', None)
            phone_number = payload.get('phone_number', None)
            # print(phone_number)
            if phone_number is None:
                return error_response(
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message= Constants.PHONE_NUMBER_MISSING,
                    error_msg=ErrMsg.VALIDATION_ERROR,
                    message_code=ErrMsgCode.VALIDATION_ERROR
                )
            if country_code is None:
                return error_response(
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message= Constants.COUNTRY_CODE_MISSING,
                    error_msg=ErrMsg.VALIDATION_ERROR,
                    message_code=ErrMsgCode.VALIDATION_ERROR
                )
            phone_number_pattern = r'^\d{7,15}$'
            country_code_pattern = r'^\+\d{1,3}$'
            if  not re.match(phone_number_pattern, phone_number) or not re.match(country_code_pattern, country_code):
                return error_response(
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message= Constants.INVALID_PHONE,
                    error_msg=ErrMsg.VALIDATION_ERROR,
                    message_code=ErrMsgCode.VALIDATION_ERROR
                )
            #flag variable is used to know that wheather the user is created for the first time or already present
            flag = 0
            #to check whether the row has been created for rhe usermapping table for corresponding user
            usermapping_flag = 0
            
            user_data = {
                    'phone_number': phone_number,
                    'country_code': country_code
                    }
            
            serializer_register = None
            
            user_obj = User.objects.filter(phone_number = phone_number, country_code = country_code)
            
            if len(user_obj) == 0:
                #for the first time user register it in the user table
                serializer_register = UserSerializer(data=user_data)
                try:
                    serializer_register.is_valid()
                    flag = 1
                    serializer_register.save()
                except :
                    return error_response(success=False,
                                status_code=status.HTTP_400_BAD_REQUEST, 
                                message= serializer_error_format(serializer_register.errors), 
                                error_msg= serializer_error_format(serializer_register.errors),
                                message_code= ErrMsgCode.VALIDATION_ERROR
                                 )
            try:
                user_obj = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.USER_NOT_FOUND,
                                      message=Constants.USER_NOT_FOUND,
                                      message_code= ErrMsgCode.USER_NOT_FOUND)
            serialzed_data = UserSerializer(user_obj)
            #for first time user we create the row for usermapping table - if  flag = 1
            if flag:
                usersmapping_data = { "app_user_id":  user_obj.user_id}
                serializer_usermapping = UsersMappingSerializer(data = usersmapping_data)
                try: 
                    serializer_usermapping.is_valid()
                    #creating the row in usersmapping table so usermapping_flag helps to know
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
                try:
                    usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj.user_id)
                except:
                    return error_response(success=False,
                                          status_code=status.HTTP_400_BAD_REQUEST,
                                          message=Constants.USERMAPPING_NOT_FOUND,
                                          error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                          message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                          )
                if usermapping_flag:
                    # creating the row for user_status for the first time user
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
            country_code = payload.get('country_code', None)
            phone_number = payload.get('phone_number', None)
            #checking payload
            if phone_number is None or device_id is None or device_token is None or device_type is None or otp is None or country_code is None:
                return error_response(success = False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.PAYLOAD_MISSING,
                                    message_code=ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= ErrMsg.VALIDATION_ERROR)
            
            phone_number_pattern = r'^\d{7,15}$'
            country_code_pattern = r'^\+\d{1,3}$'
            if not re.match(phone_number_pattern, phone_number) or not re.match(country_code_pattern, country_code):
                return error_response(
                    success=False,
                    message= Constants.INVALID_PHONE,
                    error_msg=ErrMsg.VALIDATION_ERROR,
                    message_code=ErrMsgCode.VALIDATION_ERROR
                )
            # user_obj = None
            try:
                user_obj = User.objects.get(phone_number=phone_number, country_code= country_code)
            except:
                return error_response(success=False,
                                     status_code=status.HTTP_404_NOT_FOUND,
                                     message=Constants.USER_NOT_FOUND,
                                     error_msg=ErrMsg.USER_NOT_FOUND,
                                     message_code=ErrMsgCode.USER_NOT_FOUND
                                    )
            # print('user_obj',user_obj)
            if otp != config('OTP'):
                return error_response(success = False,
                                     status_code = status.HTTP_400_BAD_REQUEST,
                                     message= Constants.WRONG_OTP,
                                     message_code= ErrMsgCode.WRONG_OTP,
                                     error_msg=ErrMsg.WRONG_OTP
                                
                                     )
            #creating token for user_obj
            token = get_tokens_for_user(user_obj)
            try:
                usermapping_obj = UsersMapping.objects.get(app_user_id = user_obj)
            except:
                return error_response(success=False,
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        message=Constants.USERMAPPING_NOT_FOUND,
                                        error_msg=ErrMsg.USERMAPPING_NOT_FOUND,
                                        message_code=ErrMsgCode.USERMAPPING_NOT_FOUND
                                        )
            session_data = {
                'chat_user_id': usermapping_obj.chat_user_id,
                'device_id':  device_id, 
                'device_token': device_token, 
                'device_type':   device_type,
                'jwt_token': token['refresh_token'],
                'deleted_at': None,
            }
            try:
                #if device_id already exists in session 
                session_obj = Session.objects.get( device_id = device_id)
                
                serializer_session = SessionSerializer(instance=session_obj,data=session_data,partial=True)
                try: 
                    serializer_session.is_valid()
                    serializer_session.save()
                except:
                    return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST, 
                                    message= serializer_error_format(serializer_session.errors) , 
                                    message_code= ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= ErrMsg.VALIDATION_ERROR
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
                                    message= serializer_error_format(serializer_session.errors) , 
                                    message_code= ErrMsgCode.VALIDATION_ERROR,
                                    error_msg= ErrMsg.VALIDATION_ERROR
                                    )
            user_details = UserProfileSerializer(user_obj).data
            try:
                user_status_obj = UserStatus.objects.get(chat_user_id = usermapping_obj )
            except: 
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      message=Constants.USER_STATUS_NOT_FOUND,
                                      error_msg=ErrMsg.USER_STATUS_NOT_FOUND,
                                      message_code=ErrMsgCode.USER_STATUS_NOT_FOUND)
            
            user_details['status_quotes'] = user_status_obj.status_quotes
            user_details['chat_user_id'] = usermapping_obj.chat_user_id
            # logger_info.info('verify-otp api')
            return json_response(success=True,
                                status_code=status.HTTP_200_OK,
                                message=Constants.LOGIN_SUCCESSFULL,
                                result= {
                                    'user_details':user_details,
                                    'token': token
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
                                    result = {},
                                    message_code=ErrMsgCode.INTERNAL_SERVER_ERROR,
                                    error_msg= str(err)
                                    )

class UserProfile(APIView):
    '''APis for the getting the user profile and updating it'''
    permission_classes = [ApiKey, IsAuthenticated]
    def get(self, request):
        '''
        APi for getting particular user details
        '''
        try:
            user_obj = request.user
            user_id = request.user.user_id
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
            # userstatus_obj = None
            try:
                userstatus_obj = UserStatus.objects.get(chat_user_id = chat_user_id)
            except UserStatus.DoesNotExist:
                return error_response(success=False, 
                                        status_code=status.HTTP_404_NOT_FOUND, 
                                        message= Constants.USER_STATUS_NOT_FOUND, 
                                        result={}, 
                                        message_code= ErrMsgCode.USER_STATUS_NOT_FOUND,
                                        error_msg= ErrMsg.USER_STATUS_NOT_FOUND
                                        )
            serializer_user = UserProfileSerializer(user_obj)
            serializer_user_status = Userstatusprofileserializer(userstatus_obj)
               
            # if user_id is not None:
            #     try:
            #         # user_obj = User.objects.get(id=id)
            #         # serializer = UserSerializer(user_obj)
            #         # serializer = UserstatuswithprofileSerializer(userstatus_obj)
            #         serializer_user_status = Userstatusprofileserializer(userstatus_obj)
            #     except User.DoesNotExist:
            #         return error_response(success=False, 
            #                             status_code=status.HTTP_404_NOT_FOUND, 
            #                             message= Constants.USER_NOT_FOUND, 
            #                             result={}, 
            #                             message_code= ErrMsgCode.USER_NOT_FOUND,
            #                             error_msg= ErrMsg.USER_NOT_FOUND
            #                             )
            user_data = {
            }
            user_data.update(serializer_user.data )
            user_data.update(serializer_user_status.data)
            # logger_info.info('profile -get api')
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message= Constants.USER_DETAILS,
                                result = user_data)
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
        
    def put(self, request):
        '''
        api to update user profile
        '''
        try:
            payload = request.data
            user_id = request.user.user_id
            user_obj = request.user
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
            # print(user_obj.profile_picture, "---")
            user_data = {
                "username": payload.get('username', user_obj.username),
                "profile_picture": payload.get('profile_picture', user_obj.profile_picture)
            }
            try:
                user_status_obj = UserStatus.objects.get(chat_user_id = chat_user_id)
            except UserStatus.DoesNotExist:
                return error_response(success=False, 
                                        status_code=status.HTTP_404_NOT_FOUND, 
                                        message= Constants.USER_STATUS_NOT_FOUND, 
                                        result={}, 
                                        message_code= ErrMsgCode.USER_STATUS_NOT_FOUND,
                                        error_msg= ErrMsg.USER_STATUS_NOT_FOUND
                                        )
            user_status_data = {
                "status_quotes": payload.get('status_quotes', user_status_obj.status_quotes),
            }
            serializer_user = UserProfileSerializer(instance=user_obj,data= user_data, partial= True)
            serializer_user_status = UserStatusSerializer(instance= user_status_obj, data = user_status_data, partial = True)
            if serializer_user.is_valid():
                serializer_user.save()
            else:
                return error_response(success=False,
                                     status_code=status.HTTP_400_BAD_REQUEST,
                                     message=Constants.UPDATE_UNSUCCESSFULL,
                                     message_code=ErrMsgCode.VALIDATION_ERROR,
                                     error_msg=serializer_error_format(serializer_user.errors)
                                    )
            if serializer_user_status.is_valid():
                serializer_user_status.save()
            else:
                print(serializer_user_status.errors)
                return error_response(success=False,
                                     status_code=status.HTTP_400_BAD_REQUEST,
                                     message=Constants.UPDATE_UNSUCCESSFULL,
                                     message_code=ErrMsgCode.VALIDATION_ERROR,
                                     error_msg=serializer_error_format(serializer_user.errors)
                                    )
            
            user_data = {}
            user_data.update(serializer_user.data )
            user_data.update(serializer_user_status.data)
            # logger_info.info('profile -put api')
            return json_response(success=True, 
                                status_code=status.HTTP_200_OK,
                                message= Constants.PROFILE_UPDATE,
                                # result=data 
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
            # print('chat____',chat_user_id)
            # serializer = None
            # privacy_obj = None
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id )
               
            except Privacy.DoesNotExist:
               
                privacy_data = {"chat_user_id": chat_user_id}
                serializer = PrivacySerializer(data = privacy_data)
                try:
                    serializer.is_valid()
                  
                    serializer.save()
                    logger_info.info('privacy-settings - get api')
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
            logger_info.info('privacy-settings - get api')
            return json_response(success=True,
                                         status_code=status.HTTP_200_OK,
                                         result=serializer.data,
                                         message=Constants.DETAILS)
        
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
    def put(self, request):
        '''
        Api for updating the privacy settings of particular user
        '''
        try:
            payload = request.data
            user_id = request.user.user_id
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
            try:
                privacy_obj = Privacy.objects.get(chat_user_id = chat_user_id)
            except:
                return error_response(success=False,
                                    status_code=status.HTTP_404_NOT_FOUND,
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
                                    message= serializer_error_format(serializer.errors), 
                                    error_msg= ErrMsg.VALIDATION_ERROR,
                                    message_code= ErrMsgCode.VALIDATION_ERROR
                                    )
            logger_info.info('privacy-getting -- put api')
            return json_response(status_code=status.HTTP_200_OK,
                                 message= Constants.PRIVACY_UPDATE, 
                                #  result=serializer.data
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
            refresh_token = payload.get("refresh_token", None)
           
            if refresh_token is None:
                return error_response(success=False,
                                      message= Constants.INVALID_TOKEN,
                                      status_code= status.HTTP_401_UNAUTHORIZED,
                                      error_msg= ErrMsg.INVALID_TOKEN,
                                      message_code=ErrMsgCode.INVALID_TOKEN            
                )
            try:
                refresh_token_object = RefreshToken(refresh_token)
            except Exception as err:
                return error_response(success=False,
                                      message= str(err),
                                      status_code= status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.TOKEN_BLACLISTED,
                                      message_code=ErrMsgCode.TOKEN_BLACLISTED,          
                )
            access_token = refresh_token_object.access_token
            logger_info.info('refresh session')
            return json_response(success = True,
                                     status_code = status.HTTP_200_OK,
                                     message = Constants.TOKEN_REFRESHED_SUCESSFULL,
                                     result = {
                                            "access_token": str(access_token)},
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




class Logout(APIView):
    '''
        Api for Logout collect user_id, device_id and remove that particular session
    '''
    permission_classes = [ApiKey, IsAuthenticated]
    def post(self, request):
        
        try:
            payload = request.data
            # user_obj = request.user
            user_id = request.user.user_id
            usermapping_obj = None
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
            # logout = payload.get()
            # device_id = payload.get('device_id', None)
            refresh_token = payload.get('refresh_token', None)
            if refresh_token is None:
                return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message=Constants.PAYLOAD_MISSING,
                                    error_msg=ErrMsg.REFRESH_TOKEN_MISSING,
                                    message_code=ErrMsgCode.PAYLOAD_MISSING
                                    )
            try:
                session_obj = Session.objects.get(chat_user_id = chat_user_id, jwt_token = refresh_token)
                # session_obj.delete()
                # session_obj = Session.objects.get(j = refresh_token)
                
                session_obj.deleted_at = datetime.datetime.now()
                session_obj.save()
            except:
                return error_response(success=False, 
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    message= Constants.SESSION_NOT_FOUND,
                                    message_code= ErrMsgCode.SESSION_NOT_FOUND,
                                    error_msg=ErrMsg.SESSION_NOT_FOUND
                                    )
            
            # refresh_token = session_obj.jwt_token
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception as err:
                return error_response(success=False,
                                      status_code=status.HTTP_400_BAD_REQUEST,
                                      error_msg=ErrMsg.TOKEN_BLACLISTED,
                                      message_code=ErrMsgCode.TOKEN_BLACLISTED,
                                      message=str(err)
                                      )

            # RefreshToken(refresh_token).blacklist()
            logger_info.info('logout api')
            return json_response(status_code=status.HTTP_200_OK,message= Constants.LOGOUT)
        
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
