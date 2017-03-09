import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
import time
import os
import csv
import requests

class ClanMod:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_nicknames=True)
    async def assign_clan(self, ctx, user : discord.Member, *, clanname=""):
        """Change user's nickname to match his clan

        Leaving the nickname empty will remove it."""
        nickname = '[{}] {}'.format(clanname.strip(), user.name)
        if clanname == "":
            nickname = None
        try:
            await self.bot.change_nickname(user, nickname)
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Manage Nicknames\" permission.")

    @commands.command(pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user == None:
            user = ctx.message.author
        channel = ctx.message.channel
        server = user.server
        curr_time = time.time()
        # creates user if doesn't exist
        await self._create_user(user, server)
        userinfo = fileIO("data/clanmod/users/{}/info.json".format(user.id), "load")

        await self.bot.say('Temporary User Profile placeholder statement for user {}'.format(user))

    async def _on_attachment(self, message):
        channel = message.channel
        user = message.author
        server = user.server
        if len(message.attachments):
            for attachement in message.attachments:
                if attachment['filename'] = 'champions.csv':
                    await self.bot.send_message(channel, 'DEBUG: Attachment detected, calling _parse_champions_csv(message)')
                    self._parse_champions_csv(message, channel, user, attachement)

    # handles user creation, adding new server, blocking
    async def _create_user(self, user, server):
        await self.bot.say('DEBUG: _create_user has been initialized')
        try:
            if not os.path.exists("data/clanmod/users/{}".format(user.id)):
                os.makedirs("data/clanmod/users/{}".format(user.id))
                new_account = {
                    "servers": {},
                    "created": time.time(),
                    "last_updated": time.time()
                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", new_account)

            userinfo = fileIO("data/clanmod/users/{}/info.json".format(user.id), "load")
            if server.id not in userinfo["servers"]:
                userinfo["servers"][server.id] = {
                    "clan":{},
                    "battlegroup":{},
                    "champs": {},
                    "prestige": 0,
                    "top5": {},
                    "aq": {},
                    "awd": {},
                    "awo": {},
                    "max5":{},
                    "last_updated": time.time()
                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", userinfo)
        except AttributeError as e:
            pass

    async def _parse_champions_csv(self, message, channel, user, attachement):
        await self.bot.send_message(channel, 'DEBUG: _parse_champions_csv initialized')
        await self.bot.send_message(channel, 'DEBUG: attachment[0] = {}'.format(attachment))
        for attachment in message.attachments:
            if attachment['filename'] == 'champions.csv':
                await self._create_user(user,server)
                await self.bot.send_message(channel, 'attachment[0]: {}'.format(attachment))
                url = open(attachment[0]['url'])
                with requests.Session() as s:
                    download = s.get(url)
                    decoded_content = download.content.decode('utf-8')
                    cr = csv.reader(decoded_content.splitlines(),delimiter=',')
                    for i in 10:
                        temp = cr[i]
                await self.bot.say('DEBUG: CSV file opened')

#-------------- setup -------------
def check_folders():
    if not os.path.exists("data/clanmod"):
        print("Creating data/clanmod folder...")
        os.makedirs("data/clanmod")

    if not os.path.exists("data/clanmod/users"):
        print("Creating data/clanmod/users folder...")
        os.makedirs("data/clanmod/users")
        transfer_info()

def setup(bot):
    check_folders()
    n = ClanMod(bot)
    bot.add_cog(n)
    bot.add_listener(n._on_attachment, name='on_message')
