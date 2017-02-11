import re
from textwrap import wrap
from math import log2
import inspect
import urllib
import requests
import json
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

champ_data_json='http://coc.frogspawn.de/champions/js/champ_data.json'
champ_data_json_local='data/mcoc/champ_data.json'
champ_crossreference_json='https://spreadsheets.google.com/feeds/list/1QesYLjDC8yd4t52g4bN70N8FndJXrrTr7g7OAS0BItk/1/public/values?alt=json'
champ_portraits='data/mcoc/portraits/portrait_'
champ_features='data/mcoc/uigacha/featured/GachaChasePrize_256x256_'

frogspawn=requests.get('http://coc.frogspawn.de/champions/js/champ_data.json')
frogspawn_data=frogspawn.json()
with open('data/mcoc/frogspawn_data.json', 'w') as outfile:
    json.dump(frogspawn_data,outfile)

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
        isig = inspect.signature
        #self.champ_data = dataIO.load_json('data/mcoc/frogspawn_data.json')
        self.settings = {'siglvl': 1,
                'sigstep': 20,
                'table_width': 10,
                'sig_inc_zero': False,
                }
        self._prepare_aliases()
        self._prepare_frogspawn_champ_data()
        #print(MCOC.event.callback, MCOC.warmap.callback)
        #print(isig(MCOC.event.callback), isig(MCOC.warmap.callback))

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

    @commands.command(help=lookup_links['streak'][0])
    async def streak(self):
        await self.bot.say('**{}**\n{}'.format(*self.lookup_links['streak']))

    @commands.command()
    async def howto(self, choice=None):
        if choice is None:
            sometxt = 'Choose\n'
            await self.bot.say(sometxt + '\n'.join(self.lessons.keys()))
        else:
            await self.bot.say('**{}**\n{}\n{}'.format(*self.lessons[choice]))

# This is what I'm using to test image uploading, vs link reference
   # @commands.command(pass_context=True)
   # async def phc(self,ctx):
   #     '''Premium Hero Crystal Release Dates'''
   #     channel=ctx.message.channel
   #     await self.bot.say('<http://marvelbitvachempionov.ru/wp-content/dates_PCHen.jpg>')

    @commands.command(pass_context=True)
    async def portrait(self, ctx, champ):
        '''View Champion Portraits'''
        channel=ctx.message.channel
        #        await self.bot.send_file(channel,champ_portraits''champ'.png', content='**'champ'**')
        await self.bot.send_file(channel,champ_portraits+champ+'.png', content='**'+champ+'**')

    @commands.command(pass_context=True)
    async def featured(self, ctx, champ):
        '''View Champion Feature Images'''
        channel=ctx.message.channel
        #        await self.bot.send_file(channel,champ_portraits''champ'.png', content='**'champ'**')
        await self.bot.send_file(channel,champ_features+champ+'.png', content='**'+champ+'**')

    @commands.command(pass_context=True)
    async def lolmap(self, ctx):
        '''Labrynth of Legends Map'''
        channel=ctx.message.channel
        filepath='data/mcoc/maps/lolmap.png'
        await self.bot.send_file(channel, filepath, content='**LABYRINTH OF LEGENDS Map by Frogspawn**')

    @commands.command()
    async def tools(self):
        self.hook()
        self.marvelynergy()
        self.frogspawn()
        self.simulator()
        #list the useful links from lookup_links

    @commands.command()
    async def test(self):
        await self.bot.say('Test string with\n line break')

    @commands.command()
    async def warmap(self, maptype=''):
        '''Select a Warmap
        syntax: /warmap <left><right>
        Where <left> = [a, b, c, d, e]
        Where <right> = [f, g, g+, h, i]'''
        if maptype in self.warmap_links:
            ##await self.bot.say('JJW: I **did** find the maptype in warmap_links')
            await self.bot.say('**{}**\n{}'.format(*self.warmap_links[maptype]))
        else :
            raise KeyError('I cannot find that map')

    #@alias_resolve
    @commands.command()
    async def bio(self, champ):
        '''Retrieve the Bio of a Champion'''
        champ = self._resolve_alias(champ)
        em = discord.Embed(color=discord.Color.blue(), title=champ.full_name, 
                description=champ.get_bio())
        await self.bot.say(embed=em)
        
    @commands.command()
    async def sig(self, champ, siglvl=None, *args):
        '''Retrieve the Signature Ability of a Champion'''
        champ = self._resolve_alias(champ)
        settings = self.settings.copy()
        if siglvl is not None:
            settings['siglvl'] = int(siglvl)
        title, desc = champ.get_sig(**settings)
        em = discord.Embed(color=discord.Color.red(), title=title, 
                description=desc)
        await self.bot.say(embed=em)

    @commands.command()
    async def sigarray(self, champ, *args):
        '''Retrieve the Signature Ability of a Champion at multiple levels'''
        champ = self._resolve_alias(champ)
        title, desc = champ.get_sigarray(**self.settings)
        em = discord.Embed(color=discord.Color.dark_magenta(), title=title, 
                description=desc)
        await self.bot.say(embed=em)

    @commands.command()
    async def champs(self):
        '''Return a list of all the champs'''
        await self.bot.say('\n'.join(wrap(', '.join(self.champ_data.keys()))))

    @commands.command()
    async def tst(self, *args):
        '''Return a list of all the champs'''
        print('\n'.join(args))
        await self.bot.say("I'm awesome!")

    def _prepare_aliases(self):
        '''Create a python friendly data structure from the aliases json'''
        response = urllib.request.urlopen(champ_crossreference_json)
        raw_data = json.loads(response.read().decode('utf-8'))
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
                    alias_set.add(v.lower())
            if all_aliases.isdisjoint(alias_set):
                all_aliases.union(alias_set)
            else:
                raise KeyError("There are aliases that conflict with previous aliases."
                        + "  First occurance with champ {}.".format(key_values['champ']))
            champs.append(Champion(alias_set, **key_values, debug=len(champs)==0))
        self.champs = champs

    def _prepare_frogspawn_champ_data(self):
        response = urllib.request.urlopen(champ_data_json)
        champ_data = json.loads(response.read().decode('utf-8'))
        for champ in self.champs:
            champ.update_frogspawn(champ_data[champ.frogspawnid])

    def _resolve_alias(self, alias):
        for champ in self.champs:
            if champ.re_alias.fullmatch(alias):
                return champ
        raise KeyError("Champion for alias '{}' not found".format(alias))

def validate_attr(*expected_args):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for attr in expected_args:
                if getattr(self, attr + '_data', None) is None:
                    raise AttributeError("{} for Champion ".format(attr.capitalize())
                        + "{} has not been initialized.".format(self.champ))
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
            setattr(self, key, value)
        self.full_name = self.champ

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
        return ('Signature Ability for {} at level={}:'.format(
                self.full_name.capitalize(), siglvl), sig_str.format(*str_data))

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
                self.full_name.capitalize()) 
        response = sig_str.format(*str_data) + self._tabulate(table_data, width=width)
        return (title, response)

    @staticmethod
    def _sig_header(str_data):
        hex_re = re.compile(r'\[[0-9a-f]{6,8}\](.+?)\[-\]', re.I)
        return hex_re.sub(r'**\1**', str_data)

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