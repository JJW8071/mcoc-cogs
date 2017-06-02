import re
from datetime import datetime, timedelta
from textwrap import wrap
from collections import UserDict, defaultdict
from operator import or_
from functools import reduce
from math import log2
from math import *
import os
import inspect
import urllib
import requests
import csv
import json
from gsheets import Sheets
import asyncio
from .utils.dataIO import dataIO
from functools import wraps
import discord
from discord.ext import commands
from .utils.dataIO import dataIO



data_files = {
    'spotlight': {'remote': 'https://docs.google.com/spreadsheets/d/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/pub?gid=0&single=true&output=csv',
                'local': 'data/mcoc/spotlight_data.csv', 'update_delta': 1},
    'crossreference': {'remote': 'https://docs.google.com/spreadsheets/d/1WghdD4mfchduobH0me4T6IvhZ-owesCIyLxb019744Y/pub?gid=0&single=true&output=csv',
                'local': 'data/mcoc/crossreference.csv', 'update_delta': 1},
    # 'sig_data': {'remote': 'https://docs.google.com/spreadsheets/d/1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg/export?gid=799981914&single=true&format=csv',
    #             'local': 'data/mcoc/sig_data.csv', 'update_delta': 1},
    'prestige': {'remote': 'https://spreadsheets.google.com/feeds/list/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/2/public/values?alt=json',
                'local': 'data/mcoc/prestige.json', 'update_delta': 1},
    'phc_jpg' : {'remote': 'http://marvelbitvachempionov.ru/wp-content/dates_PCHen.jpg',
                'local': 'data/mcoc/dates_PCHen.jpg', 'update_delta': 7},
    'duelist' : {'remote': 'https://docs.google.com/spreadsheets/d/1LSNS5j1d_vs8LqeiDQD3lQFNIxQvTc9eAx3tNe5mdMk/pub?gid=1266181139&single=true&output=csv',
                'local': 'data/mcoc/duelist.csv', 'update_delta': 1},
    #'sig_coeff': {'remote': 'https://docs.google.com/spreadsheets/d/1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg/export?gid=696682690&format=csv',
                #'local': 'data/mcoc/sig_coeff.csv', 'update_delta': 0},
    #'effect_keys': {'remote': 'https://docs.google.com/spreadsheets/d/1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg/export?gid=229525912&format=csv',
    #            'local': 'data/mcoc/effect_keys.csv', 'update_delta': 0},
### coefficient by rank is HOOK's prestige coefficients.  But I am uncertain of generation process.
##   'coefficient-by-rank': {'remote': 'https://github.com/hook/champions/blob/master/src/data/pi/coefficient-by-rank.json',
##               'local': 'data/mcoc/coefficient-by-rank.json'},
    }

local_files = {
    'sig_coeff': 'data/mcoc/sig_coeff.csv',
    'effect_keys': 'data/mcoc/effect_keys.csv',
}

gsheet_files = {
    'signature': {'gkey': '1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg',
            'local': 'data/mcoc/sig_test.csv',
            'gid': 799981914,},
            #'payload': 'pub?gid=799981914&single=true&output=csv'},
    'spotlight': {'gkey': '1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks',
            'local': 'data/mcoc/spotlight_test.csv',
            },
            #'payload': 'pub?gid=0&single=true&output=csv'},
    #'sig_coeff': {'gkey': '1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg',
    'sig_coeff': {'gkey': '1P-GeEOyod6WSGq8fUfSPZcvowthNdy-nXLKOhjrmUVI',
            'local': 'data/mcoc/sig_co_test.csv',
            'stub': 'export',
            #'range': 'A1:N99',
            #'gid': 696682690},
            },
    'crossreference': {'gkey': '1QesYLjDC8yd4t52g4bN70N8FndJXrrTr7g7OAS0BItk',
            'local': 'data/mcoc/xref_test.csv',
            #'payload': 'export?format=csv'}
            },
            #'payload': 'pub?gid=0&single=true&output=csv'}
}

# sig_data = 'data/mcoc/sig_data.json'
prestige_data = 'data/mcoc/prestige_data.json'
star_glyph = {1: '★', 2: '★★', 3: '★★★', 4: '★★★★', 5: '★★★★★'}

lolmap_path='data/mcoc/maps/lolmap.png'
file_checks_json = 'data/mcoc/file_checks.json'
remote_data_basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/'
icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'

###### KEYS for MCOC JSON Data Extraction
mcoc_dir='data/mcoc/com.kabam.marvelbattle/files/xlate/snapshots/en/'
kabam_bio = mcoc_dir + 'character_bios_en.json'
kabam_special_attacks = mcoc_dir+ 'special_attacks_en.json'
kabam_bcg_stat_en = mcoc_dir+'bcg_stat_en.json'
##### Special attacks require:
## mcoc_files + mcoc_special_attack + <champ.mcocjson> + {'_0','_1','_2'} ---> Special Attack title
#mcoc_special_attack='ID_SPECIAL_ATTACK_'
## mcoc_files mcoc_special_attack_desc + <champ.mcocjson> + {'_0','_1','_2'} ---> Special Attack Short description
#mcoc_special_attack_desc='ID_SPECIAL_ATTACK_DESCRIPTION_'


class_color_codes = {
        'Cosmic': discord.Color(0x2799f7), 'Tech': discord.Color(0x0033ff),
        'Mutant': discord.Color(0xffd400), 'Skill': discord.Color(0xdb1200),
        'Science': discord.Color(0x0b8c13), 'Mystic': discord.Color(0x7f0da8),
        'All': discord.Color(0xffffff), 'default': discord.Color.light_grey(),
        }

def from_flat(flat, ch_rating):
    denom = 5 * ch_rating + 1500 + flat
    return round(100*flat/denom, 2)

def to_flat(per, ch_rating):
    num = (5 * ch_rating + 1500) * per
    return round(num/(100-per), 2)

class AliasDict(UserDict):
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        for k in self.data.keys():
            if key in k:
                return self.data[k]
        raise KeyError("Invalid Key '{}'".format(key))

