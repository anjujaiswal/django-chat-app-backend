from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
# from utils.helpers import json_response
import json
from rest_framework import status
import uuid
import time
def json_response(success=True, status_code=status.HTTP_200_OK, message='', result={}, error={}):
    """this function is the structured Response """
    return Response({
        'success': success, 
        'status_code': status_code, 
        'message': message, 
        'result': result,
        'error': error,
        # 'timestamps': time.time()
    },
    status=status_code)

def error_response(success=True, status_code=status.HTTP_200_OK, message='', result={}, error_msg = '',message_code=''):
    """this function is the structured error Response """
    return Response({
        'success': success, 
        'status_code': status_code, 
        'message': message, 
        'result': result,
        'error': {
            'message': error_msg,
            'message_code': message_code
        }
    },
    status=status_code)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # print("refresh: ", refresh)

    return {
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),

    }

def serializer_error_list(datas):
    '''
        This function is used to return single error message if field validation got failed
        if serializer.error is list
    '''
    data = json.loads(json.dumps(datas))
    resp = []
    print(datas)
    for data in datas:
        print(data)
        for key, value in data.items():
            resp.append(f"{key}: {value[0]}")
    if resp:
        return resp[-1]
    else:
        return "Unable to detect exact error"
    
def serializer_error_format(data):
    '''
        This function is used to return single error message if field validation got failed
    '''
    data = json.loads(json.dumps(data))
    resp = []
    # print(data,"hhh")
    for key, value in data.items():
        # print(key)
        resp.append(f"{key}: {value[0]}")
        if str(key) == 'phone_number':
            resp.append('Please enter valid phone number')
        if str(key) == 'device_type':
            resp.append('Invalid device type')
        if str(key) == 'last_seen_visibility':
            resp.append('Invalid last_seen_visibility')
        if str(key) == 'profile_picture_visibility':
            resp.append('Invalid profile_picture_visibility')
        if str(key) == 'status_visibility':
            resp.append('Invalid status_visibility')
        if str(key) == 'message_receipts':
            resp.append('Invalid message_receipts')
    if resp:
        return resp[-1]
    else:
        return "Unable to detect exact error"
    
def search_list_of_dicts(data, search_value, keys):
    """
    Search for a case-insensitive substring in a list of dictionaries based on specified keys.

    Parameters:
    - data: List of dictionaries to search.
    - search_value: The value to search for.
    - keys: List of keys to check for the search value.

    Returns:
    - List of dictionaries containing the case-insensitive substring in any of the specified keys.
    """
    result = []

    search_value_lower = search_value.lower()  # Convert search value to lowercase for case-insensitive comparison

    for item in data:
        for key in keys:
            if key in item and item[key] and search_value_lower in item[key].lower():
                result.append(item)
                break  # Break the inner loop if a match is found in any key

    return result
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

def token_authorization(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    # print(token)
    
    if token:
        token = token.replace('Bearer ', '')
    # print(token)
    return token == None