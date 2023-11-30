from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from chatting.serializers import ChatSerializer
from chatting.models import Chat
from users.models import User
import uuid



class GetChat(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSerializer

    def get(self, request):
        print("request.user.id: ", request.user.id)
        print("request.user.email: ", request.user.email)
        acceptor = request.query_params.get('acceptor', None)
        initiator_obj = Account.objects.get(id=request.user.id)
        acceptor_obj = Account.objects.get(id=acceptor)
        # print("account_obj: ", account_obj)
        chat, created = Chat.objects.get_or_create(initiator=initiator_obj, acceptor=acceptor_obj)
        print("chat: ", chat)
        print("created: ", created)
        serializer = self.serializer_class(instance=chat)
        return Response({"message": "Chat gotten", "data": serializer.data}, status=status.HTTP_200_OK)