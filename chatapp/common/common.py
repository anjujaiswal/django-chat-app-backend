from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
import uuid
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

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