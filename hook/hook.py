import discord
from discord.ext import commands
from .mcoc import class_color_codes, ChampConverter, ChampConverterMult
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
from operator import itemgetter, attrgetter
from collections import OrderedDict
from functools import reduce
from random import randint
import shutil
import time
import os
import ast
import csv
import aiohttp
import re

### Monkey Patch of JSONEnconder
from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default  # Save unmodified default.
JSONEncoder.default = _default # replacemente
### Done with patch

class HashtagUserConverter(commands.Converter):
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
        return {'tags': tags, 'user': user}


class Hook:

    attr_map = {'Rank': 'rank', 'Awakened': 'sig', 'Stars': 'star', 'Role': 'quest_role'}
    alliance_map = {'alliance-war-defense': 'awd',
                    'alliance-war-attack': 'awo',
                    'alliance-quest': 'aq'}

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/hook/users/{}/'
        self.champs_file = self.data_dir + 'champs.json'
        self.champ_re = re.compile(r'champ.*\.csv')
        #self.champ_re = re.compile(r'champions(?:_\d+)?.csv')
        #self.champ_str = '{0[Stars]}★ R{0[Rank]} S{0[Awakened]:<2} {0[Id]}'
        self.champ_str = '{0[Stars]}★ {0[Id]} R{0[Rank]} s{0[Awakened]:<2}'


    @commands.command(pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user is None:
            user = ctx.message.author
        # creates user if doesn't exist
        info = self.load_champ_data(user)
        embeds = []
        if info['top5']:
            em = discord.Embed(color=discord.Color.gold(),title='{} [{}]'.format(user.name,info['prestige']), description='In-Game name: ')
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            # em.add_field(name='Prestige', value=info['prestige'])
            em.add_field(name='Top Champs', value='\n'.join(info['top5']))
            embeds.append(em)
        if info['max5']:
            em = discord.Embed(color=discord.Color.gold(),title='{} [{}]'.format(user.name, info['maxpi']), description='In-Game name: ')
            em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
            # em.add_field(name='Prestige', value=info['maxpi'])
            em.add_field(name='Max Champs', value='\n'.join(info['max5']))
            embeds.append(em)
        await self.pages_menu(ctx, embed_list=embeds)
        # await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def list_members(self, ctx, role: discord.Role, use_alias=True):
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
        """Displays a user profile."""
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
    #async def roster(self, ctx, *, hargs: HashtagUserConverter):
        """Displays a user profile."""
        hargs = await HashtagUserConverter(ctx, hargs).convert()
        data = await self.load_champions(hargs['user'])
        if not data['champs']:
            await self.bot.say('No Champions found in your roster.  Please upload a csv file first.')
            return
        all_champ_tags = reduce(set.union, [c.all_tags for c in data['champs']])
        residual_tags = hargs['tags'] - all_champ_tags
        if residual_tags:
            em = discord.Embed(title='Unused tags', description=' '.join(residual_tags))
            await self.bot.say(embed=em)
        filtered = set()
        for c in data['champs']:
            if hargs['tags'].issubset(c.all_tags):
                filtered.add(c)
        if not filtered:
            em = discord.Embed(title='User', description=hargs['user'].name,
                    color=discord.Color.gold())
            em.add_field(name='Tags used filtered to an empty roster',
                    value=' '.join(hargs['tags']))
            await self.bot.say(embed=em)
            return

        color = None
        for champ in filtered:
            if color is None:
                color = champ.class_color
            elif color != champ.class_color:
                color = discord.Color.gold()
                break

        champ_str = '{0.star}{0.star_char} {0.full_name} r{0.rank} s{0.sig:<2} [ {0.prestige} ]'
        classes = OrderedDict([(k, []) for k in ('Cosmic', 'Tech', 'Mutant', 'Skill',
                'Science', 'Mystic', 'Default')])

        em = discord.Embed(title="User", description=hargs['user'].name, color=color)
        if len(filtered) < 10:
            strs = [champ_str.format(champ) for champ in
                    sorted(filtered, key=attrgetter('prestige'), reverse=True)]
            em.add_field(name='Filtered Roster', value='\n'.join(strs),inline=False)
        else:
            for champ in filtered:
                classes[champ.klass].append(champ)
            for klass, champs in classes.items():
                if champs:
                    strs = [champ_str.format(champ) for champ in
                            sorted(champs, key=attrgetter('prestige'), reverse=True)]
                    em.add_field(name=klass, value='\n'.join(strs), inline=False)
        em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
        await self.bot.say(embed=em)

    #@commands.group(pass_context=True, aliases=('champs',))
    #async def champ(self, ctx):
        #if ctx.invoked_subcommand is None:
            #await self.bot.send_cmd_help(ctx)
            #return

    @roster.command(pass_context=True, name='import')
    async def _champ_import(self, ctx):
        if not ctx.message.attachments:
            await self.bot.say('This command can only be used when uploading files')
            return
        for atch in ctx.message.attachments:
            if atch['filename'].endswith('.csv'):
                await self._parse_champions_csv(ctx.message, atch)
            else:
                await self.bot.say("Cannot import '{}'.".format(atch)
                        + "  File must end in .csv and come from a Hook export")

    @roster.command(pass_context=True, name='export')
    async def _champ_export(self, ctx):
        user = ctx.message.author
        info = self.load_champ_data(user)
        rand = randint(1000, 9999)
        path, ext = os.path.splitext(self.champs_file.format(user.id))
        tmp_file = '{}-{}.tmp'.format(path, rand)
        with open(tmp_file, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=info['fieldnames'],
                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for row in info['champs']:
                writer.writerow(row)
        filename = self.data_dir.format(user.id) + '/champions.csv'
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
                champ_data = self.load_champ_data(member)
                if champ_data['prestige'] > 0:
                    prestige += champ_data['prestige']
                    cnt += 1
                if verbose is 1:
                    line_out.append('{:{width}} p = {}'.format(
                        member.name, champ_data['prestige'], width=width))
                elif verbose is 2:
                    line_out.append('{:{width}} p = {}'.format(
                        member.display_name, champ_data['prestige'], width=width))
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
                await self.bot.add_reaction(message, "⏪")
            await self.bot.add_reaction(message, "⬅")
            if choice is True:
                await self.bot.add_reaction(message,"⏺")
            await self.bot.add_reaction(message, "❌")
            await self.bot.add_reaction(message, "➡")
            if length > 5:
                await self.bot.add_reaction(message, "⏩")
        else:
            message = await self.bot.edit_message(message, embed=em)
        react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=timeout,emoji=["➡", "⬅", "❌", "⏪", "⏩","⏺"])
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message,"⏪", self.bot.user) #rewind
                    await self.bot.remove_reaction(message, "⬅", self.bot.user) #previous_page
                    await self.bot.remove_reaction(message, "❌", self.bot.user) # Cancel
                    await self.bot.remove_reaction(message,"⏺",self.bot.user) #choose
                    await self.bot.remove_reaction(message, "➡", self.bot.user) #next_page
                    await self.bot.remove_reaction(message,"⏩", self.bot.user) # fast_forward
            except:
                pass
            return None
        elif react is not None:
            react = react.reaction.emoji
            if react == "➡": #next_page
                next_page = (page + 1) % len(embed_list)
                await self.bot.remove_reaction(react.reaction.message, '➡', react.reaction.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react == "⬅": #previous_page
                next_page = (page - 1) % len(embed_list)
                await self.bot.remove_reaction(react.reaction.message, '⬅', react.reaction.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏪": #rewind
                next_page = (page - 5) % len(embed_list)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏩": # fast_forward
                next_page = (page + 5) % len(embed_list)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏺": #choose
                if choice is True:
                    await self.bot.say(SELECTION.format(category+' '))
                    answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
                    if answer is not None:
                        await self.bot.say('Process choice : {}'.format(answer.content.lower().strip()))
                        url = '{}{}/{}'.format(BASEURL,category,answer.content.lower().strip())

                        await self._process_item(ctx, url=url, category=category)
                else:
                    pass
            else:
                try:
                    return await self.bot.delete_message(message)
                except:
                    pass

    # handles user creation, adding new server, blocking
    def _create_user(self, user):
        if not os.path.exists(self.champs_file.format(user.id)):
            if not os.path.exists(self.data_dir.format(user.id)):
                os.makedirs(self.data_dir.format(user.id))
            champ_data = {
                "clan": None,
                "battlegroup": None,
                "fieldnames": ["Id", "Stars", "Rank", "Level", "Awakened", "Pi", "Role"],
                "champs": [],
                "prestige": 0,
                "top5": [],
                "aq": [],
                "awd": [],
                "awo": [],
                "max5": [],
            }
            self.save_champ_data(user, champ_data)

    async def load_champions(self, user):
        data = self.load_champ_data(user)
        cobjs = []
        for k in data['champs']:
            cobjs.append(await self.get_champion(k))
        data['champs'] = cobjs
        return data

    def load_champ_data(self, user):
        self._create_user(user)
        return dataIO.load_json(self.champs_file.format(user.id))

    def save_champ_data(self, user, data):
        dataIO.save_json(self.champs_file.format(user.id), data)

    async def get_champion(self, cdict):
        mcoc = self.bot.get_cog('MCOC')
        champ_attr = {v: cdict[k] for k,v in self.attr_map.items()}
        return await mcoc.get_champion(cdict['Id'], champ_attr)

    async def _parse_champions_csv(self, message, attachment):
        channel = message.channel
        user = message.author
        self._create_user(user)
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment['url']) as response:
                file_txt = await response.text()
        #dialect = csv.Sniffer().sniff(file_txt[:1024])
        cr = csv.DictReader(file_txt.split('\n'), #dialect,
                quoting=csv.QUOTE_NONE)
        champ_list = []
        for row in cr:
            champ_list.append({k: parse_value(k, v) for k, v in row.items()})

        champ_data = {}

        mcoc = self.bot.get_cog('MCOC')
        if mcoc:
            missing = await self.hook_prestige(champ_list)
            if missing:
                await self.bot.send_message(channel, 'Missing hookid for champs: '
                        + ', '.join(missing))

            # max prestige calcs
            champ_list.sort(key=itemgetter('maxpi', 'Id'), reverse=True)
            maxpi = sum([champ['maxpi'] for champ in champ_list[:5]])/5
            max_champs = [self.champ_str.format(champ) for champ in champ_list[:5]]
            champ_data['maxpi'] = maxpi
            champ_data['max5'] = max_champs

            # prestige calcs
            champ_list.sort(key=itemgetter('Pi', 'Id'), reverse=True)
            prestige = sum([champ['Pi'] for champ in champ_list[:5]])/5
            top_champs = [self.champ_str.format(champ) for champ in champ_list[:5]]
            champ_data['prestige'] = prestige
            champ_data['top5'] = top_champs

            em = discord.Embed(title="Updated Champions")
            em.add_field(name='Prestige', value=prestige)
            em.add_field(name='Max Prestige', value=maxpi, inline=True)
            em.add_field(name='Top Champs', value='\n'.join(top_champs), inline=False)
            em.add_field(name='Max PI Champs', value='\n'.join(max_champs), inline=True)

        champ_data['fieldnames'] = cr.fieldnames
        champ_data['champs'] = champ_list

        champ_data.update({v: [] for v in self.alliance_map.values()})
        for champ in champ_data['champs']:
            if champ['Role'] in self.alliance_map:
                champ_data[self.alliance_map[champ['Role']]].append(champ['Id'])

        self.save_champ_data(user, champ_data)
        if mcoc:
            await self.bot.send_message(channel, embed=em)
        else:
            await self.bot.send_message(channel, 'Updated Champion Information')

    async def hook_prestige(self, roster):
        '''Careful.  This modifies the array of dicts in place.'''
        missing = []
        for cdict in roster:
            cdict['maxpi'] = 0
            if cdict['Stars'] < 4:
                continue
            try:
                champ = await self.get_champion(cdict)
            except KeyError:
                missing.append(cdict['Id'])
                continue
            try:
                cdict['Pi'] = champ.prestige
            except AttributeError:
                missing.append(cdict['Id'])
                cdict['Pi'] = 0
                continue
            cdict['maxpi'] = champ.max_prestige
        return missing

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
                    await self._parse_champions_csv(msg, attachment)
                else:
                    await self.bot.send_message(channel, "Did not import")


def parse_value(key, value):
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
