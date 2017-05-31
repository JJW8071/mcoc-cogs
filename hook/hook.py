import discord
from discord.ext import commands
from .mcoc import class_color_codes 
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
from operator import itemgetter, attrgetter
from random import randint
import time
import os
import ast
import csv
import requests
import re

class Hook:

    attr_map = {'Rank': 'rank', 'Awakened': 'sig', 'Stars': 'star'}
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
        info = self.get_user_info(user.id)
        em = discord.Embed(title="User Profile", description=user.name)
        if info['top5']:
            em.add_field(name='Prestige', value=info['prestige'])
            em.add_field(name='Top Champs', value='\n'.join(info['top5']))
            em.add_field(name='Max Champs', value='\n'.join(info['max5']))
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def list_members(self, ctx, role: discord.Role, use_alias=True):
        server = ctx.message.server
        members = []
        for member in server.members:
            if role in member.roles:
                members.append(member)
        members.sort(key=attrgetter('name'))
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
        info = self.get_user_info(user.id)
        em = discord.Embed(title="User Profile", description=user.name)
        if info['aq']:
            em.add_field(name='AQ Champs', value='\n'.join(info['aq']))
        if info['awo']:
            em.add_field(name='AWO Champs', value='\n'.join(info['awo']))
        if info['awd']:
            em.add_field(name='AWD Champs', value='\n'.join(info['awd']))
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def roster(self, ctx, user: discord.Member=None, champclass=None):
        """Displays a user profile."""
        if user is None:
            user = ctx.message.author
        if champclass is not None:
            champclass = champclass.lower().capitalize()

        user_info = self.get_user_info(user.id)
        mcoc = self.bot.get_cog('MCOC')

        #champ_str = '{0[Stars]}★ {1} r{0[Rank]} s{0[Awakened]:<2} [ {0[Pi]} ]'
        champ_str = '{0.star}★ {0.full_name} r{0.rank} s{0.sig:<2} [ {1[Pi]} ]'
        classes = {'Cosmic': [], 'Tech':[], 'Mutant': [], 'Skill': [], 
                'Science': [], 'Mystic': [], 'Default': []}

        if champclass and champclass not in classes:
            await self.bot.say("'{}' is not a valid class".format(champclass))
            return
        for k in user_info['champs']:
            champ = self.get_champion(mcoc, k)
            package = champ_str.format(champ, k)
            classes[champ.klass].append(package)

        color = class_color_codes[champclass] if champclass else discord.Color.gold()
        em = discord.Embed(title="User", description=user.name, color=color)
        for klass, class_champs in classes.items():
            if class_champs and (champclass is None or champclass == klass):
                em.add_field(name=klass, value='\n'.join(k for k in class_champs))
        em.set_footer(text='hook/champions for Collector',icon_url='https://assets-cdn.github.com/favicon.ico')
        await self.bot.say(embed=em)

    # @commands.command(pass_context=True, no_pm=True)
    # async def teamset(self, ctx, *, *args)#, user : discord.Member=None)
    #     '''Set AQ, AW Offense or AW Defense'''
    #     # if user is None:
    #     #     user = ctx.message.author
    #     user = ctx.message.author
    #     info = self.get_user_info(user.id)
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
                champ_data = self.get_user_info(member.id)
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
    #         info = self.get_user_info(user.id)
    #         em = discord.Embed(title='War Defense',description=user.name)
    #         team = []
    #         for k in info['awd']:
    #             champ = self.mcocCog._resolve_alias(k)
    #             team.append(champ.full_name)
    #         em.add_field(name='AWD:',value=team)
    #         self.bot.say(embed=em)

    @commands.group(pass_context=True, aliases=('champs',))
    async def champ(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            return

    @champ.command(pass_context=True, name='import')
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

    @champ.command(pass_context=True, name='export')
    async def _champ_export(self, ctx):
        userid = ctx.message.author.id
        info = self.get_user_info(userid)
        rand = randint(1000, 9999)
        path, ext = os.path.splitext(self.champs_file.format(userid))
        tmp_file = '{}-{}.tmp'.format(path, rand)
        with open(tmp_file, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=info['fieldnames'],
                    extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for row in info['champs']:
                writer.writerow(row)
        filename = self.data_dir.format(userid) + '/champions.csv'
        os.replace(tmp_file, filename)
        await self.bot.upload(filename)
        os.remove(filename)

    # handles user creation, adding new server, blocking
    def _create_user(self, userid):
        if not os.path.exists(self.champs_file.format(userid)):
            if not os.path.exists(self.data_dir.format(userid)):
                os.makedirs(self.data_dir.format(userid))
            champ_data = {
                "clan": None,
                "battlegroup": None,
                "fieldnames": [],
                "champs": [],
                "prestige": 0,
                "top5": [],
                "aq": [],
                "awd": [],
                "awo": [],
                "max5": [],
            }
            dataIO.save_json(self.champs_file.format(userid), champ_data)

    def get_user_info(self, userid):
        self._create_user(userid)
        return dataIO.load_json(self.champs_file.format(userid))

    def get_champion(self, mcoc, cdict):
        champ_attr = {self.attr_map[k]: cdict[k] for k in self.attr_map.keys()}
        return mcoc.get_champion(cdict['Id'], champ_attr)

    async def _parse_champions_csv(self, message, attachment):
        channel = message.channel
        userid = message.author.id
        self._create_user(userid)
        response = requests.get(attachment['url'])
        cr = csv.DictReader(response.text.split('\n'), quoting=csv.QUOTE_NONE)
        champ_list = []
        for row in cr:
            champ_list.append({k: parse_value(k, v) for k, v in row.items()})

        champ_data = {}

        mcoc = self.bot.get_cog('MCOC')
        if mcoc:
            missing = self.hook_prestige(mcoc, champ_list)
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

        dataIO.save_json(self.champs_file.format(userid), champ_data)
        if mcoc:
            await self.bot.send_message(channel, embed=em)
        else:
            await self.bot.send_message(channel, 'Updated Champion Information')

    def hook_prestige(self, mcoc, roster):
        '''Careful.  This modifies the array of dicts in place.'''
        missing = []
        for cdict in roster:
            cdict['maxpi'] = 0
            if cdict['Stars'] < 4:
                continue
            try:
                champ_obj = self.get_champion(mcoc, cdict)
            except KeyError:
                missing.append(cdict['Id'])
                continue
            try:
                cdict['Pi'] = champ_obj.prestige
            except AttributeError:
                missing.append(cdict['Id'])
                continue
            if cdict['Stars'] == 5:
                maxrank = 3 if cdict['Rank'] < 4 else 4
            else:
                maxrank = 5
            champ_obj.update_attrs({'rank': maxrank})
            cdict['maxpi'] = champ_obj.prestige
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
