<<<<<<< HEAD
import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks

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


    async def on_message(self, message):
        await self._handle_on_message(message)

    async def _handle_on_message(self, message):
        try:
            text = message.content
            channel = message.channel
            server = message.server
            user = message.author
            # creates user if doesn't exist, bots are not logged.
            await self._create_user(user, server)
            curr_time = time.time()
            userinfo = fileIO("data/clanmod/users/{}/info.json".format(user.id), "load")

            # if server.id in self.settings["disabled_servers"]:
            #     return
            # if user.bot:
            #     return
            #
            # check if chat_block exists
            if "chat_block" not in userinfo:
                userinfo["chat_block"] = 0

            if float(curr_time) - float(userinfo["chat_block"]) >= 120 and not any(text.startswith(x) for x in prefix):
                await self._process_exp(message, userinfo, random.randint(15, 20))

        await self.bot.say('DEBUG: on_message parsed message')
        await self.bot.say('DEBUG: message.attachments len = '+len(message.attachements))
        if len(message.attachements) != 0:
            await self.bot.say('DEBUG: Message attachement detected')
            await self.bot.say('attachment[0]: {}'.format(message.attachements[0]))

        except AttributeError as e:
            pass

    async def _create_user(self, user, server):
        try:
            if not os.path.exists("data/clanmod/users/{}".format(user.id)):
                os.makedirs("data/clanmod/users/{}".format(user.id))
                new_account = {
                    "servers": {},
                    "champs":{},
                    "top5": {},
                    "prestige":{}
                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", new_account)

            userinfo = fileIO("data/clanmod/users/{}/info.json".format(user.id), "load")
            if server.id not in userinfo["servers"]:
                userinfo["servers"][server.id] = {
                    "level": 0,
                }
                fileIO("data/clanmod/users/{}/info.json".format(user.id), "save", userinfo)
        except AttributeError as e:
            pass


def setup(bot):
    n = ClanMod(bot)
    bot.add_listener(n.on_message, 'on_message')
    bot.add_cog(n)
=======
import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks

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

    async def on_attachement(self, message):
        user = message.author
        channel = message.channel
        #await self.bot.send_message(channel, 'DEBUG: message.attachments len = '+len(message.attachements))
        if len(message.attachments) != 0:
            await self.bot.send_message(channel, 'DEBUG: Message attachement detected')
            await self.bot.send_message(channel, 'attachment[0]: {}'.format(message.attachments[0]))


def setup(bot):
    n = ClanMod(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_attachement, name='on_message')
>>>>>>> 1d5bdb8c094bc7ddc0284befbcb5b2c20f10c410
