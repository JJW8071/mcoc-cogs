import discord
from discord.ext import commands

class Lessons:
    """My custom cog that does stuff!"""
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

        @commands.command()
        async def fight(self, choice=None):
            if choice in self.lessons:
                await self.bot.say('**{}**\n{}\n{}'.format(*self.fight[choice]))
            else:
                sometxt = 'Choose'
                em = discord.Embed(title=sometxt, description='\n'.join(self.fight.keys()))
                await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Mycog(bot))
