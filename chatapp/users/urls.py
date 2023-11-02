
from django.urls import path,include
from users import views, chatroom, contacts

urlpatterns = [
    # path('accounts/register/',views.Register.as_view()),
    # path('register', views.Register.as_view()),

#----------------------------auth-----------------------------------------
    path('login/', views.AddUser.as_view()),
    path('verify-otp/', views.VerifyOtp.as_view() ),
    path('logout/', views.Logout.as_view()),
    path('refresh-token/', views.RefreshTokenApi.as_view()),#refreshsession
 
#--------------------------privacy---------------------------------
    
    path('privacy-settings/', views.PrivacySettings.as_view()), #getprivacy
    
#-----------------contacts-----------------------------    
    # path('contactsync/', contacts.ContactSync.as_view()),
    path('contacts/', contacts.Contacts.as_view()),#contactsync
    
#-----------------users-----------------------------------
    path('profile/', views.UserProfile.as_view()), #updateuserdetails and get
   
#--------------------block --------------------------------
    # path('contacts/block/', contacts.BlockUser.as_view()), #blockuser
    path('block/', contacts.BlockUser.as_view()), #getblockedlist

#-------------------chatroom apis---------------------------
    path('chat-room/', chatroom.AddGroup.as_view()), #createroom
    path('admin/', chatroom.GiveAdminRights.as_view()), #to grant admin access
    path('remove/', chatroom.RemoveMember.as_view()), #removefromgroup
    path('leave/', chatroom.LeaveGroup.as_view()),
    path('members/', chatroom.GroupMembersApi.as_view()),#add member in existing group
   ]

