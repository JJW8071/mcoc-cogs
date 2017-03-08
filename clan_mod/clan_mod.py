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


    async def _on_attachement(self, message):
        user = message.author
        msg = message.content.lower()
        channel = message.channel
        await self.bot.say('DEBUG: on_message parsed message')

        if len(message.attachements) != 0:
            await self.bot.say('DEBUG: Message attachement detected')
            await self.bot.say('attachment[0]: {}'.format(message.attachements[0]))




def setup(bot):
    n = ClanMod(bot)
    bot.add_cog(n)
    bot.add_listener(n._on_attachement, name='on_message')
