
from django.urls import path,include
from users import views, chatroom, contacts, recent_chats

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework import permissions
schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    # path('accounts/register/',views.Register.as_view()),
    # path('register', views.Register.as_view()),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   
#----------------------------auth-----------------------------------------
    path('login', views.AddUser.as_view()),
    path('verify-otp', views.VerifyOtp.as_view() ),
    path('logout', views.Logout.as_view()),
    path('refresh-session', views.RefreshTokenApi.as_view()),#refreshsession
 
#--------------------------privacy---------------------------------
    
    path('privacy-settings', views.PrivacySettings.as_view()), #getprivacy
    
#-----------------contacts-----------------------------    
    # path('contactsync/', contacts.ContactSync.as_view()),
    path('contacts', contacts.Contacts.as_view()),#contactsync
    
#-----------------users-----------------------------------
    path('profile', views.UserProfile.as_view()), #updateuserdetails and get
   
#--------------------block --------------------------------
    # path('contacts/block/', contacts.BlockUser.as_view()), #blockuser
    path('block', contacts.BlockUser.as_view()), #getblockedlist

#-------------------chatroom apis---------------------------
    path('chat-room', chatroom.AddGroup.as_view()), #createroom
    path('admin', chatroom.GiveAdminRights.as_view()), #to grant admin access
    path('remove', chatroom.RemoveMember.as_view()), #removefromgroup
    path('leave', chatroom.LeaveGroup.as_view()),
    path('members/<uuid:room_id>', chatroom.GroupMembersApi.as_view()),#add member in existing group


#--------------------recent_chats apis -------------------------------------------
    # path('recent-chats', recent_chats.RecentChats.as_view()),
    path('recent-chats', recent_chats.RecentChatsNew.as_view()),
    path('message-history',recent_chats.MessageHistoryApis.as_view()),
    path('message-info', recent_chats.MessageInfo.as_view())
   ]

