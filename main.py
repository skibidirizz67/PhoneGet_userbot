from telethon import TelegramClient, events

f = open('api_id.txt', 'r')
api_id = f.read()
f = open('api_hash.txt', 'r')
api_hash = f.read()

me = 5359995738
target = 7808172033

client = TelegramClient('anon', api_id, api_hash)

@client.on(events.NewMessage(from_users=[target]))
async def nm_handler(event):
    print(0)

@client.on(events.NewMessage(outgoing=True, pattern=r'\!'))
async def cmd_handler(event):
    print(1)

client.start()
client.run_until_disconnected()
client.disconnect()