import discord
from discord.ext import commands

class Lessons:
    """How To Marvel Contest of Champions"""
    lessons = {
            'parry': (
                'How to Parry Like a Boss',
                'https://www.youtube.com/watch?v=VRPXxHrgDnY',
                '```Parry Types:\n1. The First Kiss\n2. The Cherry Picker\n3. Quick Draw\n4. The Second Coming\n~~5. Unspecial~~```'
            ),
            'intercept': (
                'How to Intercept Like a Boss',
                'https://www.youtube.com/watch?v=fIaGpZgmQJs',
                'Intercept Types:\n1. **Yo-Yo** - Dash toward your target **the very instant** they dash toward you, interrupting the target animation\n2. **Backdraft** - bait an attack, back off, then strike as they rush you\n3. **Come At Me Bro** - No bait to set up the target, you just have to be ready when they dash\n4. **Parry Mason** - As soon as the target leaves the parry you strike on their attack\n5. **Special Delivery** - This one is easy, fire a special when the target is rushing you.\n```Warning: Cannot use this well on Rhino or Juggernaut (Unstoppable)```'
            ),
            'thor': (
                'How to Use Duped Thor',
                'https://www.youtube.com/watch?v=Ng31Ow1SNOk',
                '```Evade, crit boost. >> Parry, stun. >> L3 destroyz```\nAdvanced: **Minimum Stun Duration**\nReduce your stun duration, or use against War opponents with Limber 5.\nParry. As soon as the parry debuff cycles, Parry again, stacking debuff.\nStack up to 4 or 5 debuffs.\nL3 destroys.'
            ),
            'magik': (
                'How to Magik',
                'https://www.youtube.com/watch?v=zC47YeI1b8g',
                '```Magik\'s L3 increases Attack 50% for every enemy buff Nullified.```\nWait until the target has stacked many buffs, then drop the L3.\nThis is excellent versus Venom and Groot'
            )
        }

    fight = {
            'spiderman': (
            'How to fight Spiderman',
            'https://www.youtube.com/watch?v=U-hPA-gNqqk',
            'Slow down. Don\'t rely on your standard combo pattern.\nParry-stun or bait a heavy attack.\nRely on Medium-Medium combos.\nBuild Spiderman to an L2 and Evade.'
            ),
            'cyclops': (
            'How to fight Cyclops',
            'https://www.youtube.com/watch?v=iRay5dQBRbs',
            'Watch Cyclops\' **head** during a L1 special.  When he prepares to fire a special Cyclops leans back, then leans forward. **Evade** as soon as his head shifts forward and the background darkens. If you evade too soon you will catch one of his beams.\nCyclops L2 includes a punch, a kick, and then the headshift for the blast.  '
            )
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
            if choice in self.fight:
                await self.bot.say('**{}**\n{}\n{}'.format(*self.fight[choice]))
            else:
                sometxt = 'Choose'
                em = discord.Embed(title=sometxt, description='\n'.join(self.fight.keys()))
                await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Mycog(bot))
