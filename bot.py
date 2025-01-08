# This example requires the 'message_content' intent.

import discord
import json
from datetime import datetime, timedelta
import time

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

# local vars
user_cooldowns = {}

def dump():
    file = open("storage.json", "w")
    file.write(json.dumps(count_info))
    file.close()
    file = open("users.json", "w")
    file.write(json.dumps(user_info))
    file.close()

# discord perms stuff
intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name='all the counting addicts', type=discord.ActivityType.watching)
client = discord.Client(intents=intents, activity=activity)

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
    user_info[author]["slowmode"] *= 2
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    m = message.content.split(" ")
    author = str(message.author)
    # test commands
    if m[0] == ('$ping'):
        await message.channel.send('Pong!')
    # help command
    if m[0] == ('$help'):
        await message.channel.send("""
# Don't know how to count? 
It's simple. Simply start at 1, and increase like this:
`1 2 3 4 5`
By the way, you can't count twice in a row. And try not to fail, because failing will **DOUBLE** your slowmode!
## Useful commands:
\- $ping: pings the bot
\- $highscore: outputs current highscore
\- $count or $currentcount: outputs current count info
\- $user: use this to find out stats of a user (defaults to current user) e.g. `$user computingsquid`
### Admin-only commands:
\- $setchannel: sets current channel to counting channel
\- $addadmin: adds a user to admins list 
        """)
    # high score
    if m[0] ==('$highscore'):
        await message.channel.send(f'Server high score is: {count_info["high score"]}, counted by {count_info["highest counter"]}')
    if m[0] ==('$currentcount') or m[0] ==('$count'):
        await message.channel.send(f'The current count is {count_info["current"]}, counted by {count_info["last user"]}')
    
    ##############
    # USER STUFF #
    ##############

    if m[0] ==('$user'):
        user = ""
        if len(m) == 1: user = author
        else: user = m[1]

        await message.channel.send(f'fetching user stats for {user}')
        try:
            user_stats = user_info[user]
            await message.channel.send(f'Data: \nTotal counts: {user_stats["counts"]} \nFailed counts: {user_stats["failed"]}\nSlowmode: {user_stats["slowmode"]}s')
        except KeyError:
            await message.channel.send(f'ERROR: User {user} not registered')

    if m[0] ==('$slowmode'):
        if len(m) > 1 and m[1] == "set":
            if author in count_info["admins"]:
                user = m[2]
                try:
                    user_info[user]["slowmode"] = int(m[3])
                    await message.channel.send(f'Successfully set {user}\'s slowmode to {m[3]}s')
                except:
                    await message.channel.send("invalid slowmode passed")
            else: # not admin
                if author == user:
                    await message.channel.send('You aren\'t and admin, stop trying to changing your slowmode')
                else:
                    await message.channel.send('You aren\'t and admin, stop trying to change other people\'s slowmode')

        else:
            user = ""
            if len(m) == 1:
                user = author
            else:
                user = m[1]
            try:
                user_stats = user_info[user]
                await message.channel.send(f'Current slowmode for {user} is: {user_stats["slowmode"]}s')
            except KeyError:
                await message.channel.send(f'ERROR: User {user} not registered')
    # admin commands
    if author in count_info["admins"]:
        if m[0] == ('$setchannel'):
            await message.channel.send(f'counting channel set to: <#{message.channel.id}>')
            count_info["channel"] = int(message.channel.id)
        if m[0] ==('$addadmin'):
            username = m[1]
            if not username in count_info["admins"]:
                count_info["admins"].append(username)
                await message.channel.send(f'set {username} as admin')
            else:
                await message.channel.send(f'{username} is already an admin')
        dump()
 
    # funny
    if m[0].lower().startswith('is the admin allowed to'):
        await message.channel.send(f'yes, of course they can {m[0][24:]}')

    # actual counting stuff
    number = None
    try:
        #print(eval(''.join(m)))
        number = int(eval(''.join(m)))
        #print(f'evaluated {number}')
    except:
        try:
            number = int(eval(m[0]))
            print(f'falling back to evaluating first block, {number}')
        except: pass
        pass
    if int(message.channel.id) == count_info["channel"] and isinstance(number, int):
        # set number
        #number = eval(m[0])
        # register user
        if not author in user_info.keys():
            user_info[author] = {"counts": 0, "slowmode": 1, "failed": 0}
        
        # check for slowmode
        now = datetime.now()

        # user is under cooldown
        if author in user_cooldowns and not author == "computingsquid":
            last_message_time = user_cooldowns[author]
            cooldown_end = last_message_time + timedelta(seconds=user_info[author]["slowmode"])
            if now < cooldown_end:
                # Message sent too soon, delete it
                await message.delete()
                try:
                    unix_sec = time.mktime(cooldown_end.timetuple())
                    await message.author.send("Hey! You're still under slowmode! you have <t:" + str(int(unix_sec)) + ":R> left")
                    #print(f"Message sent to {message.author.name}!")
                except discord.Forbidden:
                    print(f"Could not send a DM to {message.author.name}. They might have DMs disabled.")
                return

        # Update the user's last message time
        user_cooldowns[author] = now
    

        if count_info["last user"] == author and count_info["last user"] != "computingsquid":
            print(f'last user counted: {count_info["last user"]} user counted: {author}')
            await wrong(author, message, "You can't count twice in a row!")
        elif number == count_info["current"] + 1:
            #if count_info["last user"] == "computingsquid": await message.channel.send('admin is allowed to count consecutively')
            count_info["current"] += 1
            user_info[author]["counts"] += 1
            count_info["last user"] = author
            if count_info["high score"] < count_info["current"]:
                count_info["high score"] = count_info["current"]
                count_info["highest counter"] = count_info["last user"]
            await message.add_reaction("✅")
            if number == 69:
                await message.add_reaction("🇳")
                await message.add_reaction("🇮")
                await message.add_reaction("🇨")
                await message.add_reaction("🇪")
        elif count_info["current"] == 0:
            await message.add_reaction("⚠️")
            await message.channel.send('the counting starts at 1!')
        else:
            await wrong(author, message)
        dump()


client.run(os.getenv('TOKEN'))