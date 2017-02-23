import re
from datetime import datetime
from textwrap import wrap
from math import log2
import os
import inspect
import urllib
import requests
import json
import asyncio
from functools import wraps
import discord
from discord.ext import commands
from .utils.dataIO import dataIO

## Class : Champion Parser

## Command list
## Spotlight - done
## Event/Events - done
## Sig
### Sig <champ> <value>
## Warmap
### Warmap <lanelane>
## Sig
### Sig <champ> <value>
## Roster
## PlayerCards
### Username
### Mastery Rig link
### Frogspawn Card Link
### Member Since
### Avatar
## Howto <fight|use> <Champion>
## About <Champion>

json_data = {
    'frogspawn': {'remote': 'http://coc.frogspawn.de/champions/js/champ_data.json',
               'local':'data/mcoc/frogspawn_data.json'},
    'spotlight': {'remote': 'https://spreadsheets.google.com/feeds/list/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/1/public/values?alt=json',
                'local': 'data/mcoc/spotlight_data.json'},
    'crossreference': {'remote': 'https://spreadsheets.google.com/feeds/list/1QesYLjDC8yd4t52g4bN70N8FndJXrrTr7g7OAS0BItk/1/public/values?alt=json',
                'local': 'data/mcoc/crossreference.json'},
## prestige - strictly the export of mattkraft's prestige table
    'prestige': {'remote': 'https://spreadsheets.google.com/feeds/list/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/2/public/values?alt=json',
                'local': 'data/mcoc/prestige.json'},
    'five-star-sig': {'remote':'https://spreadsheets.google.com/feeds/list/1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg/3/public/values?alt=json',
                'local': 'data/mcoc/five-star-sig.json'},
    'four-star-sig': {'remote':'https://spreadsheets.google.com/feeds/list/1kNvLfeWSCim8liXn6t0ksMAy5ArZL5Pzx4hhmLqjukg/4/public/values?alt=json',
                'local': 'data/mcoc/five-star-sig.json'},
### coefficient by rank is HOOK's prestige coefficients.  But I am uncertain of generation process.
##   'coefficient-by-rank': {'remote': 'https://github.com/hook/champions/blob/master/src/data/pi/coefficient-by-rank.json',
##               'local': 'data/mcoc/coefficient-by-rank.json'},
    }

prestige_data = 'data/mcoc/prestige_data.json'
champ_crossreference_json_debug='https://spreadsheets.google.com/feeds/list/112Q53wW0JX2Xt8BLgQlnpieiz8f9mR0wbfqJdHubd64/1/public/values?alt=json'
champ_portraits='data/mcoc/portraits/portrait_'
champ_featured='data/mcoc/uigacha/featured/GachaChasePrize_256x256_'
lolmap_path='data/mcoc/maps/lolmap.png'
champ_avatar='http://www.marvelsynergy.com/images/'

#spotlight_json=requests.get('https://spreadsheets.google.com/feeds/list/1I3T2G2tRV05vQKpBfmI04VpvP5LjCBPfVICDmuJsjks/1/public/values?alt=json')
#spotlight_data=spotlight_json.json()
#with open('data/mcoc/spotlight_data.json','w') as outfile:
#    json.dump(spotlight_data,outfile)
#
#frogspawn_json=requests.get('http://coc.frogspawn.de/champions/js/champ_data.json')
#frogspawn_data=frogspawn_json.json()
#with open('data/mcoc/frogspawn_data.json', 'w') as outfile:
#    json.dump(frogspawn_data,outfile)

class_color_codes = {
        'Cosmic': discord.Color(0x2799f7), 'Tech': discord.Color(0x0033ff),
        'Mutant': discord.Color(0xffd400), 'Skill': discord.Color(0xdb1200),
        'Science': discord.Color(0x0b8c13), 'Mystic': discord.Color(0x7f0da8),
        'All': discord.Color(0xffffff), 'default': discord.Color.light_grey(),
        }


