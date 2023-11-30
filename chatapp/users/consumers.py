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
        print(event)
        print('Message Received',event['text'])
        print('Type of Message Received', type(event['text']))
        async_to_sync(self.channel_layer.group_send)('group_name', {
            'type': 'chat.message',
            'message': event['text'],
            'msg': 'one-to-one chat'
        })
    
    def chat_message(self, event):
        print('EVENT .........', event)
        print('actual data.......', event['message'])
        dict = {'type': 'websocket.send'}
        dict['text'] = ''
        # for key, value in event.items():
        #     print(key,value)
        #     if key != 'type':
        #         dict['text'] += value
        # print(dict)
        # self.send(dict)
        self.send({
            'type': 'websocket.send',
            'text': event['message'],
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
        print('Websocket connected',event)
        print('channel layer----------------',self.channel_layer)# get default
        print('channel_name', self.channel_name)#get channel name
        print(self.scope)
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        #add a channel to a new or existing group
        await self.channel_layer.group_add(
            # 'group_name', #group name
            self.group_name,
             self.channel_name)
        await self.send({
            'type':'websocket.accept'
        })

    async def websocket_receive(self, event):
        print(event)
        print('Message Received',event['text'])
        print('Type of Message Received', type(event['text']))
        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat.message',
            'message': event['text'],
            'msg': 'one-to-one chat'
        })
    
    async def chat_message(self, event):
        print('EVENT .........', event)
        print('actual data.......', event['message'])
        dict = {'type': 'websocket.send'}
        # dict['text'] = ''
        # for key, value in event.items():
        #     print(key,value)
        #     if key != 'type':
        #         dict['text'] += value
        # print(dict)
        # self.send(dict)
        await self.send({
            'type': 'websocket.send',
            'text': event['message'],
        })
    async def websocket_disconnect(self, event):
        print('websocket disconnected',event)
        print('channel layer------', self.channel_layer)
        print('channel name------', self.channel_name)
        await self.channel_layer.group_discard(
            self.group_name,#group_name
            self.channel_name
        )
        # raise StopConsumer()

