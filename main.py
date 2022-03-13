import json
import random
import discord
import re
import unicodedata
import os
import time
import datetime
from discord.ext import tasks, commands
import pymongo
from webserver import keep_alive

TOKEN = os.environ['DISCORD_BOT_SECRET']
mongoDB = os.environ['mongoDB']


mongoClient = pymongo.MongoClient(mongoDB)

database = mongoClient.AntiNitroScam





class NitroScam(commands.Cog, name="ScamDetect"):

    def __init__(self, client):
        self.client = client

        for x in database.Stats.find({'id': 'stats'}):
            self.stats = x
            self.oldStats = x
        self.updateDatabaseLoop.start()
    def find(self, string):

        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, string)
        return [x[0] for x in url]

    def contains(self, arr, mess, must=False):

        mess = ''.join(
            filter(lambda x: x in '0123456789abcdefghijklmnopqrstuvwxyz', mess))
        Contains = True
        for i in arr:
            Contains = i in mess and (must and Contains or True) or False

        return Contains

    def alphanumericScan(self, arr):
        for mess in arr:
            for char in mess:
                try:
                    char = unicodedata.name(char)
                    if 'SMALL LETTER' in char and not char.startswith("LATIN"):
                        return True
                except:
                    pass

    def scamCheck(self, message):
        embeds = message.embeds
        Scam = 0
        Message = ""
        if 'discord.gg/' in message.content:
            if message.content.split("discord.gg/")[1].split(" ")[0] != "":
                Scam = True
                Message = "Discord invite detected"
                return Scam, Message
        if len(embeds) == 0:
            if ('free' and 'nitro' in message.content.lower()):
                urls = self.find(message.content.lower())

                for i in urls:
                    i = i.replace("https://", "")
                    i = i.replace("http://", "")
                    if not self.contains(['free', 'nitro'], i, True):
                        if not i.startswith("discord.gift") and not i.startswith("discord.com") and not i.startswith('discordapp.com'):
                            Scam += 1
                            Message = "Possible scam link detected."
        else:
            for embed in embeds:
                jsonEmbed = embed.to_dict()
                if not 'url' in jsonEmbed:
                    return (False, False)
                url = jsonEmbed['url'].replace("https://", "")
                url = jsonEmbed['url'].replace("http://", "")
                if 'provider' not in jsonEmbed:
                    jsonEmbed['provider'] = {}
                    jsonEmbed['provider']['name'] = ""
                if not url.startswith("discord.com") and not url.startswith("discord.gift"):
                    result = self.alphanumericScan([jsonEmbed['title'].lower(
                    ), jsonEmbed['description'].lower(), jsonEmbed['provider']['name'].lower()])
                    if result:
                        Scam += 5
                        break

                    if 'nitro' in jsonEmbed['title'].lower() and 'free' in jsonEmbed['title'].lower() and 'month' in jsonEmbed['title'].lower():
                        Scam += 5
                    elif 'discord has gifted' in jsonEmbed['title'].lower() and jsonEmbed['provider']['name'].lower() == 'disсоrd':
                        Scam += 5
                    elif self.contains(['upgrade', 'emoji', 'file', 'stand', 'favourite'], jsonEmbed['description'].lower()) and jsonEmbed['provider']['name'].lower() == 'disсоrd':
                        Scam += 5
                    elif self.contains(['month', 'nitro', 'from'], jsonEmbed['title'].lower()):
                        Scam += 5
                    elif self.contains(['you', 'gifted'], jsonEmbed['title'].lower()):
                        Scam += 5
            if Scam > 0:
                org = str((Scam/7)*100+0.5)
                Chance = float(org.split(".")[0]+'.'+org.split(".")[1][0:2])
            if Scam > 0 and Scam < 2:
                return (True, f'Possible scam link detected.')
            elif Scam > 1:
                return (True, f'Scam link detected. {Chance}%')
        return (False, False)

    def updateDatabase(self, database, query, data):
        database.update_one(query, {'$set': data})

    @tasks.loop(seconds=30.0)
    async def updateDatabaseLoop(self):
        if self.oldStats != self.stats:
            self.stats = self.oldStats
            self.updateDatabase(database.Stats, {'id': 'stats'}, self.stats)

    @commands.Cog.listener()
    async def on_ready(self):
        activity = discord.Activity(
            name="discord nitro scams", type=discord.ActivityType.watching)
        await self.client.change_presence(status=discord.Status.online, activity=activity)
        print(f"Logged in as {self.client.user.name}\n{self.client.user.id}")
        documents = []
        for guild in self.client.guilds:
            if not database.Servers.count_documents({'guildID': guild.id}):
                documents.append({
                    'guildID': guild.id,
                    'settings': {
                        'ApplicationChannel': None,
                    }
                })
        if len(documents) > 0:
            database.Servers.insert_many(documents)

        

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith(".checkmark"):
            await message.add_reaction("<:Tick:926436686173454356>")
            Scam, Message = self.scamCheck(message)
            if Scam:
                await message.author.send(Message)
                await message.delete()
                self.stats['Scams Blocked'] += 1

            else:
                if "http" in message.content:
                    await message.add_reaction("<:Tick:926436686173454356>")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        Scam, Message = self.scamCheck(after)
        if Scam:
            await after.author.send(Message)
            await after.delete()

        else:
            if self.find(after.content):
                await after.add_reaction("<:Tick:926436686173454356>")


