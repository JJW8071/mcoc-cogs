import discord
from discord.ext import commands
from .mcoc import class_color_codes, ChampConverter, ChampConverterMult, QuietUserError
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
from operator import itemgetter, attrgetter
from collections import OrderedDict
from functools import reduce
from random import randint
import shutil
import time
import types
import os
import ast
import csv
import aiohttp
import re
import asyncio
### Monkey Patch of JSONEncoder
from json import JSONEncoder, dump, dumps

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

KLASS_ICON='https://raw.githubusercontent.com/JasonJW/mcoc-cogs/JJWDev/mcoc/data/class_icons/{}.png'
_default.default = JSONEncoder().default  # Save unmodified default.
JSONEncoder.default = _default # replacemente
### Done with patch
#class CustomEncoder(JSONEncoder):
#    def default(self, obj):
#        return getattr(obj.__class__, "to_json", JSONEncoder.default)(obj)

class MissingRosterError(QuietUserError):
    pass

class HashtagRosterConverter(commands.Converter):
    async def convert(self):
        tags = set()
        user = None
        for arg in self.argument.split():
            if arg.startswith('#'):
                tags.add(arg.lower())
            elif user is None:
                user = commands.UserConverter(self.ctx, arg).convert()
            else:
                err_msg = "There can only be 1 user argument.  All others should be '#'"
                await self.ctx.bot.say(err_msg)
                raise commands.BadArgument(err_msg)
        if user is None:
            user = self.ctx.message.author
        chmp_rstr = ChampionRoster(self.ctx.bot, user)
        await chmp_rstr.load_champions()
        if not chmp_rstr:
            em = discord.Embed(color=discord.Color.green(),title='[????] {}'.format(user.name))
            em.add_field(name='Missing Roster',
                    value='Load up a "champ*.csv" file from Hook to import your roster')
            em.add_field(name='Hook Web App', value='http://hook.github.io/champions/#/roster')
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            await self.ctx.bot.say(embed=em)
            # raise MissingRosterError('No Roster found for {}'.format(user.name))
        return types.SimpleNamespace(tags=tags, user=user, roster=chmp_rstr)

class RosterUserConverter(commands.Converter):
    async def convert(self):
        user = None
        if self.argument:
            user = commands.UserConverter(self.ctx, self.argument).convert()
        else:
            user = self.ctx.message.author
        chmp_rstr = ChampionRoster(self.ctx.bot, user)
        await chmp_rstr.load_champions()
        return chmp_rstr

class RosterConverter(commands.Converter):
    async def convert(self):
        chmp_rstr = ChampionRoster(self.ctx.bot, self.ctx.message.author)
        await chmp_rstr.load_champions()
        return chmp_rstr

