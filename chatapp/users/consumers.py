from channels.consumer import SyncConsumer, AsyncConsumer
from time import sleep
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync

class MySyncConsumer(SyncConsumer):
    def websocket_connect(self, event):
        print('Websocket connected',event)
        print('channel layer----------------',self.channel_layer)# get default
        print('channel_namezzzzzzzzzzz', self.channel_name)#get channel name
        #add a channel to a new or existing group
        async_to_sync(self.channel_layer.group_add)(
            'group_name', #group name
             self.channel_name)
        self.send({
            'type':'websocket.accept'
        })

    def websocket_receive(self, event):
        print('Message Received',event['text'])
        print('Type of Message Received', type(event['text']))
        async_to_sync(self.channel_layer.group_send)('group_name', {
            'type': 'chat.message',
            'message': event['text']
        })
    
    def chat_message(self, event):
        print('EVENT .........', event)
        print('actual data.......', event['message'])
        self.send({
            'type': 'websocket.send',
            'text': event['message']
        })
    def websocket_disconnect(self, event):
        print('websocket disconnected',event)
        print('channel layer------', self.channel_layer)
        print('channel name------', self.channel_name)
        async_to_sync(self.channel_layer.group_discard)(
            'group_name',
            self.channel_name
        )
        # raise StopConsumer()




class MyAsyncConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        # print('Websocket connected',event)
        await self.send({
            'type':'websocket.accept'
        })

    async def websocket_receive(self, event):
        # print('Message Received',event)
        print(event['text'])
        # for i in range(10):
        #     await self.send({
        #         'type': 'websocket.send',
        #         'text': str(i)
        #     })
        #     sleep(1)

    async def websocket_disconnect(self, event):
        print('websocket disconnected',event)