def alias_resolve(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        for i in range(len(args)):
            args[i] = self._resolve_alias(args[i])
        return f(self, *args, **kwargs)
    return wrapper

class MCOC:
    '''A Cog for Marvel's Contest of Champions'''

    lookup_links = {
            'event': (
                'Tiny MCoC Schedule',
                '<http://simians.tk/MCOC-Sched>'),
            'spotlight': (
                'MCoC Spotlight',
                '<http://simians.tk/MCoCspotlight>'),
            'marvelsynergy': (
                'Marvel Synergy Builder',
                '<http://www.marvelsynergy.com/team-builder>'),
            'hook': (
                'Hook Roster Manager',
                '<http://hook.github.io/champions>'),
            'frogspawn': (
                'Champion Signature Abilities',
                '<http://coc.frogspawn.de/champions>'),
            'alsciende':(
                'Alsciende Mastery Tool',
                '<https://alsciende.github.io/masteries/v10.0.1/#>'),
            'simulator': (
                'Mastery Simulator',
                '<http://simians.tk/msimSDF>'),
            'streak': (
                'Infinite Streak',
                'http://simians.tk/-sdf-streak')
                #'http://simians.tk/SDFstreak')
            }

    warmap_links = {
            '': (
                'AW Map',
                'http://i.imgur.com/h1N8O4R.png'),
            'eh': (
                'AW Map E-H',
                'http://i.imgur.com/ACw1wS3.png'),
            'af': (
                'AW Map A-F',
                'http://i.imgur.com/p5F0L6I.png'),
            'eg': (
                'AW Map E-G',
                'http://i.imgur.com/Gh9EK8N.png'),
            'eg+': (
                'AW Map E to G+',
                'http://i.imgur.com/l9KxWHJ.png'),
            'df': (
                'AW Map D to F',
                'http://i.imgur.com/zlGSwbj.png'),
            'ei': (
                'AW Map E to I',
                'http://i.imgur.com/JUTXNpf.png'),
            'ag+': (
                'AW Map A to G+',
                'http://i.imgur.com/KTZrCZN.png'),
            'dg+': (
                'AW Map D to G+',
                'http://i.imgur.com/3kmzhIG.png'),
            'ci': (
                'AW Map C to I',
                'http://i.imgur.com/BBFc0GS.png'),
            'dh': (
                'AW Map D to H',
                'http://i.imgur.com/DlnHQ0F.png'),
            'ag': (
                'AW Map A to G',
                'http://i.imgur.com/oQNRLTA.png'),
            'cf': (
                'AW Map C to F',
                'http://i.imgur.com/IcVC0Y8.png'),
            'ef': (
                'AW Map E to F ',
                'http://i.imgur.com/eiftXZK.png'),
            'cg+': (
                'AW Map C to G+',
                'http://i.imgur.com/smlAKwu.png'),
            'di': (
                'AW Map D to I',
                'http://i.imgur.com/WIMHR7t.png'),
            'ch': (
                'AW Map C to H',
                'http://i.imgur.com/uBpUC0y.png'),
            'bg': (
                'AW Map B to G',
                'http://i.imgur.com/hlMU7vw.png'),
            'dg': (
                'AW Map D to G',
                'http://i.imgur.com/WI7SxWT.png'),
            'ai': (
                'AW Map A to I',
                'http://i.imgur.com/h1N8O4R.png'),
            'bg+': (
                'AW Map B to G+',
                'http://i.imgur.com/i2xh3eM.png'),
            'bi': (
                'AW Map B to I',
                'http://i.imgur.com/Um06tbU.png'),
            'cg': (
                'AW Map C to G',
                'http://i.imgur.com/wM0LSed.png'),
            'bh': (
                'AW Map B to H',
                'http://i.imgur.com/gug9NyC.png'),
            'af': (
                'AW Map B to F',
                'http://i.imgur.com/0NOI2lK.png'),
            'ah': (
                'AW Map A to H',
                'http://i.imgur.com/6c96hBj.png')
            }

    lessons = {
            'parry': (
                'How to Parry Like a Boss',
                'https://www.youtube.com/watch?v=VRPXxHrgDnY',
                '```Parry Types:\n1. The First Kiss\n2. The Cherry Picker\n3. Quick Draw\n4. The Second Coming\n~~5. Unspecial~~```'),
            'thor': (
                'How to Use Duped Thor',
                'https://www.youtube.com/watch?v=Ng31Ow1SNOk',
                '```Evade, crit boost. >> Parry, stun. >> L3 destroyz```\nAdvanced: **Minimum Stun Duration**\nReduce your stun duration, or use against War opponents with Limber 5.\nParry. As soon as the parry debuff cycles, Parry again, stacking debuff.\nStack up to 4 or 5 debuffs.\nL3 destroys.'),
            'magik': (
                'How to Magik',
                'https://www.youtube.com/watch?v=zC47YeI1b8g',
                "```Magik's L3 increases Attack 50% for every enemy buff Nullified.```\nWait until the target has stacked many buffs, then drop the L3.\nThis is excellent versus Venom and Groot")
            }

    def __init__(self, bot):
        self.bot = bot

        self.settings = {
                'siglvl': 1,
                'sigstep': 20,
                'table_width': 10,
                'sig_inc_zero': False,
                }

        for val in json_data.values():
            self.cache_json_file(**val)

        self._prepare_aliases()
        self._prepare_frogspawn_champ_data()
        self._prepare_prestige_data()
        # self._prepare_spotlight_data()

    @commands.command()
    async def mcocset(self, setting, value):
        if setting in self.settings:
            self.settings[setting] = int(value)

    @commands.command(help=lookup_links['event'][0])
    async def event(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['event']))

    @commands.command(help=lookup_links['event'][0])
    async def events(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['event']))

    @commands.command(help=lookup_links['spotlight'][0])
    async def spotlight(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['spotlight']))

    @commands.command(help=lookup_links['hook'][0])
    async def hook(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['hook']))

    @commands.command(help=lookup_links['frogspawn'][0])
    async def frogspawn(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['frogspawn']))

    @commands.command(help=lookup_links['marvelsynergy'][0])
    async def marvelsynergy(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['marvelsynergy']))

    @commands.command(help=lookup_links['simulator'][0])
    async def simulator(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['simulator']))

    @commands.command(help=lookup_links['alsciende'][0])
    async def alsciende(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['alsciende']))

    @commands.command(help=lookup_links['alsciende'][0])
    async def mrig(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['alsciende']))

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['streak']))

    @commands.command(pass_context=True)
    async def lolmap(self, ctx):
        '''Labrynth of Legends Map'''
        channel=ctx.message.channel
        await self.bot.send_file(channel, lolmap_path, content='**LABYRINTH OF LEGENDS Map by Frogspawn**')

    @commands.command()
    async def howto(self, choice=None):
        if choice in self.lessons:
            #title, url, desc = self.lessons[choice]
            #em = discord.Embed(title=title, description=desc, url=url)
            #await self.bot.say(embed=em)
            await self.bot.say('**{}**\n{}\n{}'.format(*self.lessons[choice]))
        else:
            sometxt = 'Choose'
            em = discord.Embed(title=sometxt, description='\n'.join(self.lessons.keys()))
            await self.bot.say(embed=em)
            #await self.bot.say(sometxt + '\n'.join(self.lessons.keys()))

    def cache_json_file(self, remote=None, local=None):
        resp = requests.get(remote)
        copy_to_cache = self.check_local_remote_timestamp(resp, local)
        if copy_to_cache:
            #await self.bot.say('Caching remote contents to local file: ' + local)
            print('Caching remote contents to local file: ' + local)
            fp = open(local, 'wb')
            for chunk in resp.iter_content():
                fp.write(chunk)
        else:
            #await self.bot.say('Local file up-to-date: ' + local)
            print('Local file up-to-date: ' + local)
        #self.report_cache_status(local, copy_to_cache)

    #async def report_cache_status(self, local, caching_statuIs):
        #if caching_status:
            #await self.bot.say('Caching remote contents to local file: ' + local)
        #else:
            #await self.bot.say('Local file up-to-date: ' + local)

    def check_local_remote_timestamp(self, resp, local):
        strf_remote = '%a, %d %b %Y %H:%M:%S %Z'
        if os.path.exists(local):
            remote_dt = datetime.strptime(resp.headers['Last-Modified'], strf_remote)
            local_dt = datetime.fromtimestamp(os.path.getmtime(local))
            copy_to_cache = remote_dt > local_dt
        else:
            copy_to_cache = True
        return copy_to_cache

    @commands.command(pass_context=True)
    async def phc(self,ctx):
        '''Premium Hero Crystal Release Dates'''
        channel=ctx.message.channel
        await self.bot.say('<http://marvelbitvachempionov.ru/wp-content/dates_PCHen.jpg>')

    @commands.command(pass_context=True)
    async def portrait(self, ctx, champ):
        '''View Champion Portraits'''
        channel=ctx.message.channel
        champ = self._resolve_alias(champ)
        #em = discord.Embed(title=champ.full_name).set_image(url=champ.get_portrait())
        #await self.bot.say(embed=em)
        await self.bot.send_file(channel, champ.get_portrait(), content=champ.bold_name)

    @commands.command(pass_context=True)
    async def featured(self, ctx, champ):
        '''View Champion Feature Images'''
        channel=ctx.message.channel
        champ = self._resolve_alias(champ)
        await self.bot.send_file(channel, champ.get_featured(), content=champ.bold_name)

    @commands.command(pass_context=True)
    async def warmap(self, ctx, maptype='ai', link=False):
        '''Select a Warmap
        syntax: /warmap <left><right>
        Where <left> = [a, b, c, d, e]
        Where <right> = [f, g, g+, h, i]'''
        channel = ctx.message.channel
        filepath_png = 'data/mcoc/warmaps/warmap_{}.png'
        maps = {'af','ag','ag+','ah','ai','bf','bg','bg+','bh','bi','cf','cg',
                'cg+','ch','ci','df','dg','dg+','dh','ef','eg','eg+','eh','ei'}
        if maptype in maps:
            mapTitle = '**Alliance War Map {}**'.format(maptype.upper())
            if link:
                filepath = self.warmap_links[maptype][1]
                em = discord.Embed(title=mapTitle).set_image(url=filepath)
                await self.bot.say(embed=em)
            else:
                filepath = filepath_png.format(maptype.lower())
                await self.bot.send_file(channel, filepath, content=mapTitle)
        else :
            raise KeyError('Summoner, I cannot find that map with arg <{}>'.format(maptype))

    #@alias_resolve
    @commands.command()
    async def bio(self, champ):
        '''Retrieve the Bio of a Champion'''
        champ = self._resolve_alias(champ)
        em = discord.Embed(color=champ.class_color, title=champ.full_name,
                description=champ.get_bio())
        em.set_thumbnail(url=champ.get_avatar())
        #em.set_thumbnail(url=champ.get_portrait())
        await self.bot.say(embed=em)

    @commands.command()
    async def sig(self, champ, siglvl=None, dbg=0, *args):
        '''Retrieve the Signature Ability of a Champion'''
        champ = self._resolve_alias(champ)
        settings = self.settings.copy()
        if siglvl is not None:
            settings['siglvl'] = int(siglvl)
        title, desc, siglvl = champ.get_sig(**settings)
        if dbg == 0:
            em = discord.Embed(color=champ.class_color, title=champ.full_name)
            em.add_field(name='Signature Level '+str(siglvl),  value=desc)
        elif dbg == 1:
            em = discord.Embed(color=champ.class_color, title='Signature Ability')
            em.add_field(name='@ Level', value=siglvl)
            em.add_field(name = champ.full_name, value=desc)
        else:
            em = discord.Embed(color=champ.class_color,
                title=champ.full_name + ' Signature Ability')
            em.add_field(name='Level '+str(siglvl),  value=desc)
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @commands.command()
    async def sigarray(self, champ, dbg=1, *args):
        '''Retrieve the Signature Ability of a Champion at multiple levels'''
        champ = self._resolve_alias(champ)
        title, desc = champ.get_sigarray(**self.settings)
        if dbg == 0:
            em = discord.Embed(color=champ.class_color, title=title,
                    description=desc)
        elif dbg == 1:
            em = discord.Embed(color=champ.class_color, title=champ.full_name)
            em.add_field(name='Signature Ability Array', value=desc)
        else:
            em = discord.Embed(color=champ.class_color, title=title)
            em.add_field(name='__SigLvl__', value='1\n20\n40')
            em.add_field(name='__X__', value='1.0\n1.9\n2.1', inline=True)

        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    @commands.command()
    async def prestige(self, champ):
        champ = self._resolve_alias(champ)
        title, desc = champ.get_prestige(**self.settings)
        em = discord.Embed(color=champ.class_color, title=title,
                description=desc)
        em.set_thumbnail(url=champ.get_avatar())
        await self.bot.say(embed=em)

    #@commands.command()
    #async def champ_stats(self, star=4, champ, rank=5):
    #    '''JJW trying to get Spotlight data'''
    #    champ = self._resovle_alias(champ)


    @commands.command()
    async def champ_aliases(self, *args):
        champs_matched = []
        em = discord.Embed(color=discord.Color.teal(), title='Champion Aliases')
        for arg in args:
            if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')) :
                champs = self._resolve_mult_aliases(arg[1:-1])
            elif '*' in arg:
                champs = self._resolve_mult_aliases('.*'.join(arg.split('*')))
            else:
                champs = (self._resolve_alias(arg),)
            for champ in champs:
                if champ not in champs_matched:
                    #print(champ.alias_set)
                    em.add_field(name=champ.full_name, value=champ.get_aliases())
                    champs_matched.append(champ)
        await self.bot.say(embed=em)

    def _prepare_aliases(self):
        '''Create a python friendly data structure from the aliases json'''
        #response = urllib.request.urlopen(json_data['crossreference']['local'])
        #response = urllib.request.urlopen(champ_crossreference_json_debug)
        fp = open(json_data['crossreference']['local'], encoding='utf-8')
        #raw_data = json.loads(response.read().decode('utf-8'))
        raw_data = json.load(fp)
        champs = []
        all_aliases = set()
        id_index = False
        for row in raw_data['feed']['entry']:
            cells = row['content']['$t'].split(', ')
            if id_index is False:
                id_index = 0
                for i in cells:
                    id_index += 1
                    if i.startswith('champ:'):
                        break
            key_values = {}
            alias_set = set()
            for i in range(len(cells)):
                k, v = cells[i].split(': ')
                key_values[k] = v
                if i < id_index:
                    if v != 'n/a':
                        alias_set.add(v.lower())
            if all_aliases.isdisjoint(alias_set):
                all_aliases.union(alias_set)
            else:
                raise KeyError("There are aliases that conflict with previous aliases."
                        + "  First occurance with champ {}.".format(key_values['champ']))
            #champs.append(Champion(alias_set, **key_values, debug=len(champs)==0))
            champs.append(Champion(alias_set, **key_values))
        self.champs = champs

    def _prepare_frogspawn_champ_data(self):
        #response = urllib.request.urlopen(champ_data_json)
        #response = urllib.request.urlopen(json_data['frogspawn']['remote'])
        #champ_data = json.loads(response.read().decode('utf-8'))
        fp = open(json_data['frogspawn']['local'], encoding='utf-8')
        champ_data = json.load(fp)
        for champ in self.champs:
            if getattr(champ, 'frogspawnid', None):
                champ.update_frogspawn(champ_data.get(champ.frogspawnid))

    def _resolve_alias(self, alias):
        for champ in self.champs:
            if champ.re_alias.fullmatch(alias):
                return champ
        raise KeyError("Champion for alias '{}' not found".format(alias))

    def _resolve_mult_aliases(self, match_str):
        re_champ = re.compile(match_str)
        champs = []
        for champ in self.champs:
            for alias in champ.alias_set:
                if re_champ.fullmatch(alias):
                    champs.append(champ)
                    break
        return champs