class Commands(commands.Cog, name="Commands"):

    def __init__(self, client):
        self.client = client
        self.rps = {
            'choices': ['rock', 'paper', ' scissors'],
            'win': {
                'rock': 'scissors',
                'paper': 'rock',
                'scissors': 'paper'
            }
        }
        self.snipe = {

        }
        for x in database.Stats.find({'id': 'stats'}):
            self.stats = x
        self.updateStats.start()

    @tasks.loop(seconds=20.0)
    async def updateStats(self):
        for x in database.Stats.find({'id': 'stats'}):
            self.stats = x

    @commands.command()
    async def uptime(self, ctx):
        current_time = time.time()
        difference = int(round(current_time - start_time))
        text = str(datetime.timedelta(seconds=difference))
        embed = discord.Embed(colour=0xc8dc6c)
        embed.add_field(name='Uptime', value=text)
        await ctx.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        embed = discord.Embed(colour=0xc8dc6c)
        embed.title = "Stats"
        blocked = self.stats["Scams Blocked"]
        embed.add_field(name="Scams Blocked",
                        value=f"{blocked}", inline=True)
        embed.add_field(name="   count",
                        value=f"{len(self.client.guilds)}", inline=False)
        total = 0
        for i in self.client.guilds:
            total += i.member_count
        embed.add_field(name="Total members", value=f"{total}", inline=False)

        embed.set_footer(text=f"{datetime.date.today()}")
        embed = discord.Embed(colour=0xc8dc6c, title='Stats')
        embed.add_field(name='Scams Blocked', value=f'{blocked}', inline=False)
        embed.add_field(name='Guild Count',
                        value=f'{len(self.client.guilds)}', inline=False)
        embed.add_field(name='Total Members', value=f'{total}', inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def rps(self, ctx, use=''):
        choices = self.rps['choices']
        if not use.lower() in choices:
            embed = discord.Embed(
                colour=0xE74C3C, title='Rock Paper Scissors!')
            embed.add_field(name='Invalid input!',
                            value=f'Valid inputs are: Rock, Paper, Scissors.')
            await ctx.channel.send(embed=embed)
            return

        choice = random.choice(choices).replace(" ", "")
        if self.rps['win'][choice] == use.lower():
            embed = discord.Embed(
                colour=0xE74C3C, title='Rock Paper Scissors!')
            embed.add_field(name='You lost!', value=f'{choice} beats {use}')
        elif choice == use.lower():
            embed = discord.Embed(
                colour=0xFEE75C, title='Rock Paper Scissors!')
            embed.add_field(
                name='Draw!', value=f'{choice} doesn\'t beat {use}')
        else:
            embed = discord.Embed(
                colour=0x2ECC71, title='Rock Paper Scissors!')
            embed.add_field(name='You win!', value=f'{use} beats {choice}')

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.snipe[message.channel.id] = {}
        self.snipe[message.channel.id]['image'] = message.author.avatar_url
        self.snipe[message.channel.id]['author'] = message.author
        self.snipe[message.channel.id]['content'] = message.content

    @commands.command()
    async def snipe(self, ctx):
        if ctx.channel.id in self.snipe and self.snipe[ctx.channel.id] != None:
            dat = self.snipe[ctx.channel.id]
            embed = discord.Embed(
                title=dat['author'], colour=0x2ECC71, description=dat['content'])
            embed.set_thumbnail(url=dat['image'])
            await ctx.send(embed=embed)
            self.snipe[ctx.channel.id] = None
        else:
            await ctx.send(embed=discord.Embed(colour=0xE74C3C, title='Snipe', description="There is nothing to snipe."))


start_time = time.time()


client = commands.Bot(command_prefix=".")


scamDetect = client.add_cog(NitroScam(client))

commands = client.add_cog(Commands(client))

client.run(TOKEN)

