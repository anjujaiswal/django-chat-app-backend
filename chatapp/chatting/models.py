# from django.db import models

# # Create your models here.
# from accounts.models import Account
# import uuid
# from django.utils import timezone


# class Chat(models.Model):
#     initiator = models.ForeignKey(
#         Account, on_delete=models.DO_NOTHING
#     )
#     acceptor = models.ForeignKey(
#         Account, on_delete=models.DO_NOTHING
#     )
#     short_id = models.CharField(max_length=255, default=uuid.uuid4, unique=True)


# class ChatMessage(models.Model):
#     chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
#     sender = models.ForeignKey(Account, on_delete=models.DO_NOTHING)
#     text = models.TextField()
#     created_at = models.DateTimeField(default=timezone.now)