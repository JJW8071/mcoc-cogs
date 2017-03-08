import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
import time
import os

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


    async def on_attachement(self, message):
        user = message.author
        channel = message.channel
        if len(message.attachments):
            for attachment in message.attachments:
                if attachment['filename'] == 'champions.csv':
                    await self.bot.send_message(channel, 'DEBUG: Message attachement detected')
                    await self.bot.send_message(channel, 'attachment[0]: {}'.format(attachment))

    # handles user creation, adding new server, blocking
    async def _create_user(self, user, server):
        await self.bot.say('DEBUG: _create_user has been initialized')
        try:
            if not os.path.exists("data/clanmod/users/{}".format(user.id)):
                os.makedirs("data/clanmod/users/{}".format(user.id))
                new_account = {
                    "servers": {},
                    "champs": {},
                    "prestige": 0,
                    "top5": {},
                    "aq": {},
                    "awd": {},
                    "awo": {}

                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", new_account)

            userinfo = fileIO("data/clanmod/users/{}/info.json".format(user.id), "load")
            if server.id not in userinfo["servers"]:
                userinfo["servers"][server.id] = {
                    "clan": {},
                    "battlegroup": {}
                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", userinfo)
        except AttributeError as e:
            pass

def setup(bot):
    n = ClanMod(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_attachement, name='on_message')