class ChampionFactory():

    champions = AliasDict()

    def create_champion_class(self, bot, alias_set, **kwargs):
        kwargs['bot'] = bot
        kwargs['alias_set'] = alias_set
        kwargs['klass'] = kwargs.pop('class', 'default')
        for key, value in kwargs.items():
            if not value or value == 'n/a':
                kwargs[key] = None
        kwargs['full_name'] = kwargs['champ']
        kwargs['bold_name'] = '**' + ' '.join(
                [word.capitalize() for word in kwargs['full_name'].split(' ')]
                ) + '**'
        kwargs['class_color'] = class_color_codes[kwargs['klass']]
        champion = type(kwargs['mattkraftid'], (Champion,), kwargs)
        self.champions[tuple(alias_set)] = champion
        return champion

    def get_champion(self, name_id, attrs=None):
        champ = self.champions[name_id]
        return champ(attrs)

    def search_champions(self, search_str, attrs=None):
        re_str = re.compile(search_str)
        champs = []
        for champ in self.champions.values():
            if reduce(or_, [re_str.search(alias) is not None
                    for alias in champ.alias_set]):
                champs.append(champ(attrs))
        return champs


class ChampConverter(commands.Converter):

    _bare_arg = None
    parse_re = re.compile(r'''(?:s(?P<sig>[0-9]{1,3}))
                             |(?:r(?P<rank>[1-5]))
                             |(?:(?P<star>[1-5])\\?\*)
                             |(?:d(?P<debug>[0-9]{1,2}))''', re.X)
    async def convert(self):
        bot = self.ctx.bot
        attrs = {}
        if self._bare_arg:
            args = self.argument.rsplit(' ', maxsplit=1)
            if len(args) > 1 and args[-1].isdecimal():
                attrs[self._bare_arg] = int(args[-1])
                self.argument = args[0]
        arg = ''.join(self.argument.lower().split(' '))
        for m in self.parse_re.finditer(arg):
            attrs[m.lastgroup] = int(m.group(m.lastgroup))
        token = self.parse_re.sub('', arg)
        if not token:
            err_str = "No Champion remains from arg '{}'".format(self.argument)
            await bot.say(err_str)
            raise commands.BadArgument(err_str)
        return (await self.get_champion(bot, token, attrs))

    async def get_champion(self, bot, token, attrs):
        mcoc = bot.get_cog('MCOC')
        try:
            champ = mcoc.get_champion(token, attrs)
        except KeyError:
            champs = mcoc.search_champions('.*{}.*'.format(token), attrs)
            if len(champs) == 1:
                await bot.say("'{}' was not exact but found close alternative".format(
                        token))
                champ = champs[0]
            else:
                err_str = "Cannot resolve alias for '{}'".format(token)
                await bot.say(err_str)
                raise commands.BadArgument(err_str)
        return champ

class ChampConverterSig(ChampConverter):
    _bare_arg = 'sig'

class ChampConverterRank(ChampConverter):
    _bare_arg = 'rank'

class ChampConverterStar(ChampConverter):
    _bare_arg = 'star'

class ChampConverterDebug(ChampConverter):
    _bare_arg = 'debug'

class ChampConverterMult(ChampConverter):
    async def convert(self):
        bot = self.ctx.bot
        champs = []
        default = {}
        for arg in self.argument.lower().split(' '):
            attrs = default.copy()
            for m in self.parse_re.finditer(arg):
                attrs[m.lastgroup] = int(m.group(m.lastgroup))
            token = self.parse_re.sub('', arg)
            if token != '':
                champ = await self.get_champion(bot, token, attrs)
                champs.append(champ)
            else:
                default.update(attrs)
        return champs

