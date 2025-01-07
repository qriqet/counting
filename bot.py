# This example requires the 'message_content' intent.

import discord
import json


from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()

f = open("storage.json", "r")
count_info = json.loads(f.read())
g = open("users.json", "r")
user_info = json.loads(g.read())
g.close()
f.close()

def dump():
    file = open("storage.json", "w")
    file.write(json.dumps(count_info))
    file.close()
    file = open("users.json", "w")
    file.write(json.dumps(user_info))
    file.close()


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    print(f'Current count: {count_info["current"]}')

async def wrong(author, message, reason=None):
    if reason == None:
        await message.channel.send(f'Wrong count, expected {count_info["current"] + 1}. Next count is 1')
    else:
        await message.channel.send(reason +  ' Next count is 1')
    await message.add_reaction("❌")
    count_info["current"] = 0
    count_info["last user"] = ""
    user_info[author]["failed"] += 1
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    m = message.content
    author = str(message.author)
    # test commands
    if m.startswith('$hello'):
        await message.channel.send('Hello!')
    if m.startswith('$ping'):
        await message.channel.send('Pong!')
    # help command
    if m.startswith('$help'):
        await message.channel.send("""
        # Don't know how to count?
        
        It's simple. Simply start at 1, and increase like this:
        `1 2 3 4 5`
        By the way, you can't count twice in a row.
        """)
    # high score
    if m.startswith('$highscore'):
        await message.channel.send(f'Server high score is: {count_info["high score"]}, counted by {count_info["highest counter"]}')
    if m.startswith('$currentcount') or m.startswith('$count'):
        await message.channel.send(f'The current count is {count_info["current"]}, counted by {count_info["last user"]}')
    
    ##############
    # USER STUFF #
    ##############

    if m.startswith('$user'):
        user = m[5:].strip()
        await message.channel.send(f'fetching user stats for {user}')
        user_stats = user_info[user]
        await message.channel.send(f'Data: \nTotal counts: {user_stats["counts"]} \nFailed counts: {user_stats["failed"]}\nSlowmode: {user_stats["slowmode"]}s')

    # admin commands
    if author in count_info["admins"]:
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
        # register user
        if not author in user_info.keys():
            user_info[author] = {"counts": 0, "slowmode": 0, "failed": 0}
        if count_info["last user"] == author and count_info["last user"] != "computingsquid":
            print(f'last user counted: {count_info["last user"]} user counted: {author}')
            await wrong(author, message, "You can't count twice in a row!")
        elif int(m) == count_info["current"] + 1:
            #if count_info["last user"] == "computingsquid": await message.channel.send('admin is allowed to count consecutively')
            count_info["current"] += 1
            user_info[author]["counts"] += 1
            count_info["last user"] = author
            if count_info["high score"] < count_info["current"]:
                count_info["high score"] = count_info["current"]
                count_info["highest counter"] = count_info["last user"]
            await message.add_reaction("✅")
        elif count_info["current"] == 0:
            await message.add_reaction("⚠️")
            await message.channel.send('the counting starts at 1!')
        else:
            await wrong(author, message)
        dump()


client.run(os.getenv('TOKEN'))