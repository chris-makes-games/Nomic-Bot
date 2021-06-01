import asyncio
import websockets
import uuid
import json
import sheets
import os


user_id = os.environ['twitch_user']
oauth = os.environ['twitch_oauth']
token = os.environ['twitch_token']
secret = os.environ['twitch_secret']
app_id = os.environ['twitch_app_id']


class TwitchClient:

    def __init__(self):
        # list of topics to subscribe to. oauth used as token
        self.topics = ["channel-points-channel-v1." + user_id]
        self.auth_token = token
        pass

    async def connect(self):
        # connect to server and wait for reply
        self.connection = await websockets.client.connect('wss://pubsub-edge.twitch.tv')
        if self.connection.open:
            print('Connected to Twitch')
            print('--------------------')
            # Send greeting
            message = {"type": "LISTEN", "nonce": str(self.generate_nonce()), "data":{"topics": self.topics, "auth_token": self.auth_token}}
            json_message = json.dumps(message)
            await self.sendMessage(json_message)
            return self.connection

    def generate_nonce(self):
        # Generate pseudo-random number and seconds since epoch (UTC).
        nonce = uuid.uuid1()
        oauth_nonce = nonce.hex
        return oauth_nonce

    async def sendMessage(self, message):
        # message sent to websocket server
        await self.connection.send(message)

    async def receiveMessage(self, connection):
        # recieves message back from server, sends to handler
        while True:
            try:
                message = await connection.recv()
                jmessage = json.loads(message)
                if jmessage["type"] == "RESPONSE":
                    pass
                elif jmessage["type"] == "PONG":
                    # print("Pong received")
                    pass
                else:
                    s = str(jmessage["data"]["message"])
                    s = json.loads(s)
                    username = str(s["data"]["redemption"]["user"]["display_name"])
                    reward = str(s["data"]["redemption"]["reward"]["title"])
                    print(username + " just redeemed " + reward)
                    if reward == "Nomic Point":
                        sheets.new_user(username)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break
            except Exception as exp:
                print("Error: " + str(exp))

    async def heartbeat(self, connection):
        # ping -pong to keep connection live to server
        while True:
            try:
                data_set = {"type": "PING"}
                json_request = json.dumps(data_set)
                # print('Sending Ping...')
                await connection.send(json_request)
                await asyncio.sleep(60)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break

if __name__ == '__main__':
  # Creating client object
  client = TwitchClient()
  loop = asyncio.get_event_loop()
  # Start connection and get client connection protocol
  connection = loop.run_until_complete(client.connect())
  # Start listener and heartbeat
  tasks = [
        asyncio.ensure_future(client.heartbeat(connection)),
        asyncio.ensure_future(client.receiveMessage(connection)),
    ]

  loop.run_until_complete(asyncio.wait(tasks))