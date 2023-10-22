from django.urls import path,include
from users import views, chatroom, contacts

urlpatterns = [
    # path('accounts/register/',views.Register.as_view()),
    # path('register', views.Register.as_view()),

#----------------------------auth-----------------------------------------
    path('login/', views.AddUser.as_view()),
    path('verifyotp/', views.VerifyOtp.as_view() ),
    path('logout/', views.Logout.as_view()),
    path('refresh/', views.RefreshTokenApi.as_view()),
 
#--------------------------privacy---------------------------------
    
    path('privacy/', views.PrivacyGet.as_view()),
    path('privacyUpdate/', views.PrivacyUpdate.as_view()),
    
#-----------------contacts-----------------------------    
    # path('contactsync/', contacts.ContactSync.as_view()),
    path('contactsync/', contacts.ContactSyncser.as_view()),
    # path('contactUpdate/',contacts.ContactUpdate.as_view()),
    path('contactUpdate/',contacts.ContactUpdate.as_view()),
    path('contactlist/', contacts.GetContactList.as_view()),

#-----------------users-----------------------------------
    path('update/', views.Update.as_view()),
    path('details/', views.UserDetail.as_view()),

#--------------------block --------------------------------
    path('block/', contacts.BlockUser.as_view()),
    path('blockDetails/', contacts.BlockDetails.as_view()),

#-------------------chatroom apis---------------------------
    path('addgroup/', chatroom.AddGroup.as_view())
    
    # path('list', views.UserApi.as_view()),
]