## I replaced 'spotlight' with 'prestige'
    def _prepare_prestige_data(self):
        fp = open(json_data['prestige']['local'], encoding='utf-8')
        raw_data = json.load(fp)
        champs = {}
        for row in raw_data['feed']['entry']:
            #cells = row['content']['$t'].split(', ')
            raw_dict = dict([kv.split(': ') for kv in re.split(', (?=\w+:)', row['content']['$t'])])
            if 'champ' not in raw_dict:
                continue
            champ_name = raw_dict['champ']
            if champ_name not in champs:
                champs[champ_name] = {}
                champs[champ_name][4] = [None] * 5
                champs[champ_name][5] = [None] * 4
            if int(raw_dict['star']) == 5:
                sig_len = 200
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
                #else:
                    #key_values[k] = v
            champs[champ_name][int(raw_dict['star'])][int(raw_dict['rank'])-1] = sig
        dumpfp = open(prestige_data, 'w')
        json.dump(champs, dumpfp)
        for champ in self.champs:
            if champ.full_name in champs:
                champ.prestige_data = champs[champ.full_name]

    # def _prepare_spotlight_data(self):
    #     fp = open(json_data['spotlight']['local'],encoding='utf-8')
    #     raw_data = json.load(fp)
    #     champs = {}


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

    def __init__(self, alias_set, *args, debug=0, **kwargs):
        self.alias_set = alias_set
        self.re_alias = re.compile('|'.join(alias_set), re.I)
        self.frogspawn_data = None
        if debug:
            print(kwargs)
        for key, value in kwargs.items():
            if value == 'n/a':
                value = None
            setattr(self, key, value)
        self.full_name = self.champ
        self.bold_name = '**' + ' '.join(
            [word.capitalize() for word in self.full_name.split(' ')]) + '**'
        self.class_color = class_color_codes[getattr(self, 'class', 'default')]

    def update_frogspawn(self, data):
        self.frogspawn_data = data

    def getSigValue(self, siglvl, i=None):
        '''Python port of siglvl interpolator from
        http://coc.frogspawn.de/champions/js/functions.js'''
        if i is None:
            base = self.frogspawn_data['sb']
            multi = self.frogspawn_data['sm']
        else:
            base = self.frogspawn_data['sb'][i]
            multi = self.frogspawn_data['sm'][i]
        if siglvl > 0 and base:
            return round(base + log2(siglvl) * multi, 1)
        else:
            return '-'

    def get_avatar(self):
        return '{}{}.png'.format(champ_avatar, self.marvelthumbnail)

    def get_portrait(self):
        return '{}{}.png'.format(champ_portraits, self.mcocui)

    def get_featured(self):
        return '{}{}.png'.format(champ_featured, self.mcocui)

    @validate_attr('frogspawn')
    def get_bio(self):
        return self.frogspawn_data['bio']

    @validate_attr('frogspawn')
    def get_sig(self, **kwargs):
        sig_str = self._sig_header(self.frogspawn_data['sd'])
        siglvl = self.bound_lvl(kwargs['siglvl'])
        str_data = []
        for i in range(len(self.frogspawn_data['sn'])):
            if self.frogspawn_data['sn'][i] != 0:
                str_data.append(self.frogspawn_data['sn'][i])
            elif isinstance(self.frogspawn_data['sb'], list):
                str_data.append(self.getSigValue(siglvl, i))
            else:
                str_data.append(self.getSigValue(siglvl))
        return ('Signature Ability for {}'.format(
                self.full_name.capitalize()), sig_str.format(*str_data), siglvl)

    @validate_attr('frogspawn')
    def get_sigarray(self, sigstep=20, width=10, inc_zero=False, **kwargs):
        '''Retrieve the Signature Ability of a Champion at multiple levels'''
        var_list = 'XYZABCDEF'
        sig_str = self._sig_header(self.frogspawn_data['sd'])
        str_data = []
        sigstep_arr = self.bound_lvl(list(range(0, 101, sigstep)))
        if inc_zero:
            sigstep_arr.insert(1, 1)
        else:
            sigstep_arr[0] = 1
        table_data = [[''] + sigstep_arr]
        count = 0
        for i in range(len(self.frogspawn_data['sn'])):
            if self.frogspawn_data['sn'][i] != 0:
                str_data.append(self.frogspawn_data['sn'][i])
            elif '{' + str(i) + '}' in sig_str:
                table_data.append([var_list[count]])
                str_data.append(var_list[count])
                for j in sigstep_arr:
                    if isinstance(self.frogspawn_data['sb'], list):
                        table_data[-1].append(self.getSigValue(j, i))
                    else:
                        table_data[-1].append(self.getSigValue(j))
                count += 1
            else:
                # nothing to do if there is no valid sub in sig_str
                #  but we need to make sure the length is correct for format
                str_data.append('dummy')
        title = 'Signature Ability for {} at multiple Sig Levels:'.format(
                self.bold_name)
        response = sig_str.format(*str_data) + self._tabulate(table_data, width=width)
        return (title, response)

 #   @validate_attr('spotlight')
 #   def get_spotlight(self, rank=None, star=None, **kwargs):



    @validate_attr('prestige')
    def get_prestige(self, rank=None, sig=None, star=None, sigstep=20, width=10, **kwargs):
        sigstep_arr = self.bound_lvl(list(range(0, 101, sigstep)))
        table_data = [[''] + sigstep_arr]
        for rank in (4,5):
            row = ['rank{}'.format(rank)]
            for sig in sigstep_arr:
                try:
                    row.append(self.prestige_data[4][rank-1][sig])
                except:
                    print(rank, sig, self.prestige_data)
                    raise
            table_data.append(row)
        title = 'Debug Prestige for {}'.format(self.bold_name)
        return (title, self._tabulate(table_data, width=width))


    def get_aliases(self):
        return '```{}```'.format(', '.join(self.alias_set))

    @staticmethod
    def _sig_header(str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return hex_re.sub(r'**[ \1 ]**', str_data)

    @staticmethod
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

    def _tabulate(self, table_data, width, rotate=True, header_sep=True):
        rows = []
        cells_in_row = None
        for i in self._rotate(table_data, rotate):
            if cells_in_row is None:
                cells_in_row = len(i)
            elif cells_in_row != len(i):
                raise IndexError("Array is not uniform")
            rows.append('|'.join(['{:^{width}}']*len(i)).format(*i, width=width))
        if header_sep:
            rows.insert(1, '|'.join(['-' * width] * cells_in_row))
        return '```' + '\n'.join(rows) + '```'

    @staticmethod
    def _rotate(array, rotate):
        if not rotate:
            for i in array:
                yield i
        for j in range(len(array[0])):
            row = []
            for i in range(len(array)):
                row.append(array[i][j])
            yield row

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