class ChampionRoster:

    _data_dir = 'data/hook/users/{}/'
    _champs_file = _data_dir + 'champs.json'
    #champ_str = '{0.star}{0.star_char} {0.full_name} r{0.rank} s{0.sig:<2} [ {0.prestige} ]'
    attr_map = {'Rank': 'rank', 'Awakened': 'sig', 'Stars': 'star', 'Role': 'quest_role'}
    alliance_map = {'alliance-war-defense': 'awd',
                    'alliance-war-attack': 'awo',
                    'alliance-quest': 'aq'}
    update_str = '{0.star_name_str} {1} -> {0.rank_sig_str} [ {0.prestige} ]'

    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.roster = {}
        self._create_user()
        self._cache = {}
        #self.load_champions()

    def __len__(self):
        return len(self.roster)

    def __contains__(self, item):
        if hasattr(item, 'immutable_id'):
            return item.immutable_id in self.roster
        return item in self.roster

    # handles user creation, adding new server, blocking
    def _create_user(self):
        if not os.path.exists(self.champs_file):
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            champ_data = {
                #"clan": None,
                #"battlegroup": None,
                "fieldnames": ["Id", "Stars", "Rank", "Level", "Awakened", "Pi", "Role"],
                "roster": [],
                "prestige": 0,
                "top5": [],
                "aq": [],
                "awd": [],
                "awo": [],
                "max5": [],
            }
            dataIO.save_json(self.champs_file, champ_data)
            #self.save_champ_data(champ_data)

    async def load_champions(self):
        data = self.load_champ_data()
        self.roster = {}
        name = 'roster' if 'roster' in data else 'champs'
        for k in data[name]:
            champ = await self.get_champion(k)
            self.roster[champ.immutable_id] = champ

    def load_champ_data(self):
        data = dataIO.load_json(self.champs_file)
        self.fieldnames = data['fieldnames']
        return data

    def save_champ_data(self):
        #print(dumps(self, cls=CustomEncoder))
        #with open(self.champs_file.format(self.user.id), 'w') as fp:
            #dump(self, fp, indent=2, cls=CustomEncoder)
        dataIO.save_json(self.champs_file, self)

    def to_json(self):
        translate = ['fieldnames', 'prestige', 'max_prestige', 'top5',
                     'max5']
        pack = {i: getattr(self, i) for i in translate}
        pack['roster'] = list(self.roster.values())
        return pack
        #return {i: getattr(self, i) for i in translate}

    @property
    def data_dir(self):
        return self._data_dir.format(self.user.id)

    @property
    def champs_file(self):
        return self._champs_file.format(self.user.id)

    async def get_champion(self, cdict):
        mcoc = self.bot.get_cog('MCOC')
        champ_attr = {v: cdict[k] for k,v in self.attr_map.items()}
        return await mcoc.get_champion(cdict['Id'], champ_attr)

    async def filter_champs(self, tags):
        residual_tags = tags - self.all_tags
        if residual_tags:
            em = discord.Embed(title='Unused tags', description=' '.join(residual_tags))
            await self.bot.say(embed=em)
        filtered = set()
        for c in self.roster.values():
            if tags.issubset(c.all_tags):
                filtered.add(c.immutable_id)
        return [self.roster[iid] for iid in filtered]

    @property
    def all_tags(self):
        return reduce(set.union, [c.all_tags for c in self.roster.values()])

    @property
    def prestige(self):
        return self._get_five('prestige')[0]

    @property
    def top5(self):
        return self._get_five('prestige')[1]

    @property
    def max_prestige(self):
        return self._get_five('max_prestige')[0]

    @property
    def max5(self):
        return self._get_five('max_prestige')[1]

    def _get_five(self, key):
        if self._cache.get(key, None) is None:
            champs = sorted(self.roster.values(), key=attrgetter(key),
                        reverse=True)
            prestige = sum([getattr(champ, key) for champ in champs[:5]])/5
            champs_str = [champ.verbose_prestige_str for champ in champs[:5]]
            self._cache[key] = (prestige, champs_str)
        return self._cache[key]

    async def parse_champions_csv(self, channel, attachment):
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment['url']) as response:
                file_txt = await response.text()
        #dialect = csv.Sniffer().sniff(file_txt[:1024])
        cr = csv.DictReader(file_txt.split('\n'), #dialect,
                quoting=csv.QUOTE_NONE)
        missing = []
        dupes = []
        for row in cr:
            champ_csv = {k: parse_value(v) for k, v in row.items()}
            try:
                champ = await self.get_champion(champ_csv)
            except KeyError:
                missing.append(champ_csv['Id'])
                continue
            if champ.immutable_id in self.roster:
                dupes.append(champ)
            self.roster[champ.immutable_id] = champ

        if missing:
            await self.bot.send_message(channel, 'Missing hookid for champs: '
                    + ', '.join(self.missing))
        if dupes:
            await self.bot.send_message(channel,
                    'WARNING: Multiple instances of champs in file.  '
                    + 'Overloading:\n\t'.format(
                    ', '.join([c.star_name_str for c in dupes])))

        em = discord.Embed(title="Updated Champions")
        em.add_field(name='Prestige', value=self.prestige)
        em.add_field(name='Max Prestige', value=self.max_prestige, inline=True)
        em.add_field(name='Top Champs', value='\n'.join(self.top5), inline=False)
        em.add_field(name='Max PI Champs', value='\n'.join(self.max5), inline=True)

        self.fieldnames = cr.fieldnames

        #champ_data.update({v: [] for v in self.alliance_map.values()})
        #for champ in champ_data['champs']:
        #    if champ['Role'] in self.alliance_map:
        #        champ_data[self.alliance_map[champ['Role']]].append(champ['Id'])

        self.save_champ_data()
        #if mcoc:
        await self.bot.send_message(channel, embed=em)
        #else:
        #    await self.bot.send_message(channel, 'Updated Champion Information')

    def set_defaults_of(self, champs):
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                champ.update_default({'rank': 1, 'sig': 0})
            else:
                champ.update_default({'rank': self.roster[iid].rank,
                        'sig': self.roster[iid].sig})

    def update(self, champs):
        self.set_defaults_of(champs)
        track = {'new': set(), 'modified': set(), 'unchanged': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                track['new'].add(champ.verbose_prestige_str)
            else:
                if champ == self.roster[iid]:
                    track['unchanged'].add(champ.verbose_prestige_str)
                else:
                    track['modified'].add(self.update_str.format(champ,
                            self.roster[iid].rank_sig_str))
            self.roster[iid] = champ
        self.save_champ_data()
        return track

    def inc_dupe(self, champs):
        self.set_defaults_of(champs)
        track = {'modified': set(), 'missing': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid in self.roster:
                old_str = self.roster[iid].rank_sig_str
                self.roster[iid].inc_dupe()
                track['modified'].add(self.update_str.format(self.roster[iid], old_str))
            else:
                track['missing'].add(champ.star_name_str)
        self.save_champ_data()
        return track

    def delete(self, champs):
        track = {'deleted': set(), 'non-existant': set()}
        self._cache = {}
        for champ in champs:
            iid = champ.immutable_id
            if iid not in self.roster:
                track['non-existant'].add(champ.star_name_str)
            else:
                track['deleted'].add(champ.star_name_str)
                self.roster.pop(iid)
        self.save_champ_data()
        return track


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
            embeds = []
            em = discord.Embed(color=discord.Color.gold(),title='{}'.format(roster.prestige))
            em.set_author(name=roster.user.name, icon_url=roster.user.avatar_url)
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            em.add_field(name='Top Champs', value='\n'.join(roster.top5), inline=False)
            embeds.append(em)
            em2 = discord.Embed(color=discord.Color.red(),title='{}'.format(roster.max_prestige))
            em2.set_author(name=roster.user.name,icon_url=roster.user.avatar_url)
            em2.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            em2.add_field(name='Max Champs', value='\n'.join(roster.max5), inline=False)
            embeds.append(em2)
            await self.pages_menu(ctx, embed_list=embeds)
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

    # def setup_hook(self, author):
    #     emcolor=discord.Color.red()
        # em1 = '1. On the hook/champions webiste, enter your 4★ & 5★ champions.\nhook/champions website: <http://hook.github.io/champions>'
        # em2 = '2. Set the [rank], [level], and [signature level] for your champions.  Disregard the Power Index.  Collector will recalcualte.'
        # em3 = '3. [Optional] Set the champions in your Alliance Quest, Alliance War Defense, and Alliance War Offense teams.'
        # em4 = '4. [Android | PC Browser] Using the upper right-hand menu, Export CSV.  This will download a file [champions.csv]'
        # em5 = '4. [iOS] If you are using iOS, you have an extra step. Using the upper right-hand menu, Export CSV.\nThis produces a webpage with the content of the CSV.\nCopy the text of the entire page.\nUse the **goodReader** app (Apple Store) create a file [champions.csv] and paste the content of your clipboard.'
        # em6 ='https://cdn.discordapp.com/attachments/324676145490427904/329060454833979392/unknown.png'
        # em7 = '5. In DISCORD, upload your [champions.csv] file here, or in an appropriate channel on your server.'
        # em1=discord.Embed(color=emcolor,title='hook/Champions setup instructions',description='')
        # em1.add_field(name='Step 1: hook tool',value=em1d)
        # em1.add_field(name='Step 2: set rank, level, sig',value=em2d)
        # em1.add_field(name='Step 3: set teams',value=emd3d)
        # em1.add_field(name='Step 4: Export',value=emd4d)
        # await self.bot.send_message(author, 'test')
        # await self.bot.send_message(author, em2)
        # await self.bot.send_message(author, em3)
        # await self.bot.send_message(author, em4)
        # await self.bot.send_message(author, em5)
        # await self.bot.send_message(author, em6)
        # await self.bot.send_message(author, em7)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def roster(self, ctx, *, hargs=''):
    #async def roster(self, ctx, *, hargs: HashtagRosterConverter):
        """Displays a user roster with tag filtering
        ex.
        /roster [user] [#mutuant #bleed]"""
        hargs = await HashtagRosterConverter(ctx, hargs).convert()
        filtered = await hargs.roster.filter_champs(hargs.tags)
        embeds = []
        if not filtered:
            em = discord.Embed(title='User', description=hargs.user.name,
                    color=discord.Color.gold())
            em.add_field(name='Tags used filtered to an empty roster',
                    value=' '.join(hargs.tags))
            await self.bot.say(embed=em)
            return

        color = None
        for champ in filtered:
            if color is None:
                color = champ.class_color
            elif color != champ.class_color:
                color = discord.Color.gold()
                break

        #champ_str = '{0.star}{0.star_char} {0.full_name} r{0.rank} s{0.sig:<2} [ {0.prestige} ]'
        classes = OrderedDict([(k, []) for k in ('Cosmic', 'Tech', 'Mutant', 'Skill',
                'Science', 'Mystic', 'Default')])

        if len(filtered) < 10:
            em = discord.Embed(title='', color=color)
            em.set_author(name=hargs.user.name,icon_url=hargs.user.avatar_url)
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            strs = [champ.verbose_prestige_str for champ in
                    sorted(filtered, key=attrgetter('prestige'), reverse=True)]
            em.add_field(name='Filtered Roster', value='\n'.join(strs),inline=False)
            embeds.append(em)
        else:
            i = 1
            for champ in filtered:
                classes[champ.klass].append(champ)
            for klass, champs in classes.items():
                if champs:
                    strs = [champ.verbose_prestige_str for champ in
                            sorted(champs, key=attrgetter('prestige'), reverse=True)]
                    em = discord.Embed(title='', description='Page {}'.format(i), color=class_color_codes[klass])
                    em.set_author(name=hargs.user.name,icon_url=hargs.user.avatar_url)
                    # em.set_thumbnail(url=KLASS_ICON.format(klass.lower()))
                    em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
                    em.add_field(name=klass, value='\n:{}: '.format(klass.lower()).join(strs), inline=False)
                    embeds.append(em)
                    i+=1
        # await self.bot.say(embed=em)
        await self.pages_menu(ctx=ctx, embed_list=embeds, timeout=120)

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
        for k in ('new', 'modified', 'unchanged'):
            if track[k]:
                em.add_field(name='{} Champions'.format(k.capitalize()),
                        value='\n'.join(sorted(track[k])), inline=False)
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

    @commands.command(pass_context=True)
    async def clan_prestige(self, ctx, role : discord.Role, verbose=0):
        '''Report Clan Prestige'''
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
        line_out.append('{0:{width}} p = {1}  from {2} members'.format(
                role.name, round(prestige/cnt,0), cnt, width=width))
        await self.bot.say('```{}```'.format('\n'.join(line_out)))


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

    async def pages_menu(self, ctx, embed_list: list, category: str='', message: discord.Message=None, page=0, timeout: int=30, choice=False):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        print('list len = {}'.format(len(embed_list)))
        length = len(embed_list)
        em = embed_list[page]
        if not message:
            message = await self.bot.say(embed=em)
            if length > 5:
                await self.bot.add_reaction(message, '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}')
            await self.bot.add_reaction(message, '\N{BLACK LEFT-POINTING TRIANGLE}')
            if choice is True:
                await self.bot.add_reaction(message,'\N{SQUARED OK}')
            await self.bot.add_reaction(message, '\N{CROSS MARK}')
            await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}')
            if length > 5:
                await self.bot.add_reaction(message, '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}')
        else:
            message = await self.bot.edit_message(message, embed=em)
        await asyncio.sleep(1)

        react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['\N{BLACK RIGHT-POINTING TRIANGLE}', '\N{BLACK LEFT-POINTING TRIANGLE}', '\N{CROSS MARK}', '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}', '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}','\N{SQUARED OK}'])
        # if react.reaction.me == self.bot.user:
        #     react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['\N{BLACK RIGHT-POINTING TRIANGLE}', '\N{BLACK LEFT-POINTING TRIANGLE}', '\N{CROSS MARK}', '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}', '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}','\N{SQUARED OK}'])
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message,'\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}', self.bot.user) #rewind
                    await self.bot.remove_reaction(message, '\N{BLACK LEFT-POINTING TRIANGLE}', self.bot.user) #previous_page
                    await self.bot.remove_reaction(message, '\N{CROSS MARK}', self.bot.user) # Cancel
                    await self.bot.remove_reaction(message,'\N{SQUARED OK}',self.bot.user) #choose
                    await self.bot.remove_reaction(message, '\N{BLACK RIGHT-POINTING TRIANGLE}', self.bot.user) #next_page
                    await self.bot.remove_reaction(message,'\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}', self.bot.user) # fast_forward
            except:
                pass
            return None
        elif react is not None:
            # react = react.reaction.emoji
            if react.reaction.emoji == '\N{BLACK RIGHT-POINTING TRIANGLE}': #next_page
                next_page = (page + 1) % len(embed_list)
                # await self.bot.remove_reaction(message, '▶', react.reaction.message.author)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '\N{BLACK LEFT-POINTING TRIANGLE}': #previous_page
                next_page = (page - 1) % len(embed_list)
                # await self.bot.remove_reaction(message, '⬅', react.reaction.message.author)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}': #rewind
                next_page = (page - 5) % len(embed_list)
                # await self.bot.remove_reaction(message, '⏪', react.reaction.message.author)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}': # fast_forward
                next_page = (page + 5) % len(embed_list)
                # await self.bot.remove_reaction(message, '⬅', react.reaction.message.author)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '\N{SQUARED OK}': #choose
                if choice is True:
                    # await self.bot.remove_reaction(message, '⏩', react.reaction.message.author)
                    prompt = await self.bot.say(SELECTION.format(category+' '))
                    answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
                    if answer is not None:
                        await self.bot.delete_message(prompt)
                        prompt = await self.bot.say('Process choice : {}'.format(answer.content.lower().strip()))
                        url = '{}{}/{}'.format(BASEURL,category,answer.content.lower().strip())
                        await self._process_item(ctx, url=url, category=category)
                        await self.bot.delete_message(prompt)
                else:
                    pass
            else:
                try:
                    return await self.bot.delete_message(message)
                except:
                    pass

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


def parse_value(value):
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


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
