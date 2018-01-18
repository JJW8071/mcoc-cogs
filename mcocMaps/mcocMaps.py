import discord
import asyncio
import urllib, json #For fetching JSON from alliancewar.com
import os
from .utils.dataIO import dataIO
from discord.ext import commands

class MCOCMaps:
    '''Maps for Marvel Contest of Champions'''

    aq_map = {'5':{'map': 'aq5', 'maptitle':'5'},
        '5.1':{'map': 'aq51','maptitle':'5 Tier 1'},
        '5.2':{'map':  'aq52', 'maptitle':'5 Tier 2'},
        '5.3':{'map': 'aq53','maptitle':'5 Tier 3'},}
    lolmaps = {'0':{'map':'0', 'maptitle': 'Completion Path 0'},
        '1':{'map':'1', 'maptitle': 'Exploration Path 1'},
        '2':{'map':'2', 'maptitle': 'Exploration Path 2'},
        '3':{'map':'3', 'maptitle': 'Exploration Path 3'},
        '4':{'map':'4', 'maptitle': 'Exploration Path 4'},
        '5':{'map':'5', 'maptitle': 'Exploration Path 5'},
        '6':{'map':'6', 'maptitle': 'Exploration Path 6'},
        '7':{'map':'7', 'maptitle': 'Exploration Path 7'},}

    basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcocMaps/data/'
    icon_sdf = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/sdf_icon.png'
    JPAGS = 'http://www.alliancewar.com'
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['aq'])
    async def aqmap(self, ctx, *, maptype: str):
        '''Select a Map
            aq maps : 5, 5.1, 5.2, 5.3
            /aq 5'''
        if maptype in self.aq_map:
            mapurl = '{}{}.png'.format(self.basepath, self.aq_map[maptype]['map'])
            maptitle = 'Alliance Quest {}'.format(self.aq_map[maptype]['maptitle'])
            em = discord.Embed(color=discord.Color.gold(),title=maptitle)
            em.set_image(url=mapurl)
            em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
            await self.bot.say(embed=em)

    @commands.command(pass_context=True, aliases=['lol'])
    async def lolmap(self, ctx, *, maptype: str):
        '''Select a Map
            LOL maps: 0, 1, 2, 3, 4, 5, 6, 7
            /lol 5'''
        if maptype in self.lolmaps:
            page_list = []
            for i in range(0, 8):
                mapurl = '{}lolmap{}.png'.format(self.basepath, i)
                print(mapurl)
                maptitle = 'Labyrinth of Legends: Kiryu\'s {}'.format(self.lolmaps[str(i)]['maptitle'])
                em = discord.Embed(color=discord.Color.gold(),title=maptitle)
                em.set_image(url=mapurl)
                em.set_footer(text='Art: CollectorDevTeam, Plan: LabyrinthTeam',)
                page_list.append(em)
            await self.pages_menu(ctx=ctx, embed_list=page_list, timeout=60, page=int(maptype))
                #await self.bot.say(embed=em)

    @commands.command(pass_context=True, aliases=['lolteam, kiryu'])
    async def lolteams(self, ctx, *, team: int = 1):
        '''Highly Effective LOL Teams'''
        maxkiryu = 5
        page_list = []
        for i in range(1, maxkiryu+1):
            imgurl = '{}kiryu{}.png'.format(self.basepath, i)
            print(imgurl)
            imgtitle = 'Labyrinth of Legends: Kiryu\'s Teams #{}'.format(i)
            em = discord.Embed(color=discord.Color.gold(),title=imgtitle)
            em.set_image(url=imgurl)
            em.set_footer(text='Art: CollectorDevTeam Plan: LabyrinthTeam',)
            page_list.append(em)
        await self.pages_menu(ctx=ctx, embed_list=page_list, timeout=60, page=team-1)

    @commands.command(pass_context=True, aliases=('aw'))
    async def warmap(self, ctx):
        '''Alliance War 2.0 Map'''
        mapurl = '{}warmap_2.png'.format(self.basepath)
        mapTitle = 'Alliance War 2.0 Map'
        em = discord.Embed(color=discord.Color.gold(),title=mapTitle)
        em.set_image(url=mapurl)
        em.set_footer(text='Presented by [-SDF-]',icon_url=self.icon_sdf)
        await self.bot.say(embed=em)

    @commands.command(pass_context=True, hidden=True)
    async def boost_info(self, ctx, boost):
        # boosturl = 'http://www.alliancewar.com/global/ui/js/boosts.json'
        # data = urllib.urlopen(boosturl).read()
        if os.path.exists('data/mcocMaps/boosts.json'):
            boosts = dataIO.load_json('data/mcocMaps/boosts.json')
            # await self.bot.say('data loaded')
        # boosts = json.loads(data)

        keys = boosts.keys()
        if boost not in keys:
            await self.bot.say('Available boosts:\n'+'\n'.join(k for k in keys))
        else:
            info = boosts[boost]
            img = '{}/global/ui/images/booster/{}.png'.format(JPAGS, info['img'])
            title = info['title']
            text = info['text']
            em = discord.Embed(color=discord.Color.gold(), title='Boost Info', descritpion='', url=JPAGS)
            em.set_thumbnail(url=img)
            em.add_field(name=title, value=text)
            em.set_footer(icon_url=JPAGS+'/aw/images/app_icon.jpg',text='JPAGS & AllianceWar.com')
            await self.bot.say(embed=em)



    async def pages_menu(self, ctx, embed_list: list, category: str='', message: discord.Message=None, page=0, timeout: int=30, choice=False):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        print('list len = {}'.format(len(embed_list)))
        length = len(embed_list)
        em = embed_list[page]
        if not message:
            message = await self.bot.say(embed=em)
            # try:
            #     await self.bot.delete_message(ctx.message)
            # except:
            #     pass
            if length > 5:
                await self.bot.add_reaction(message, '⏪')
            if length > 1:
                await self.bot.add_reaction(message, '◀')
            if choice is True:
                await self.bot.add_reaction(message,'🆗')
            await self.bot.add_reaction(message, '❌')
            if length > 1:
                await self.bot.add_reaction(message, '▶')
            if length > 5:
                await self.bot.add_reaction(message, '⏩')
        else:
            message = await self.bot.edit_message(message, embed=em)
        await asyncio.sleep(1)

        react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
        # if react.reaction.me == self.bot.user:
        #     react = await self.bot.wait_for_reaction(message=message, timeout=timeout,emoji=['▶', '◀', '❌', '⏪', '⏩','🆗'])
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message,'⏪', self.bot.user) #rewind
                    await self.bot.remove_reaction(message, '◀', self.bot.user) #previous_page
                    await self.bot.remove_reaction(message, '❌', self.bot.user) # Cancel
                    await self.bot.remove_reaction(message,'🆗',self.bot.user) #choose
                    await self.bot.remove_reaction(message, '▶', self.bot.user) #next_page
                    await self.bot.remove_reaction(message,'⏩', self.bot.user) # fast_forward
            except:
                pass
            return None
        elif react is not None:
            # react = react.reaction.emoji
            if react.reaction.emoji == '▶': #next_page
                next_page = (page + 1) % len(embed_list)
                # await self.bot.remove_reaction(message, '▶', react.user)
                await self.bot.remove_reaction(message, '▶', react.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '◀': #previous_page
                next_page = (page - 1) % len(embed_list)
                await self.bot.remove_reaction(message, '◀', react.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '⏪': #rewind
                next_page = (page - 5) % len(embed_list)
                await self.bot.remove_reaction(message, '⏪', react.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '⏩': # fast_forward
                next_page = (page + 5) % len(embed_list)
                await self.bot.remove_reaction(message, '⏩', react.user)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react.reaction.emoji == '🆗': #choose
                if choice is True:
                    # await self.bot.remove_reaction(message, '🆗', react.user)
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

def setup(bot):
    bot.add_cog(MCOCMaps(bot))
