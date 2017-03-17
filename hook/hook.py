import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
from operator import itemgetter
from functools import reduce
import time
import os
import ast
import csv
import requests
import re

class Hook:

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/hook/users/{}/'
        self.champs_file = self.data_dir + 'champs.json'
        self.champ_re = re.compile(r'champions(?: \(\d+\))?.csv')
        self.mcoc = self.bot.get_cog('MCOC')

    @commands.command(pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user is None:
            user = ctx.message.author
        channel = ctx.message.channel
        # creates user if doesn't exist
        self._create_user(user)
        #userinfo = fileIO("data/hook/users/{}/champs.json".format(user.id), "load")
        userinfo = dataIO.load_json('data/hook/users/{}/champs.json'.format(user.id))
        if userinfo['prestige'] is not 0:
            em = discord.Embed(title='{} Prestige:'.format(user.name),description='{}'.format(userinfo['prestige']))
            aq = []
            awd = []
            awo = []
            for k in userinfo['awd']:
                champ = self.mcoc._resolve_alias(k)
                awd.append('{}'.format(champ.full_name))
            for k in userinfo['awo']:
                champ = self.mcoc._resolve_alias(k)
                awo.append('{}'.format(champ.full_name))
            for k in userinfo['aq']:
                champ = self.mcoc._resolve_alias(k)
                aq.append('{}'.format(champ.full_name))
            em.add_field(name='AQ:',value='\n'.join(k for k in aq))
            em.add_field(name='AW Offense:',value='\n'.join(k for k in awo))
            em.add_field(name='AW Defense:',value='\n'.join(k for k in awd))
            await self.bot.say(embed=em)
        else:
            await self.bot.say('Temporary User Profile placeholder statement for user {}'.format(user))

    # handles user creation, adding new server, blocking
    def _create_user(self, user):
        if not os.path.exists(self.champs_file.format(user.id)):
            if not os.path.exists(self.data_dir.format(user.id)):
                os.makedirs(self.data_dir.format(user.id))
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
                'maxpi': 0
            }
            dataIO.save_json(self.champs_file.format(user.id), champ_data)

    async def _parse_champions_csv(self, message, attachment):
        channel = message.channel
        self._create_user(message.author)
        response = requests.get(attachment['url'])
        cr = csv.DictReader(response.text.split('\n'), quoting=csv.QUOTE_NONE)
        champ_list = []
        for row in cr:
            champ_list.append({k: parse_value(k, v) for k, v in row.items()})

        mcoc = self.bot.get_cog('MCOC')
        if mcoc:
            self.bot.say('DEBUG: cog mcoc found')
            missing = self.hook_prestige(champ_list)
            if missing:
                await self.bot.send_message(channel, 'Missing hookid for champs: '
                        + ', '.join(missing))

            # max prestige calcs
            champ_list.sort(key=itemgetter('maxpi', 'Id'), reverse=True)
            maxpi = sum([champ['maxpi'] for champ in champ_list[:5]])/5
            max_champs = ['{0[Stars]}* {0[Id]}'.format(champ) for champ in champ_list[:5]]

            # prestige calcs
            champ_list.sort(key=itemgetter('Pi', 'Id'), reverse=True)
            prestige = sum([champ['Pi'] for champ in champ_list[:5]])/5
            top_champs = ['{0[Stars]}* {0[Id]}'.format(champ) for champ in champ_list[:5]]

            em = discord.Embed(title="Updated Champions")
            em.add_field(name='Prestige', value=prestige)
            em.add_field(name='Max Prestige', value=maxpi, inline=True)
            em.add_field(name='Top Champs', value='\n'.join(top_champs), inline=False)
            em.add_field(name='Max PI Champs', value='\n'.join(max_champs), inline=True)

        chfile = self.champs_file.format(message.author.id)
        champ_data = dataIO.load_json(chfile)

        champ_data['fieldnames'] = cr.fieldnames
        champ_data['champs'] = champ_list
        champ_data.update({'awd': [], 'awo': [], 'aq': []})
        champ_data['maxpi'] = maxpi
        champ_data['prestige'] = prestige

        for champ in champ_data['champs']:
            if champ['Role'] == 'alliance-war-defense':
                champ_data['awd'].append(champ['Id'])
            elif champ['Role'] == 'alliance-war-attack':
                champ_data['awo'].append(champ['Id'])
            elif champ['Role'] == 'alliance-quest':
                champ_data['aq'].append(champ['Id'])

        dataIO.save_json(chfile, champ_data)
        if mcoc:
            await self.bot.send_message(channel, embed=em)
        else:
            await self.bot.send_message(channel, 'Updated Champion Information')

    def hook_prestige(self, roster):
        '''Careful.  This modifies the array of dicts in place.'''
        mcoc = self.bot.get_cog('MCOC')
        missing = []
        for cdict in roster:
            cdict['maxpi'] = 0
            if cdict['Stars'] < 4:
                continue
            try:
                champ_obj = mcoc.find_champ(cdict['Id'], 'hookid')
            except KeyError:
                missing.append(cdict['Id'])
                continue
            cdict['Pi'] = champ_obj.get_prestige(rank=cdict['Rank'],
                    sig=cdict['Awakened'], star=cdict['Stars'], value=True)
            if cdict['Stars'] == 5:
                maxrank = 3 if cdict['Rank'] < 4 else 4
            else:
                maxrank = 5
            cdict['maxpi'] = champ_obj.get_prestige(rank=maxrank,
                    sig=cdict['Awakened'], star=cdict['Stars'], value=True)
        return missing

    async def _on_attachment(self, message):
        channel = message.channel
        for attachment in message.attachments:
            if self.champ_re.match(attachment['filename']):
                await self.bot.send_message(channel,
                        "Found a CSV file to import.  Load new champions?  Type 'yes'.")
                reply = await self.bot.wait_for_message(30, channel=channel,
                        author=message.author, content='yes')
                if reply:
                    await self._parse_champions_csv(message, attachment)
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
