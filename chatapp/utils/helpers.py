from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
# from utils.helpers import json_response

from rest_framework import status
import uuid

def json_response(success=True, status_code=status.HTTP_200_OK, message='', result={}, error={}):
    """this function is the structured Response """
    return Response({
        'success': success, 
        'status_code': status_code, 
        'message': message, 
        'result': result,
        'error':error
    })

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # print("refresh: ", refresh)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),

    }

from rest_framework.permissions import BasePermission

class ApiKey(BasePermission):
    def has_permission(self, request, view):

        api_key_secret = request.headers.get('X-API-KEY')
        # print("api_key_secret: ", api_key_secret)

        return api_key_secret == config('API_KEY_SECRET') 
        # if not (api_key_secret == config('API_KEY_SECRET')  ):
        #     return json_response(success=False,
        #                         status_code= status.HTTP_401_UNAUTHORIZED,
        #                         )


def get_user_id_from_tokens(refresh_token, access_token):
    try:
        refresh = RefreshToken(refresh_token)
        user_id = refresh.payload['user_id']
        return user_id
    except Exception as e:
        # Handle any exceptions that may occur (e.g., token is invalid)
        return None
    

def genUUID():
    uuid = uuid.uuid4()
    return uuid

def api_key_authorization(request):
    api_key_secret = request.headers.get('X-API-KEY')
    print(api_key_secret,config('API_KEY_SECRET'))
    # print("api_key_secret: ", api_key_secret)

    return api_key_secret == config('API_KEY_SECRET') 
    # if not (api_key_secret == config('API_KEY_SECRET')  ):
    #     return json_response(success=False,
    #                         status_code= status.HTTP_401_UNAUTHORIZED,
    #                         )

def token_authorization(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    # print(token)
    
    if token:
        token = token.replace('Bearer ', '')
    # print(token)
    return token == None