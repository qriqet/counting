import discord
import json
from datetime import datetime, timedelta
import time
import allyourbase

from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()

f = open("data/_servers.json", "r")
server_info = json.loads(f.read())
f.close()
count_info = {}
for id in server_info.values():
    file = open(f'data/{id}.json', "r")
    count_info[str(id)] = json.loads(file.read())
    file.close()
#print(count_info)
# initialize local vars
user_cooldowns = {}

# dump function dumps local vars to saved storage json file
def dump(id):
    file = open(f'data/{id}.json', "w")
    file.write(json.dumps(count_info[id]))
    file.close()

# discord perms stuff
intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name='all the counting addicts', type=discord.ActivityType.watching)
client = discord.Client(intents=intents, activity=activity)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for x in count_info:
        print(f'Current count in server {x} is {count_info[x]["current"]}')
    

@client.event
async def on_guild_join(guild: discord.Guild):
    # Code to run when the bot joins a server
    print(f"Joined a new server: {guild.name}")
    count_info[str(guild.id)] = {
        "current": 0, "high score": 0, "highest counter": "nobody yet!", "last user": "", "channel": 0
        }
    #print(count_info)
    dump(guild.id)

    
async def wrong(author, message, reason=None):
    SERVER = str(message.guild.id)
    if reason == None:
        await message.channel.send(f'Wrong count, expected {count_info[SERVER]["current"] + 1}. Next count is 1')
    else:
        await message.channel.send(reason +  ' Next count is 1')
    await message.add_reaction("❌")
    count_info[SERVER]["current"] = 0
    count_info[SERVER]["last user"] = ""
    count_info["userdata"][author]["failed"] += 1
    count_info["userdata"]["base"] -= 1 if count_info["userdata"]["base"] != 1 else 2
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    SERVER = str(message.guild.id)
    m = message.content.split(" ")
    author = str(message.author)
    # test commands
    if m[0] == ('$guildid'):
        await message.channel.send(message.guild.id)
    if m[0] == ('$ping'):
        await message.channel.send('Pong!')
    # help command
    if m[0] == ('$help'):
        await message.channel.send("""
# Don't know how to count? 
It's simple. Simply start at 1, and increase like this:
`1 2 3 4 5`
By the way, you can't count twice in a row. And try not to fail, because failing will decrease your base!
## Useful commands:
\- $ping: pings the bot
\- $highscore: outputs current highscore
\- $count or $currentcount: outputs current count info
\- $user: use this to find out stats of a user (defaults to current user) e.g. `$user computingsquid`
\- $slowmode: find out the slowmode of a user (defaults to current user) e.g. `$slowmode computingsquid`
### Admin-only commands:
\- $setchannel: sets current channel to counting channel

        """)
    # high score
    if m[0] ==('$highscore'):
        await message.channel.send(f'Server high score is: {count_info[SERVER]["high score"]}, counted by {count_info[SERVER]["highest counter"]}')
    if m[0] ==('$currentcount') or m[0] ==('$count'):
        await message.channel.send(f'The current count is {count_info[SERVER]["current"]}, counted by {count_info[SERVER]["last user"]}')
    if m[0] == '$leaderboard':
        await message.channel.send(f'Server leaderboard:')
        leaderboard = {}
        for user in count_info[SERVER]["userdata"]:
            leaderboard[str(user)] = count_info[SERVER]["userdata"][user]["counts"] 
        joined = ""
        for user, count in leaderboard.items():
            joined += f'{user}:{count}\n'
        await message.channel.send(joined)
    ##############
    # USER STUFF #
    ##############

    if m[0] ==('$user'):
        user = ""
        if len(m) == 1: user = author
        else: user = m[1]

        await message.channel.send(f'fetching user stats for {user}')
        try:
            user_stats = count_info[SERVER]["userdata"][user]
            await message.channel.send(f'Data: \nTotal counts: {user_stats["counts"]} \nFailed counts: {user_stats["failed"]}\nSlowmode: {user_stats["slowmode"]}s')
        except KeyError:
            await message.channel.send(f'ERROR: User {user} not registered')

    if m[0] ==('$slowmode'):
        if len(m) > 1 and m[1] == "set":
            user = m[2]
            if message.author.guild_permissions.administrator or author == "computingsquid":
                try:
                    count_info[SERVER]["userdata"][user]["slowmode"] = int(m[3])
                    await message.channel.send(f'Successfully set {user}\'s slowmode to {m[3]}s')
                except:
                    await message.channel.send("invalid slowmode passed")
            else: # not admin
                if author == user:
                    await message.channel.send('You aren\'t an admin, stop trying to changing your slowmode')
                else:
                    await message.channel.send('You aren\'t an admin, stop trying to change other people\'s slowmode')

        else:
            user = ""
            if len(m) == 1:
                user = author
            else:
                user = m[1]
            try:
                user_stats = count_info[SERVER]["userdata"][user]
                await message.channel.send(f'Current slowmode for {user} is: {user_stats["slowmode"]}s')
            except KeyError:
                await message.channel.send(f'ERROR: User {user} not registered')
    # admin commands
    if message.author.guild_permissions.administrator:
        if m[0] == ('$setchannel'):
            await message.channel.send(f'counting channel set to: <#{message.channel.id}>')
            count_info[SERVER]["channel"] = int(message.channel.id)
        dump(SERVER)

    # actual counting stuff
    number = None
    try:
        number = int(allyourbase.BaseConvert(count_info[SERVER]["userdata"][user]["base"]).decode(m[0]))
    except: pass
    if int(message.channel.id) == count_info[SERVER]["channel"] and isinstance(number, int):
        # set number
        #number = eval(m[0])
        # register user
        if not author in count_info[SERVER]["userdata"].keys():
            count_info[SERVER]["userdata"][author] = {"counts": 0, "base": 16, "failed": 0}
        
        # check for slowmode
        now = datetime.now()

        # user is under cooldown
        if author in user_cooldowns and not author == "computingsquid":
            last_message_time = user_cooldowns[author]
            cooldown_end = last_message_time + timedelta(seconds=count_info[SERVER]["userdata"][author]["slowmode"])
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
    

        if count_info[SERVER]["last user"] == author and count_info[SERVER]["last user"] != "computingsquid":
            print(f'last user counted: {count_info[SERVER]["last user"]} user counted: {author}')
            await wrong(author, message, "You can't count twice in a row!")
        elif number == count_info[SERVER]["current"] + 1:
            #if count_info[SERVER]["last user"] == "computingsquid": await message.channel.send('admin is allowed to count consecutively')
            count_info[SERVER]["current"] += 1
            count_info[SERVER]["userdata"][author]["counts"] += 1
            count_info[SERVER]["last user"] = author
            if count_info[SERVER]["high score"] < count_info[SERVER]["current"]:
                count_info[SERVER]["high score"] = count_info[SERVER]["current"]
                count_info[SERVER]["highest counter"] = count_info[SERVER]["last user"]
            await message.add_reaction("✅")
            if number == 69:
                await message.add_reaction("🇳")
                await message.add_reaction("🇮")
                await message.add_reaction("🇨")
                await message.add_reaction("🇪")
        elif count_info[SERVER]["current"] == 0:
            await message.add_reaction("⚠️")
            await message.channel.send('the counting starts at 1!')
        else:
            await wrong(author, message)
        dump(SERVER)


client.run(os.getenv('TOKEN'))