class MCOC(ChampionFactory):
    '''A Cog for Marvel's Contest of Champions'''
    def __init__(self, bot):
        self.bot = bot

        self.settings = {
                'siglvl': 1,
                'sigstep': 20,
                'table_width': 9,
                'sig_inc_zero': False,
                }

        self.parse_re = re.compile(r'(?:s(?P<sig>[0-9]{1,3}))|(?:r(?P<rank>[1-5]))|(?:(?P<star>[1-5])\\?\*)')
        self.split_re = re.compile(', (?=\w+:)')
        self.verify_cache_remote_files(verbose=True)
        self._init()

    def _init(self):
        self._prepare_aliases()
        self._prepare_prestige_data()

    @commands.command(aliases=('p2f',),hidden=True)
    async def per2flat(self, per: float, ch_rating: int=100):
        '''Convert Percentage to MCOC Flat Value'''
        await self.bot.say(to_flat(per, ch_rating))

    @commands.command(aliases=('flat', 'f2p'),hidden=True)
    async def flat2per(self, *, m):
        '''Convert MCOC Flat Value to Percentge'''
        if ' ' in m:
            m, cr = m.rsplit(' ',1)
            challenger_rating = int(cr)
        else:
            challenger_rating = 100
        m = ''.join(m)
        math_filter = re.findall(r'[\[\]\-()*+/0-9=.,% ]' +
            r'|acos|acosh|asin|asinh' +
            r'|atan|atan2|atanh|ceil|copysign|cos|cosh|degrees|e|erf|erfc|exp' +
            r'|expm1|fabs|factorial|floor|fmod|frexp|fsum|gamma|gcd|hypot|inf' +
            r'|isclose|isfinite|isinf|isnan|round|ldexp|lgamma|log|log10|log1p' +
            r'|log2|modf|nan|pi|pow|radians|sin|sinh|sqrt|tan|tanh', m)
        flat_val = eval(''.join(math_filter))
        p = from_flat(flat_val, challenger_rating)
        em = discord.Embed(color=discord.Color.gold(),
                title='FlatValue:',
                description='{}'.format(flat_val))
        em.add_field(name='Percentage:', value='{}\%'.format(p))
        await self.bot.say(embed=em)

    @commands.command(aliases=['compf',],hidden=True)
    async def compound_frac(self, base: float, exp: int):
        if base > 1:
            base = base / 100
        compound = 1 - (1 - base)**exp
        em = discord.Embed(color=discord.Color.gold(),
            title="Compounded Fractions",
            description='{:.2%} compounded {} times'.format(base, exp))
        em.add_field(name='Expected Chance', value='{:.2%}'.format(compound))
        await self.bot.say(embed=em)

    @commands.command(aliases=['update_mcoc',],hidden=True)
    async def mcoc_update(self, fname, force=False):
        if len(fname) > 3:
            for key in data_files.keys():
                if key.startswith(fname):
                    fname = key
                    break
        if fname in data_files:
            self.cache_remote_file(fname, force_cache=force, verbose=True)
        else:
            await self.bot.say('Valid options for 1st argument are one of (or initial portion of)\n\t'
                    + '\n\t'.join(data_files.keys()))
            return

        self._init()
        await self.bot.say('Summoner, I have Collected the data')

    async def say_user_error(self, msg):
        em = discord.Embed(color=discord.Color.gold(), title=msg)
        await self.bot.say(embed=em)

    @commands.command(hidden=True)
    async def mcocset(self, setting, value):
        if setting in self.settings:
            self.settings[setting] = int(value)

    def verify_cache_remote_files(self, verbose=False, force_cache=False):
        if os.path.exists(file_checks_json):
            try:
                file_checks = dataIO.load_json(file_checks_json)
            except:
                file_checks = {}
        else:
            file_checks = {}
        s = requests.Session()
        for key in data_files.keys():
            if key in file_checks:
                last_check = datetime(*file_checks.get(key))
            else:
                last_check = None
            remote_check = self.cache_remote_file(key, s, verbose=verbose,
                    last_check=last_check)
            if remote_check:
                file_checks[key] = remote_check.timetuple()[:6]
        dataIO.save_json(file_checks_json, file_checks)

    def cache_remote_file(self, key, session=None, verbose=False, last_check=None,
                force_cache=False):
        if session is None:
            session = requests.Session()
        dargs = data_files[key]
        strf_remote = '%a, %d %b %Y %H:%M:%S %Z'
        response = None
        remote_check = False
        now = datetime.now()
        if os.path.exists(dargs['local']) and not force_cache:
            check_marker = None
            if last_check:
                check_marker = now - timedelta(days=dargs['update_delta'])
                refresh_remote_check = check_marker > last_check
            else:
                refresh_remote_check = True
            local_dt = datetime.fromtimestamp(os.path.getmtime(dargs['local']))
            #print(check_marker, last_check, refresh_remote_check, local_dt)
            if refresh_remote_check:
                response = session.get(dargs['remote'])
                if 'Last-Modified' in response.headers:
                    remote_dt = datetime.strptime(response.headers['Last-Modified'], strf_remote)
                    remote_check = now
                    if remote_dt < local_dt:
                        # Remote file is older, so no need to transfer
                        response = None
                #else:
                    #print('DEBUG: No Last-Modified header ', remote)
                    #print('DEBUG: Date:  ', response.headers['Date'])
                    #for k in response.headers:
                        #print(k)
                    #print(response.headers.keys())
        else:
            response = session.get(dargs['remote'])
        if response and response.status_code == requests.codes.ok:
            print('Caching remote contents to local file: ' + dargs['local'])
            with open(dargs['local'], 'wb') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            remote_check = now
        elif response:
            err_str = "HTTP error code {} while trying to retrieve {}".format(
                    response.status_code, key)
            print(err_str)
        elif verbose and remote_check:
            print('Local file up-to-date:', dargs['local'], now)
        return remote_check

    @commands.command(hidden=True)
    async def cache_gsheets(self):
        s = requests.Session()
        #gs = Sheets.from_files('data/mcoc/client_secrets.json')
        for k, v in gsheet_files.items():
            #s = gs[v['gkey']]
            #s.sheets[0].to_csv(v['local'])
            #payload = {'format': 'csv', 'gid': v.get('gid', 0)}
            if 'payload' in k:
                payload = {}
                remote = 'https://docs.google.com/spreadsheets/d/{0[gkey]}/{0[payload]}'.format(v)
            elif v.get('stub') == 'export':
                payload = {'format': 'csv', 'gid': v.get('gid', 0)}
                remote = 'https://docs.google.com/spreadsheets/d/{0[gkey]}/{0[stub]}'.format(v)
            else:
                payload = {'output': 'csv', 'single': 'true', 'gid': v.get('gid', 0)}
                remote = 'https://docs.google.com/spreadsheets/d/{0}/pub'.format(v['gkey'])
            #response = s.get(remote)
            response = s.get(remote, params=payload)
            if response.status_code == requests.codes.ok:
                with open(v['local'], 'wb') as fp:
                    for chunk in response.iter_content():
                        fp.write(chunk)
            else:
                err_str = "HTTP error code {} while trying to retrieve Google Sheet {}".format(
                        response.statuse_code, k)
                await self.bot.say(err_str)
        await self.bot.say("Google Sheet retrieval complete")

    @commands.command(aliases=['featured'])
    async def champ_featured(self, champ : ChampConverter):
        '''Retrieve Champion Feature Images'''
        em = discord.Embed(color=champ.class_color, title=champ.bold_name)
        em.set_image(url=champ.get_featured())
        await self.bot.say(embed=em)

    @commands.command(aliases=['portrait',])
    async def champ_portrait(self, champ : ChampConverter):
        '''Retrieve Champion Portrait'''
        em = discord.Embed(color=champ.class_color, title=champ.bold_name)
        em.set_image(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @commands.command(aliases=('bio',))
    async def champ_bio(self, *, champ : ChampConverterDebug):
        '''Retrieve the Bio of a Champion'''
        try:
            bio_desc = await champ.get_bio()
        except KeyError:
            await self.say_user_error("Cannot find bio for Champion '{}'".format(champ.full_name))
            return
        em = discord.Embed(color=champ.class_color, title=champ.full_name,
                description=bio_desc)
        em.set_thumbnail(url=champ.get_avatar())
        em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
        await self.bot.say(embed=em)

    @commands.command(aliases=('duel',))
    async def champ_duel(self, champ : ChampConverter):
        '''Lookup Duel/Sparring Targets'''
        dataset=data_files['duelist']['local']
        targets = defaultdict(list)
        names = {4: 'Duel', 5: 'Sparring'}
        em = discord.Embed(color=champ.class_color, title='')
        em.set_image(url=champ.get_featured())
        em.set_footer(text='Sourced from Community Spreadsheet',
                icon_url='https://d2jixqqjqj5d23.cloudfront.net/assets/developer/imgs/icons/google-spreadsheet-icon.png')
        target_found = False
        for star in (4,5):
            for rank in range(6):
                champ.update_attrs({'star': star, 'rank': rank})
                for data in get_csv_rows(dataset, 'unique', champ.unique):
                    if data['username'] != 'none':
                        targets[star].append( '{} : {}'.format(
                                champ.star_str, data['username']))
            if len(targets[star]) > 0:
                target_found = True
                em.add_field(name='{} Target'.format(names[star]),
                        value='\n'.join(k for k in targets[star]), inline=False)
        if not target_found:
            em.add_field(name='Target not found',
                    value='\n'.join(['Add one to the Community Spreadhseet!',
                            'Duel Targets: <http://simians.tk/mcocduel>',
                            'Sparring Targets: <http://simians.tk/mcocspar>']))
        await self.bot.say(embed=em)

    @commands.command(aliases=('champ_stat', 'champ_stats', 'cstat', 'about_champ'))
    async def champ_about(self, *, champ : ChampConverterRank):
        '''Retrieve Champion Base Stats'''
        data = champ.get_spotlight(default='x')
        title = 'Base Attributes for {}'.format(champ.verbose_str)
        em = discord.Embed(color=champ.class_color,
                title=champ.verbose_str, description='Base Attributes')
        titles = ('Health', 'Attack', 'Crit Rate', 'Crit Damage', 'Armor', 'Block Prof')
        keys = ('health', 'attack', 'critical', 'critdamage', 'armor', 'blockprof')
        if champ.debug:
            em.add_field(name='Attrs', value='\n'.join(titles))
            em.add_field(name='Values', value='\n'.join([data[k] for k in keys]), inline=True)
        else:
            for t, k in zip(titles, keys):
                em.add_field(name=t, value=data[k])
        if champ.infopage != 'none':
            em.add_field(name='Infopage',value='<{}>'.format(champ.infopage))
        em.set_footer(text='[-SDF-] Spotlight Dataset', icon_url=icon_sdf)
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    # @commands.command(aliases=['msig',])
    # async def mcoc_sig(self, champ : ChampConverter, siglvl: int=99, star: int=4, dbg=False):
    #     '''Retrieve Champion Signature Ability from MCOC Files'''
    #     mcocjson = champ.mcocjson
    #     title, title_lower, simple, desc = champ.get_mcoc_keys()
    #
    #     raw_sig = '\n'.join([Champion._sig_header(sigs[k]) for k in desc])
    #     #clean_sig = raw_sig
    #     clean_sig = re.sub(r'\{[0-9]\}','{}',raw_sig)
    #     # if sig_stack != '':
    #     #     clean_sig = clean_sig.format(','.join(sig_stack))
    #     #print(clean_sig)
    #     terminus = clean_sig.count('}')
    #     print('terminus:', terminus)
    #
    #     sig_stack = []
    #
    #     for x in range(terminus):
    #         key = '{}-{}-{}'.format(star, mcocjson, x)
    #         col = 'sig'+str(siglvl)
    #         value = get_csv_row('data/mcoc/sig_data.csv', 'unique', key)
    #         # print('sig:', value)
    #         if value is None:
    #             continue
    #         else:
    #             sig_stack.append(value[col])
    #     print('sig_stack: ', len(sig_stack), sig_stack)
    #
    #     if dbg:
    #         ret = ['** DEBUG **']
    #         ret.append('Title: '+ title)
    #         ret.append('title_lower: '+ title_lower)
    #         for k in simple:
    #             ret.append('Simple: '+ k)
    #         for k in desc:
    #             ret.append('Desc: '+ k)
    #             ret.append('    ' + Champion._sig_header(sigs[k]))
    #         ret.append('    ' + clean_sig)
    #         ret.append('    ' + ','.join(sig_stack))
    #         await self.bot.say('```{}```'.format('\n'.join(ret)))
    #
    #     #elif terminus > 0:
    #     if len(sig_stack) == terminus:
    #         clean_sig = clean_sig.format(*sig_stack)
    #         #print('Replacing ', terminus, 'x {} with values:', ','.join(sig_stack))
    #         #for value in sig_stack:
    #             #clean_sig = clean_sig.replace('{}', value, 1)
    #
    #     em = discord.Embed(color=champ.class_color, title=champ.full_name)
    #     if title in sigs:
    #         em.add_field(name=sigs[title], value='\n'.join([sigs[k] for k in simple]))
    #     else:
    #         em.add_field(name=sigs[title_lower], value='\n'.join([sigs[k] for k in simple]))
    #     em.add_field(name='Signature Level {}'.format(siglvl),
    #             value=clean_sig)
    #     em.set_thumbnail(url=champ.get_avatar())
    #     await self.bot.say(embed=em)

    @commands.command(aliases=['sig','signature'])
    async def champ_sig(self, *, champ : ChampConverterSig):
        '''Retrieve the Signature Ability of a Champion'''
        if champ.star == 5:
            await self.say_user_error("Sorry.  5{} data for any champion is not currently available".format(star_glyph[1]))
            return
        try:
            title, desc = await champ.process_sig_description()
        except KeyError:
            await champ.missing_sig_ad()
            return
        if title is None:
            return
        em = discord.Embed(color=champ.class_color, title=champ.full_name)
        em.add_field(name=title, value=champ.star_str)
        em.add_field(name='Signature Level {}'.format(champ.sig),  value=desc)
        em.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @commands.command(aliases=['abilities',])
    async def champ_abilities(self, champ : ChampConverter):
        '''In-Development: Retrieve Champion Abilities'''
        specials = champ.get_special_attacks()
        em = discord.Embed(color=champ.class_color,
        title=champ.full_name + 'Abilities')
        em.add_field(name='Passive',value='placeholder')
        em.add_field(name='All Attacks',value='placeholder')
        em.add_field(name='When Attacked',value='placeholder')
        em.set_thumbnail(url=champ.get_avatar())
        em2 = discord.Embed(color=champ.class_color,
        title=champ.full_name + ' Special Attacks')
        em2.add_field(name=specials[0], value=specials[3])
        em2.add_field(name=specials[1], value=specials[4])
        em2.add_field(name=specials[2], value=specials[5])
        em2.set_footer(text='MCOC Game Files', icon_url='https://imgur.com/UniRf5f.png')
        await self.bot.say(embed=em)
        await self.bot.say(embed=em2)

    # @commands.command()
    # async def sigarray(self, champ : ChampConverter, dbg=1, *args):
    #     '''Retrieve the Signature Ability of a Champion at multiple levels'''
    #     champ = self._resolve_alias(champ)
    #     title, desc = champ.get_sigarray(**self.settings)
    #     if dbg == 0:
    #         em = discord.Embed(color=champ.class_color, title=title,
    #                 description=desc)
    #     elif dbg == 1:
    #         em = discord.Embed(color=champ.class_color, title=champ.full_name)
    #         em.add_field(name='Signature Ability Array', value=desc)
    #     else:
    #         em = discord.Embed(color=champ.class_color, title=title)
    #         em.add_field(name='__SigLvl__', value='1\n20\n40')
    #         em.add_field(name='__X__', value='1.0\n1.9\n2.1', inline=True)
    #
    #     em.set_thumbnail(url=champ.get_avatar())
    #     await self.bot.say(embed=em)

    @commands.command(aliases=('prestige',))
    async def champ_prestige(self, *, champs : ChampConverterMult):
        '''Retrieve prestige data for champs'''
        em = discord.Embed(color=discord.Color.magenta(), title='Prestige')
        for champ in champs:
            try:
                # em.add_field(name=champ.coded_str, value=champ.prestige)
                #em.add_field(name=champ.star_name_str,
                        #value='{0.rank_sig_str}\n{0.prestige}'.format(champ),
                em.add_field(name=champ.full_name,
                        value='{0.stars_str}\n{0.rank_sig_str}\n{0.prestige}'.format(champ),
                        inline=False)
            except AttributeError:
                await self.bot.say("**WARNING** Champion Data for "
                    + "{} does not exist".format(champ.verbose_str))
        ##em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @commands.command(aliases=('calias',))
    async def champ_aliases(self, *args):
        '''Retrieve Champion Aliases'''
        champs_matched = []
        em = discord.Embed(color=discord.Color.teal(), title='Champion Aliases')
        for arg in args:
            if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')) :
                champs = self.search_champions(arg[1:-1])
            elif '*' in arg:
                champs = self.search_champions('.*'.join(re.split(r'\\?\*', arg)))
            else:
                champs = (self.get_champion(arg),)
            for champ in champs:
                if champ not in champs_matched:
                    em.add_field(name=champ.full_name, value=champ.get_aliases())
                    champs_matched.append(champ)
        await self.bot.say(embed=em)

    @commands.command()
    async def phc(self):
        '''Premium Hero Crystal Release Dates'''
        await self.bot.upload(data_files['phc_jpg']['local'],
                content='Dates Champs are added to PHC (and as 5* Featured for 2nd time)')


    @commands.command(hidden=True)
    async def tst(self, key):
        files = {'bio': (kabam_bio, 'ID_CHARACTER_BIOS_', 'mcocjson'),
                 'sig': (kabam_bcg_stat_en, 'ID_UI_STAT_', 'mcocsig')}
        ignore_champs = ('DRONE', 'SYMBIOD')
        if key not in files:
            await self.bot.say('Accepted Key values:\n\t' + '\n\t'.join(files.keys()))
            return
        data = load_kabam_json(files[key][0])
        no_mcocjson = []
        no_kabam_key = []
        data_keys = {k for k in data.keys() if k.startswith(files[key][1])}
        ignore_keys = set()
        for champ in ignore_champs:
            ignore_keys.update({k for k in data_keys if k.find(champ) != -1})
        data_keys -= ignore_keys
        print(ignore_keys)
        for champ in self.champs:
            if not getattr(champ, files[key][2], None):
                no_mcocjson.append(champ.full_name)
                continue
            kabam_key = files[key][1] + getattr(champ, files[key][2])
            champ_keys = {k for k in data.keys() if k.startswith(kabam_key)}
            if not champ_keys:
                no_kabam_key.append(champ.full_name)
            else:
                data_keys -= champ_keys
        if no_mcocjson:
            await self.bot.say('Could not find mcocjson alias for champs:\n\t' + ', '.join(no_mcocjson))
        if no_kabam_key:
            await self.bot.say('Could not find Kabam key for champs:\n\t' + ', '.join(no_kabam_key))
        if data_keys:
            #print(data_keys, len(data_keys))
            if len(data_keys) > 20:
                dump = {k for k in data_keys if k.endswith('TITLE')}
            else:
                dump = data_keys
            await self.bot.say('Residual keys:\n\t' + '\n\t'.join(dump))
        await self.bot.say('Done')

#My intention was to create a hook command group. If nothing is specified, then drop the URL

    def _prepare_aliases(self):
        '''Create a python friendly data structure from the aliases json'''
        raw_data = load_csv(data_files['crossreference']['local'])
        champs = []
        all_aliases = set()
        id_index = raw_data.fieldnames.index('status')
        alias_index = raw_data.fieldnames[:id_index-1]
        for row in raw_data:
            alias_set = set()
            for col in alias_index:
                if row[col]:
                    alias_set.add(row[col].lower())
            if all_aliases.isdisjoint(alias_set):
                all_aliases.union(alias_set)
            else:
                raise KeyError("There are aliases that conflict with previous aliases."
                        + "  First occurance with champ {}.".format(row['champ']))
            self.create_champion_class(self.bot, alias_set, **row)

    def _google_json_content_split(self, row):
            return dict([kv.split(': ') for kv in self.split_re.split(row['content']['$t'])])

    def _prepare_prestige_data(self):
        mattkraft_re = re.compile(r'(?P<star>\d)-(?P<champ>.+)-(?P<rank>\d)')
        raw_data = dataIO.load_json(data_files['prestige']['local'])
        champs = {}
        for row in raw_data['feed']['entry']:
            raw_dict = self._google_json_content_split(row)
            champ_match = mattkraft_re.fullmatch(raw_dict['mattkraftid'])
            if champ_match:
                champ_name = champ_match.group('champ')
                champ_star = int(champ_match.group('star'))
                champ_rank = int(champ_match.group('rank'))
            else:
                continue
            if champ_name not in champs:
                champs[champ_name] = {}
                champs[champ_name][4] = [None] * 5
                champs[champ_name][5] = [None] * 5
            if champ_star == 5:
                sig_len = 201
            else:
                sig_len = 100
            key_values = {}
            sig = [0] * sig_len
            for k, v in raw_dict.items():
                if k.startswith('sig'):
                    try:
                        if (int(k[3:]) < sig_len) and v != '#N/A':
                            sig[int(k[3:])] = int(v)
                    except:
                        print(champ_name, k, v, len(sig))
                        raise
            try:
                champs[champ_name][champ_star][champ_rank-1] = sig
            except:
                print(champ_name, champ_star, champ_rank, len(champs[champ_name]), len(champs[champ_name][champ_star]))
                raise
        dataIO.save_json(prestige_data, champs)
        for champ in self.champions.values():
            if champ.mattkraftid in champs:
                champ.prestige_data = champs[champ.mattkraftid]

    #def _prepare_signature_data(self):
        #raw_data = load_csv(local_files['sig_coeff'])

def validate_attr(*expected_args):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for attr in expected_args:
                if getattr(self, attr + '_data', None) is None:
                    raise AttributeError("{} for Champion ".format(attr.capitalize())
                        + "'{}' has not been initialized.".format(self.champ))
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class Champion:

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        self.debug = attrs.pop('debug', 0)
        default = {'star': 4, 'rank': 5, 'sig': 99}
        default.update(attrs)
        self.update_attrs(default)

    def update_attrs(self, attrs):
        for k in ('star', 'rank', 'sig'):
            if k in attrs:
                setattr(self, k, attrs[k])
        if self.sig < 0:
            self.sig = 0
        if self.star < 1:
            print('Star {} for Champ {} is too low.  Setting to 1'.format(
                    self.star, self.full_name))
            self.star = 1
        if self.star > 5:
            print('Star {} for Champ {} is too high.  Setting to 5'.format(
                    self.star, self.full_name))
            self.star = 5
        if self.star == 5:
            if self.rank > 5:
                self.rank = 5
            if self.sig > 200:
                self.sig = 200
        elif self.star < 5:
            if self.rank > (self.star + 1):
                self.rank = self.star + 1
            if self.sig > 99:
                self.sig = 99

    def get_avatar(self):
        image = '{}portraits/portrait_{}.png'.format(remote_data_basepath, self.mcocui)
        return image

    def get_featured(self):
        image = '{}uigacha/featured/GachaChasePrize_256x256_{}.png'.format(
                    remote_data_basepath, self.mcocui)
        return image

    async def get_bio(self):
        bios = load_kabam_json(kabam_bio)
        key = 'ID_CHARACTER_BIOS_' + self.mcocjson
        if key not in bios:
            raise KeyError('Cannot find Champion {} in data files'.format(self.full_name))
        if self.debug:
            dbg_str = 'BIO:  ' + key
            await self.bot.say('```{}```'.format(dbg_str))
        return bios[key]

    @property
    def star_str(self):
        return '{0.stars_str} {0.rank}/{0.max_lvl}'.format(self)

    @property
    def unique(self):
        return '{0.star}-{0.mattkraftid}-{0.rank}'.format(self)

    @property
    def coded_str(self):
        return '{0.star}*{0.short}r{0.rank}s{0.sig}'.format(self)

    @property
    def verbose_str(self):
        return '{0.stars_str} {0.full_name} r{0.rank}'.format(self)

    @property
    def star_name_str(self):
        return '{0.stars_str} {0.full_name}'.format(self)
        #return '{0.star}★ {0.full_name}'.format(self)

    @property
    def rank_sig_str(self):
        return '{0.rank}/{0.max_lvl} sig{0.sig}'.format(self)

    @property
    def stars_str(self):
        return '★' * self.star

    @property
    def chlgr_rating(self):
        if self.star == 1:
            return self.rank * 10
        else:
            return (2 * self.star - 3 + self.rank) * 10

    @property
    def max_lvl(self):
        if self.star < 5:
            return self.rank * 10
        else:
            return 15 + self.rank * 10

    def get_special_attacks(self):
        specials = load_kabam_json(kabam_special_attacks)
        prefix = 'ID_SPECIAL_ATTACK_'
        desc = 'DESCRIPTION_'
        zero = '_0'
        one = '_1'
        two = '_2'
        s0 = specials[prefix + self.mcocjson + zero]
        s1 = specials[prefix + self.mcocjson + one]
        s2 = specials[prefix + self.mcocjson + two]
        s0d = specials[prefix + desc + self.mcocjson + zero]
        s1d = specials[prefix + desc + self.mcocjson + one]
        s2d = specials[prefix + desc + self.mcocjson + two]
        specials = (s0, s1, s2, s0d, s1d, s2d)
        return specials

    @property
    @validate_attr('prestige')
    def prestige(self):
        if self.prestige_data[self.star][self.rank-1] is None:
            return 0
        return self.prestige_data[self.star][self.rank-1][self.sig]

    @validate_attr('prestige')
    def get_prestige_arr(self, rank, sig_arr, star=4):
        row = ['{}r{}'.format(self.short, rank)]
        for sig in sig_arr:
            try:
                row.append(self.prestige_data[star][rank-1][sig])
            except:
                print(rank, sig, self.prestige_data)
                raise
        return row

    async def missing_sig_ad(self):
        em = discord.Embed(color=self.class_color,
                title='Signature Data is Missing')
        em.add_field(name=self.full_name,
                value='Contribute your data at http://discord.gg/wJqpYGS')
        await self.bot.say(embed=em)

    async def process_sig_description(self):
        brkt_re = re.compile(r'{([0-9])}')
        sigs = load_kabam_json(kabam_bcg_stat_en)
        title, title_lower, simple, desc = self.get_mcoc_keys()
        if self.debug:
            dbg_str = ['Title:  ' + title]
            dbg_str.append('Simple:  ' + ', '.join(simple))
            dbg_str.append('Description Keys:  ')
            dbg_str.append('  ' + ', '.join(desc))
            dbg_str.append('Description Text:  ')
            dbg_str.extend(['  ' + self._sig_header(sigs[d]) for d in desc])
            await self.bot.say('```{}```'.format('\n'.join(dbg_str)))
        coeff = self.get_sig_coeff()
        ekey = self.get_effect_keys()
        spotlight = self.get_spotlight()
        if coeff is None:
            print('get_sig_coeff returned None')
        if ekey is None:
            print('get_effect_keys returned None')
        if coeff is None or ekey is None:
            raise KeyError("Missing Sig data for {}".format(self.full_name))
        if self.sig == 0:
            return sigs[title], '\n'.join([sigs[k] for k in simple])
        sig_calcs = {}
        ftypes = {}
        data_missing = False
        for i in map(str, range(6)):
            if not ekey['Location_' + i]:
                break
            effect = ekey['Effect_' + i]
            try:
                m = float(coeff['ability_norm' + i])
                b = float(coeff['offset' + i])
            except:
                #await self.bot.say("Missing data for champion '{}'.  Try again later".format(self.full_name))
                await self.missing_sig_ad()
                self.update_attrs({'sig': 0})
                return sigs[title], '\n'.join([sigs[k] for k in simple])
                #return None
            ckey = ekey['Location_' + i]
            raw_str = '{:.2f}'
            raw_per_str = '{:.2%}'
            per_str = '{:.2f} ({:.2%})'

            if effect == 'rating':
                sig_calcs[ckey] = raw_str.format(m * self.chlgr_rating + b)
                continue
            per_val = m * log(self.sig) + b
            if effect == 'flat':
                sig_calcs[ckey] = per_str.format(
                        to_flat(per_val, self.chlgr_rating), per_val/100)
            elif effect == 'attack':
                if not spotlight['attack']:
                    data_missing = True
                    sig_calcs[ckey] = raw_per_str.format(per_val/100)
                    continue
                sig_calcs[ckey] = per_str.format(
                        int(spotlight['attack']) * per_val / 100, per_val/100)
            elif effect == 'health':
                if not spotlight['health']:
                    data_missing = True
                    sig_calcs[ckey] = raw_per_str.format(per_val/100)
                    continue
                sig_calcs[ckey] = per_str.format(
                        int(spotlight['health']) * per_val / 100, per_val/100)
            else:
                if per_val.is_integer():
                    sig_calcs[ckey] = '{:.0f}'.format(per_val)
                else:
                    sig_calcs[ckey] = raw_str.format(per_val)

        if data_missing:
            await self.bot.say('Missing Attack/Health info for {} {}'.format(
                    self.full_name, self.star_str))
        fdesc = []
        for i, kabam_key in enumerate(desc):
            fdesc.append(brkt_re.sub(r'{{d[{0}-\1]}}'.format(i),
                        self._sig_header(sigs[kabam_key])))
        if self.debug:
            await self.bot.say('```{}```'.format('\n'.join(fdesc)))
        return sigs[title], '\n'.join(fdesc).format(d=sig_calcs)

    def get_mcoc_keys(self):
        sigs = load_kabam_json(kabam_bcg_stat_en)
        mcocsig = self.mcocsig
        preamble = None
        title = None
        title_lower = None
        simple = []
        desc = []

        if mcocsig == 'COMICULTRON':
            mcocsig = 'DRONE_TECH'
        elif mcocsig == 'CYCLOPS_90S':
            mcocsig = 'CYCLOPS'

        titles = ('ID_UI_STAT_SIGNATURE_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_{}_SIGNATURE_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIG_{}_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIGNATURE_TITLE'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIG_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_FORMAT_{}_SIG_TITLE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_{}_SIG_TITLE'.format(mcocsig),
            )

        for x in titles:
            if x in sigs:
                title = x

        if title is None:
            raise KeyError('DEBUG - title not found')
        elif title + '_LOWER' in sigs:
            title_lower = title + '_LOWER'

        if self.mcocsig == 'COMICULTRON':
            mcocsig = self.mcocsig  # re-init for Ultron Classic

        preambles = ('ID_UI_STAT_SIGNATURE_{}'.format(mcocsig),
            'ID_UI_STAT_{}_SIGNATURE'.format(mcocsig),
            'ID_UI_STAT_SIG_{}'.format(mcocsig),
            'ID_UI_STAT_ATTRIBUTE_{}_SIGNATURE'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_FORMAT_{}_SIG'.format(mcocsig),
            'ID_UI_STAT_SIGNATURE_{}_SIG'.format(mcocsig),
            )

        for x in preambles:
            if x + '_SIMPLE' in sigs:
                preamble = x
                break

        # if preamble is 'undefined':
        #     raise KeyError('DEBUG - Preamble not found')
        if preamble + '_SIMPLE_NEW' in sigs:
            simple.append(preamble + '_SIMPLE_NEW')
        elif preamble + '_SIMPLE' in sigs:
            simple.append(preamble + '_SIMPLE')
        else:
            raise KeyError('Signature SIMPLE cannot be found with: {}_SIMPLE'.format(preamble))

        champ_exceptions = {
            #'CYCLOPS_90S': ['ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO'],
            'CYCLOPS_90S': ['ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO'],
            'LOKI': ['ID_UI_STAT_SIGNATURE_LOKI_LONGDESC'],
            'DEADPOOL': ['ID_UI_STAT_SIGNATURE_DEADPOOL_DESC2_AO'],
            #'ULTRON': ['ID_UI_STAT_SIGNATURE_ULTRON_DESC'],
            #'COMICULTRON': ['ID_UI_STAT_SIGNATURE_ULTRON_DESC'],
            'IRONMAN_SUPERIOR': ['ID_UI_STAT_SIGNATURE_IRONMAN_DESC_AO',
                    'ID_UI_STAT_SIGNATURE_IRONMAN_DESC_B_AO'],
            'BEAST': ['ID_UI_STAT_SIGNATURE_LONGDESC_AO',
                    'ID_UI_STAT_SIGNATURE_LONGDESC_B_AO',
                    'ID_UI_STAT_SIGNATURE_LONGDESC_C_AO',
                    'ID_UI_STAT_SIGNATURE_LONGDESC_D_AO',
                    'ID_UI_STAT_SIGNATURE_LONGDESC_E_AO'],
            'GUILLOTINE': ['ID_UI_STAT_SIGNATURE_GUILLOTINE_DESC'],
            'NEBULA': ['ID_UI_STAT_SIGNATURE_NEBULA_LONG'],
            'RONAN': ['ID_UI_STAT_SIGNATURE_RONAN_DESC_AO'],
            'MORDO': ['ID_UI_STAT_SIG_MORDO_DESC_AO'],
        }

        if self.mcocsig == 'CYCLOPS_90S':
            desc.append('ID_UI_STAT_SIGNATURE_CYCLOPS_DESC_90S_AO')
        elif mcocsig in champ_exceptions:
            desc.extend(champ_exceptions[mcocsig])
        elif preamble + '_DESC_NEW' in sigs:
            for k in ('_DESC_NEW','_DESC_NEW_B'):
                if preamble + k in sigs:
                    if preamble + k + '_AO' in sigs:
                        desc.append(preamble + k + '_AO')
                    else:
                        desc.append(preamble + k)
        elif preamble + '_5STAR_DESC_MOD' in sigs:
            desc.append(preamble+'_DESC_MOD')
        else:
            for k in ('_DESC','_DESC_A','_DESC_B'):
                if preamble + k + '_UPDATED' in sigs:
                    k = k + '_UPDATED'
                if preamble + k in sigs:
                    if preamble + k + '_ALT' in sigs:
                        desc.append(preamble + k + '_ALT')
                    elif preamble + k + '_AO' in sigs:
                        desc.append(preamble + k + '_AO')
                    else:
                        desc.append(preamble + k)

        #print(desc)
        return title, title_lower, simple, desc

    def get_sig_coeff(self):
        return get_csv_row(local_files['sig_coeff'], 'CHAMP', self.full_name)

    def get_effect_keys(self):
        return get_csv_row(local_files['effect_keys'], 'CHAMP', self.full_name)

    def get_spotlight(self, default=None):
        return get_csv_row(data_files['spotlight']['local'], 'unique',
                self.unique, default=default)

    def get_aliases(self):
        return '```{}```'.format(', '.join(self.alias_set))

    @staticmethod
    def _sig_header(str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return '• ' + hex_re.sub(r'**\1**', str_data)

def bound_lvl(siglvl, max_lvl=99):
    if isinstance(siglvl, list):
        ret = []
        for j in siglvl:
            if j > max_lvl:
                j = max_lvl
            elif j < 0:
                j = 0
            ret.append(j)
    else:
        ret = siglvl
        if siglvl > max_lvl:
            ret = max_lvl
        elif siglvl < 0:
            ret = 0
    return ret

def tabulate(table_data, width, do_rotate=True, header_sep=True):
    rows = []
    cells_in_row = None
    for i in rotate(table_data, rotate):
        if cells_in_row is None:
            cells_in_row = len(i)
        elif cells_in_row != len(i):
            raise IndexError("Array is not uniform")
        rows.append('|'.join(['{:^{width}}']*len(i)).format(*i, width=width))
    if header_sep:
        rows.insert(1, '|'.join(['-' * width] * cells_in_row))
    return '```' + '\n'.join(rows) + '```'

def rotate(array, do_rotate):
    if not do_rotate:
        for i in array:
            yield i
    for j in range(len(array[0])):
        row = []
        for i in range(len(array)):
            row.append(array[i][j])
        yield row

def load_kabam_json(file):
    raw_data = dataIO.load_json(file)
    data = {}
    for d in raw_data['strings']:
        data[d['k']] = d['v']
    return data

def _truncate_text(self, text, max_length):
    if len(text) > max_length:
        if text.strip('$').isdigit():
            text = int(text.strip('$'))
            return "${:.2E}".format(text)
        return text[:max_length-3] + "..."
    return text

def get_csv_row(filecsv, column, match_val, default=None):
    csvfile = load_csv(filecsv)
    for row in csvfile:
        if row[column] == match_val:
            if default is not None:
                for k, v in row.items():
                    if v == '':
                        row[k] = default
            return row

def get_csv_rows(filecsv, column, match_val, default=None):
    csvfile = load_csv(filecsv)
    package =[]
    for row in csvfile:
        if row[column] == match_val:
            if default is not None:
                for k, v in row.items():
                    if v == '':
                        row[k] = default
            package.append(row)
    return package

def load_csv(filename):
    return csv.DictReader(open(filename))



# Creation of lookup functions from a tuple through anonymous functions
#for fname, docstr, link in MCOC.lookup_functions:
    #async def new_func(self):
        #await self.bot.say('{}\n{}'.format(docstr, link))
        #raise Exception
    ##print(new_func)
    ##setattr(MCOC, fname, commands.command(name=fname, help=docstr)(new_func))
    #new_func = commands.command(name=fname, help=docstr)(new_func)
    #setattr(MCOC, fname, new_func)
    ##print(getattr(MCOC, fname).name, getattr(MCOC, fname).callback)



def setup(bot):
    bot.add_cog(MCOC(bot))
