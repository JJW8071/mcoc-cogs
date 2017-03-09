import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from .utils import checks
import time
import os
import csv
import requests
import re

class Hook:

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/hook/users/{}/'
        self.champs_file = self.data_dir + 'champs.json'
        self.champ_re = re.compile(r'champions(?: \(\d+\))?.csv')

    @commands.command(pass_context=True, no_pm=True)
    async def profile(self,ctx, *, user : discord.Member=None):
        """Displays a user profile."""
        if user is None:
            user = ctx.message.author
        channel = ctx.message.channel
        # creates user if doesn't exist
        self._create_user(user)
        userinfo = fileIO("data/hook/users/{}/champs.json".format(user.id), "load")

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
            }
            dataIO.save_json(self.champs_file.format(user.id), champ_data)

    async def _parse_champions_csv(self, message, attachment):
        channel = message.channel
        self._create_user(message.author)
        response = requests.get(attachment['url'])
        cr = csv.DictReader(response.text.split('\n'))

        chfile = self.champs_file.format(message.author.id)
        champ_data = dataIO.load_json(chfile)

        champ_data['fieldnames'] = cr.fieldnames
        champ_data['champs'] = list(cr)
        champ_data.update({'awd': [], 'awo': [], 'aq': []})

        for champ in champ_data['champs']:
            if champ['Role']:
                print(champ['Role'])
            if champ['Role'] == 'alliance-war-defense':
                champ_data['awd'].append(champ['Id'])
            elif champ['Role'] == 'alliance-war-attack':
                champ_data['awo'].append(champ['Id'])
            elif champ['Role'] == 'alliance-quest':
                champ_data['aq'].append(champ['Id'])

        dataIO.save_json(chfile, champ_data)
        await self.bot.send_message(channel, 'Updated Champion Information')

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
