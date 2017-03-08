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
        if len(message.attachments):
            for attachment in message.attachments:
                if attachment['filename'] == 'champions.csv':
                    await self.bot.send_message(channel, 'DEBUG: Message attachement detected')
                    await self.bot.send_message(channel, 'attachment[0]: {}'.format(attachment))


def setup(bot):
    n = ClanMod(bot)
    bot.add_cog(n)
    bot.add_listener(n.on_attachement, name='on_message')
