from channels.consumer import SyncConsumer

class MySyncConsumer(SyncConsumer):
    def websocket_connect(self, event):
        print('Websocket connected',event)
        self.send({
            'type':'websocket.accept'
        })

    def websocket_receive(self, event):
        print('Message Received',event)

    def websocket_disconnect(self, event):
        print('websocket disconnected',event)