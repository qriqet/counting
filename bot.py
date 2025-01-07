# This example requires the 'message_content' intent.

import discord
import json


from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()

f = open("storage.json", "r")
count_info = json.loads(f.read())
f.close()

def dump():
    file = open("storage.json", "w")
    file.write(json.dumps(count_info))
    file.close()


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    print(f'Current count: {count_info["current"]}')

async def wrong(message, reason=None):
    if reason == None:
        await message.channel.send(f'Wrong count, expected {count_info["current"] + 1}. Next count is 1')
    else:
        await message.channel.send(reason +  ' Next count is 1')
    await message.add_reaction("❌")
    count_info["current"] = 0
    count_info["last user"] = ""
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    m = message.content
    # test commands
    if m.startswith('$hello'):
        await message.channel.send('Hello!')
    if m.startswith('$ping'):
        await message.channel.send('Pong!')
    # high score
    if m.startswith('$highscore'):
        await message.channel.send(f'Server high score is: {count_info["high score"]}, counted by {count_info["highest counter"]}')
    
    # admin commands
    if str(message.author) in count_info["admins"]:
        if m.startswith('$setchannel'):
            await message.channel.send(f'counting channel set to: <#{message.channel.id}>')
            count_info["channel"] = int(message.channel.id)
        if m.startswith('$addadmin'):
            username = m[9:].strip()
            if not username in count_info["admins"]:
                count_info["admins"].append(username)
                await message.channel.send(f'set {username} as admin')
            else:
                await message.channel.send(f'{username} is already an admin')
        dump()
 
    #funny
    if m.lower().startswith('is the admin allowed to count consecutively'):
        await message.channel.send('yes, of course they can')

    # actual counting stuff
    if int(message.channel.id) == count_info["channel"] and m.isnumeric():
        if count_info["last user"] == str(message.author) and count_info["last user"] != "computingsquid":
            print(f'last user counted: {count_info["last user"]} user counted: {str(message.author)}')
            await wrong(message, "You can't count twice in a row!")
        elif int(m) == count_info["current"] + 1:
            #if count_info["last user"] == "computingsquid": await message.channel.send('admin is allowed to count consecutively')
            count_info["current"] += 1
            count_info["last user"] = str(message.author)
            if count_info["high score"] < count_info["current"]:
                count_info["high score"] = count_info["current"]
                count_info["highest counter"] = count_info["last user"]
            await message.add_reaction("✅")
        elif count_info["current"] == 0:
            await message.add_reaction("⚠️")
            await message.channel.send('the counting starts at 1!')
        else:
            await wrong(message)
        dump()


client.run(os.getenv('TOKEN'))