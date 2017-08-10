import discord
import re
import csv
import random
import os
import json
import asyncio
from .utils.dataIO import dataIO

class GSJSON():
    def __init__(self):

    @checks.owner()
    @commands.command(hidden=True, pass_context=True)
    async def setgoogleapikey(self, ctx):
        settings = load_json('data/red/settings.json')
        msg = await self.bot.say('What is your Google API key?')
        msg1 = await self.bot.wait_for_message(timeout=30, author=ctx.message.author)
        await self.bot.edit_message(msg, 'What is your Google API key?\nKey: {}'.format(msg1.content))
        # settings.update({"GSJSON":msg1.content})



    @commands.command(hidden=True)
    async def gs_to_json(self, head_url:str, body_url:str, foldername:str, filename:str, groupby_value=None, DATA_DIR='data/mcoc/{}/'):
        DATA_DIR = DATA_DIR.format(foldername)
        SHELL_JSON = DATA_DIR + '{}.json'.format(filename)

        if head_url is not None:
            async with aiohttp.get(head_url) as response:
                try:
                    header_json = await response.json()
                except:
                    print('No header data found.')
                    return
            header_values = header_json['values']

        async with aiohttp.get(body_url) as response:
            try:
                body_json = await response.json()
            except:
                print('No data found.')
                return
        body_values = body_json['values']

        output_dict = {}
        if head_url is not None:
            if groupby_value is None:
                groupby_value = 0
            grouped_by = header_values[0][groupby_value]
            for row in body_values:
                dict_zip = dict(zip(header_values[0],row))
                groupby = row[groupby_value]
                output_dict.update({groupby:dict_zip})
        else:
            output_dict =body_values

        self.save_gsjson(output_dict, DATA_DIR, SHELL_JSON)
        return output_dict

    def save_gsjson(self, output_dict, DATA_DIR, SHELL_JSON):
        if foldername is not None and filename is not None:
            if not os.path.exists(SHELL_JSON):
                if not os.path.exists(DATA_DIR):
                    os.makedirs(DATA_DIR)
                dataIO.save_json(DATA_DIR, output_dict)
            dataIO.save_json(DATA_DIR,output_dict)


def setup(bot):
    bot.add_cog(MCOC(bot))
