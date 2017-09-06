import discord
from discord.ext import commands
from .mcoc_utils import *
from .utils.dataIO import dataIO
from .utils import chat_formatting as chat
from operator import itemgetter, attrgetter
from collections import OrderedDict, namedtuple
from random import randint
import logging
import os
import csv
import aiohttp
import re
### Monkey Patch of JSONEncoder
from json import JSONEncoder, dump, dumps

logger = logging.getLogger('red.roster')
logger.setLevel(logging.INFO)

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

KLASS_ICON='https://raw.githubusercontent.com/JasonJW/mcoc-cogs/JJWDev/mcoc/data/class_icons/{}.png'
_default.default = JSONEncoder().default  # Save unmodified default.
JSONEncoder.default = _default # replacemente
### Done with patch
#class CustomEncoder(JSONEncoder):
#    def default(self, obj):
#        return getattr(obj.__class__, "to_json", JSONEncoder.default)(obj)


class Hook:

    def __init__(self, bot):
        self.bot = bot
        self.champ_re = re.compile(r'champ.*\.csv')
        #self.champ_re = re.compile(r'champions(?:_\d+)?.csv')
        #self.champ_str = '{0[Stars]}★ R{0[Rank]} S{0[Awakened]:<2} {0[Id]}'


    @commands.command(pass_context=True)
    #async def profile(self, roster: RosterUserConverter):
    async def profile(self, ctx, roster=''):
        """Displays a user profile."""
        roster = await RosterUserConverter(ctx, roster).convert()
        if roster:
            em_info = ((discord.Color.gold(), roster.prestige, 'Top Champs'),
                       (discord.Color.red(), roster.max_prestige, 'Max Champs'))
            embeds = []
            for clr, val, title in em_info:
                em = discord.Embed(color=clr, title=str(val))
                em.set_author(name=roster.user.name, icon_url=roster.user.avatar_url)
                em.set_footer(text='hook/champions for Collector',
                              icon_url='https://assets-cdn.github.com/favicon.ico')
                em.add_field(name=title, value='\n'.join(roster.top5), inline=False)
                embeds.append(em)
            menu = PagesMenu(self.bot, timeout=120, delete_onX=True, add_pageof=True)
            await menu.menu_start(embeds)
            #await self.pages_menu(ctx, embed_list=embeds)
        else:
            em = discord.Embed(color=discord.Color.green(),title='????')
            em.set_author(name = roster.user.name,icon_url=roster.user.avatar_url)
            em.add_field(name='Missing Roster',
                    value='Load up a "champ*.csv" file from Hook to import your roster')
            em.add_field(name='Hook Web App', value='http://hook.github.io/champions/#/roster')
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            await self.bot.say(embed=em)

    @commands.command(pass_context=True, aliases=('list_members','role_roster','list_users'))
    async def users_by_role(self, ctx, role: discord.Role, use_alias=True):
        '''Embed a list of server users by Role'''
        server = ctx.message.server
        members = []
        for member in server.members:
            if role in member.roles:
                members.append(member)
        # members.sort(key=attrgetter('name'))
        if use_alias:
            ret = '\n'.join([m.display_name for m in members])
        else:
            ret = '\n'.join([m.name for m in members])
        em = discord.Embed(title='{0.name} Role - {1} member(s)'.format(role, len(members)),
                description=ret, color=role.color)
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def team(self,ctx, *, user : discord.Member=None):
        """Displays a user's AQ/AWO/AWD teams.
        Teams are set in hook/champions"""
        if user is None:
            user = ctx.message.author
        # creates user if doesn't exist
        info = self.load_champ_data(user)
        em = discord.Embed(title="User Profile", description=user.name)
        if info['aq']:
            em.add_field(name='AQ Champs', value='\n'.join(info['aq']))
        if info['awo']:
            em.add_field(name='AWO Champs', value='\n'.join(info['awo']))
        if info['awd']:
            em.add_field(name='AWD Champs', value='\n'.join(info['awd']))
        await self.bot.say(embed=em)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def roster(self, ctx, *, hargs=''):
    #async def roster(self, ctx, *, hargs: HashtagRosterConverter):
        """Displays a user roster with tag filtering
        ex.
        /roster [user] [#mutuant #bleed]"""
        hargs = await HashtagRosterConverter(ctx, hargs).convert()
        await hargs.roster.display(hargs.tags)

    @roster.command(pass_context=True, name='update')
    async def _roster_update(self, ctx, *, champs: ChampConverterMult):
        '''Update your roster using the standard command line syntax.

        Defaults for champions you specify are the current values in your roster.
        If it is a new champ, defaults are 4*, rank 1, sig 0.

        This means that
        /roster update some_champs20
        would just set some_champ's sig to 20 but keep it's rank the same.
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        await self._update(roster, champs)

    async def _update(self, roster, champs):
        track = roster.update(champs)
        em = discord.Embed(title='Champion Update for {}'.format(roster.user.name),
                color=discord.Color.gold())
        if len(champs) <= 20:
            for k in ('new', 'modified', 'unchanged'):
                if track[k]:
                    em.add_field(name='{} Champions'.format(k.capitalize()),
                            value='\n'.join(sorted(track[k])), inline=False)
        else:
            em.add_field(name='{} Champions updated, confirmed.'.format(len(champs)), value='Number exceeds display limitation')
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='dupe')
    async def _roster_dupe(self, ctx, *, champs: ChampConverterMult):
        '''Update your roster by incrementing your champs by the duped sig level, i.e. 20 for a 4*.
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        track = roster.inc_dupe(champs)
        em = discord.Embed(title='Champion Dupe Update for {}'.format(roster.user.name),
                color=discord.Color.gold())
        for k in ('modified', 'missing'):
            if track[k]:
                em.add_field(name='{} Champions'.format(k.capitalize()),
                        value='\n'.join(sorted(track[k])), inline=False)
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='delete', aliases=('del',))
    async def _roster_del(self, ctx, *, champs: ChampConverterMult):
        '''Delete champion(s) from your roster'''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        track = roster.delete(champs)
        em = discord.Embed(title='Champion Deletion for {}'.format(roster.user.name),
                color=discord.Color.gold())
        for k in ('deleted', 'non-existant'):
            if track[k]:
                em.add_field(name='{} Champions'.format(k.capitalize()),
                        value='\n'.join(sorted(track[k])), inline=False)
        await self.bot.say(embed=em)

    @roster.command(pass_context=True, name='import')
    async def _roster_import(self, ctx):
        '''Silent import file attachement command'''
        if not ctx.message.attachments:
            await self.bot.say('This command can only be used when uploading files')
            return
        for atch in ctx.message.attachments:
            if atch['filename'].endswith('.csv'):
                roster = ChampionRoster(self.bot, ctx.message.author)
                await roster.parse_champions_csv(ctx.message.channel, atch)
            else:
                await self.bot.say("Cannot import '{}'.".format(atch)
                        + "  File must end in .csv and come from a Hook export")

    @roster.command(pass_context=True, name='export')
    async def _roster_export(self, ctx):
        '''Export roster as champions.csv
        Exported file can be imported to hook/champions
        '''
        roster = ChampionRoster(ctx.bot, ctx.message.author)
        await roster.load_champions()
        rand = randint(1000, 9999)
        path, ext = os.path.split(roster.champs_file)
        tmp_file = '{}-{}.tmp'.format(path, rand)
        with open(tmp_file, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=roster.fieldnames,
                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for champ in roster.roster.values():
                writer.writerow(champ.to_json())
        filename = roster.data_dir + '/champions.csv'
        os.replace(tmp_file, filename)
        await self.bot.upload(filename)
        os.remove(filename)

    # @commands.command(pass_context=True, no_pm=True)
    # async def teamset(self, ctx, *, *args)#, user : discord.Member=None)
    #     '''Set AQ, AW Offense or AW Defense'''
    #     # if user is None:
    #     #     user = ctx.message.author
    #     user = ctx.message.author
    #     info = self.get_user_info(user)
    #     aq = False
    #     awo = False
    #     awd = False
    #     champs = []
    #     for arg in args:
    #         if arg == 'aq':
    #             aq = True
    #         elif arg == 'awo':
    #             awo = True
    #         elif arg == 'awd':
    #             awd = True
    #         champ = self.mcocCog._resolve_alias(arg)
    #         champs.append(str(champ.hookid))
    #     if aq is True:
    #         info['aq'] = champs
    #     elif awo is True:
    #         info['awo'] = champs
    #     elif awd is True:
    #         info['awd'] = champs

    @commands.command(pass_context=True, name='rank_prestige', aliases=('prestige_list',))
    async def _rank_prestige(self, ctx, *, hargs=''):
        hargs = await HashtagRankConverter(ctx, hargs).convert()
        roster = ChampionRoster(self.bot, self.bot.user)
        mcoc = self.bot.get_cog('MCOC')
        rlist = []
        for champ_class in mcoc.champions.values():
            champ = champ_class(hargs.attrs.copy())
            if champ.has_prestige:
                rlist.append(champ)
        roster.from_list(rlist)
        roster.display_override = 'Prestige Listing: {0.attrs_str}'.format(rlist[0])
        await roster.display(hargs.tags)


    @commands.command(pass_context=True, no_pm=True)
    async def clan_prestige(self, ctx, role : discord.Role, verbose=0):
        '''Report Clan Prestige.
        Specify clan-role or battlegroup-role.'''
        server = ctx.message.server
        width = 20
        prestige = 0
        cnt = 0
        line_out = []
        for member in server.members:
            if role in member.roles:
                roster = ChampionRoster(self.bot, member)
                await roster.load_champions()
                if roster.prestige > 0:
                    prestige += roster.prestige
                    cnt += 1
                if verbose is 1:
                    line_out.append('{:{width}} p = {}'.format(
                        member.name, roster.prestige, width=width))
                elif verbose is 2:
                    line_out.append('{:{width}} p = {}'.format(
                        member.display_name, roster.prestige, width=width))
        if verbose > 0:
            line_out.append('_' * (width + 11))
        if cnt > 0:
            line_out.append('{0:{width}} p = {1}  from {2} members'.format(
                    role.name, round(prestige/cnt,0), cnt, width=width))
            await self.bot.say('```{}```'.format('\n'.join(line_out)))
        else:
            await self.bot.say('You cannot divide by zero.')


    # @commands.group(pass_context=True, aliases=('teams',))
    # async def team(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.bot.send_cmd_help(ctx)
    #         return
    #
    # @team.command(pass_context=True, name='awd')
    # async def _team_awd(self, ctx):
    #     '''Return user AWD team'''
    #     channel = ctx.message.channel
    #     self.bot.send_message(channel,'DEBUG: team awd invoked: {}'.format(ctx))
    #     user = ctx.message.author
    #     message = ctx.message
    #     if message is discord.Role:
    #         self.bot.say('DEBUG: discord.Role identified')
    #     elif message is discord.Member:
    #         self.bot.say('DEBUG: discord.Member identified')
    #         user = message
    #         info = self.load_champ_data(user)
    #         em = discord.Embed(title='War Defense',description=user.name)
    #         team = []
    #         for k in info['awd']:
    #             champ = self.mcocCog._resolve_alias(k)
    #             team.append(champ.full_name)
    #         em.add_field(name='AWD:',value=team)
    #         self.bot.say(embed=em)

    # async def pages_menu(self, ctx, embed_list: list, category: str='',
    #         message: discord.Message=None, page=0, timeout: int=30, choice=False):
    #     """menu control logic for this taken from
    #        https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
    #     #print('list len = {}'.format(len(embed_list)))
    #     length = len(embed_list)
    #     em = embed_list[page]
    #     if not message:
    #         message = await self.bot.say(embed=em)
    #         if length > 5:
    #             await self.bot.add_reaction(message, '⏪')
    #         if length > 1:
    #             await self.bot.add_reaction(message, '◀')
    #         if choice is True:
    #             await self.bot.add_reaction(message,'🆗')
    #         await self.bot.add_reaction(message, '❌')
    #         if length > 1:
    #             await self.bot.add_reaction(message, '▶')
    #         if length > 5:
    #             await self.bot.add_reaction(message, '⏩')
    #     else:
    #         message = await self.bot.edit_message(message, embed=em)
    #     await asyncio.sleep(1)

    #     react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
    #     # if react.reaction.me == self.bot.user:
    #     #     react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
    #     if react is None:
    #         try:
    #             try:
    #                 await self.bot.clear_reactions(message)
    #             except:
    #                 await self.bot.remove_reaction(message,'⏪', self.bot.user) #rewind
    #                 await self.bot.remove_reaction(message, '◀', self.bot.user) #previous_page
    #                 await self.bot.remove_reaction(message, '❌', self.bot.user) # Cancel
    #                 await self.bot.remove_reaction(message,'🆗',self.bot.user) #choose
    #                 await self.bot.remove_reaction(message, '▶', self.bot.user) #next_page
    #                 await self.bot.remove_reaction(message,'⏩', self.bot.user) # fast_forward
    #         except:
    #             pass
    #         return None
    #     elif react is not None:
    #         # react = react.reaction.emoji
    #         if react.reaction.emoji == '▶': #next_page
    #             next_page = (page + 1) % len(embed_list)
    #             # await self.bot.remove_reaction(message, '▶', react.user)
    #             try:
    #                 await self.bot.remove_reaction(message, '▶', react.user)
    #             except:
    #                 pass
    #             return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
    #         elif react.reaction.emoji == '◀': #previous_page
    #             next_page = (page - 1) % len(embed_list)
    #             try:
    #                 await self.bot.remove_reaction(message, '◀', react.user)
    #             except:
    #                 pass
    #             return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
    #         elif react.reaction.emoji == '⏪': #rewind
    #             next_page = (page - 5) % len(embed_list)
    #             try:
    #                 await self.bot.remove_reaction(message, '⏪', react.user)
    #             except:
    #                 pass
    #             return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
    #         elif react.reaction.emoji == '⏩': # fast_forward
    #             next_page = (page + 5) % len(embed_list)
    #             try:
    #                 await self.bot.remove_reaction(message, '⏩', react.user)
    #             except:
    #                 pass
    #             return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
    #         elif react.reaction.emoji == '🆗': #choose
    #             if choice is True:
    #                 # await self.bot.remove_reaction(message, '🆗', react.user)
    #                 prompt = await self.bot.say(SELECTION.format(category+' '))
    #                 answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
    #                 if answer is not None:
    #                     await self.bot.delete_message(prompt)
    #                     prompt = await self.bot.say('Process choice : {}'.format(answer.content.lower().strip()))
    #                     url = '{}{}/{}'.format(BASEURL,category,answer.content.lower().strip())
    #                     await self._process_item(ctx, url=url, category=category)
    #                     await self.bot.delete_message(prompt)
    #             else:
    #                 pass
    #         else:
    #             try:
    #                 return await self.bot.delete_message(message)
    #             except:
    #                 pass

    async def _on_attachment(self, msg):
        channel = msg.channel
        prefixes = tuple(self.bot.settings.get_prefixes(msg.server))
        if not msg.attachments or msg.author.bot or msg.content.startswith(prefixes):
            return
        for attachment in msg.attachments:
            if self.champ_re.match(attachment['filename']):
                await self.bot.send_message(channel,
                        "Found a CSV file to import.  Load new champions?  Type 'yes'.")
                reply = await self.bot.wait_for_message(30, channel=channel,
                        author=msg.author, content='yes')
                if reply:
                    roster = ChampionRoster(self.bot, msg.author)
                    await roster.parse_champions_csv(msg.channel, attachment)
                else:
                    await self.bot.send_message(channel, "Did not import")


#-------------- setup -------------
def check_folders():
    #if not os.path.exists("data/hook"):
        #print("Creating data/hook folder...")
        #os.makedirs("data/hook")

    if not os.path.exists("data/hook/users"):
        print("Creating data/hook/users folder...")
        os.makedirs("data/hook/users")
        #transfer_info()

def setup(bot):
    check_folders()
    n = Hook(bot)
    bot.add_cog(n)
    bot.add_listener(n._on_attachment, name='on_message')
