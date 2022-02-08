import os
import asyncio

from discord.ext import commands

from cogs import Greetings, Music, Christmas
from utils import get_user_bot_connection_enum, UserBotConnectionEnum, snek_emoji


TOKEN = os.environ['TOKEN']

class Rattlebot(commands.Bot):
  def __init__(self):
    super().__init__(command_prefix='~')

    self.voice_lock = asyncio.Lock()
    
    self.add_cog(Greetings(self, self.voice_lock))
    self.add_cog(Music(self, self.voice_lock))
    #self.add_cog(Christmas(self))


rattlebot = Rattlebot()


@rattlebot.event
async def on_ready():
  print(f'Rattlebot on the prowl {snek_emoji}')


@rattlebot.command()
async def join(ctx):
  c = get_user_bot_connection_enum(ctx)

  if c == UserBotConnectionEnum.OnSameChannel:
    await ctx.reply(f'Άνοιξε τα γκαβά σου ρε γρόθε, είμαι ήδη στο {ctx.voice_client.channel}.')
  elif c == UserBotConnectionEnum.NotOnSameChannel:
    await ctx.reply(f'Τι πας να κάνεις εκεί ρε γρόθε; Πας να με απαγάγεις στο {ctx.author.voice.channel};')
  elif c == UserBotConnectionEnum.UserNotConnected:
    await ctx.reply(f'Αφενός είμαι ήδη στο {ctx.voice_client.channel}, αφετέρου πρέπει να είσαι εσύ σε voice channel ρε γρόθε.')
  elif c == UserBotConnectionEnum.NeitherConnected: 
    await ctx.reply('Πρέπει να είσαι σε voice channel ρε γρόθε.')
  elif c == UserBotConnectionEnum.BotNotConnected:
    # Add snek reaction
    await ctx.author.voice.channel.connect()
    rattlebot.get_cog('Greetings').queue.start()
    rattlebot.get_cog('Music').queue.start()
    await ctx.message.add_reaction(snek_emoji)


@rattlebot.command()
async def leave(ctx): 
  c = get_user_bot_connection_enum(ctx)

  if c == UserBotConnectionEnum.NotOnSameChannel or c == UserBotConnectionEnum.UserNotConnected:
    await ctx.reply(f'Τι πας να κάνεις εκεί ρε γρόθε; Πας να με βγάλεις από το {ctx.voice_client.channel};')
  elif c == UserBotConnectionEnum.BotNotConnected:
    await ctx.reply('Πώς να βγω από voice channel ενώ δεν είμαι σε κάποιο ρε γρόθε; Duh!')
  elif c == UserBotConnectionEnum.NeitherConnected: 
    await ctx.reply('Ούτε είμαι σε voice channel, αλλά και να ήμουν, δεν είσαι εσύ. Γρόθος εις διπλούν.')
  if c == UserBotConnectionEnum.OnSameChannel:
    rattlebot.get_cog('Greetings').queue.stop()
    rattlebot.get_cog('Music').queue.stop()
    await ctx.voice_client.disconnect()
    await ctx.message.add_reaction(snek_emoji)


import typing

@rattlebot.command()
async def test(ctx, n: typing.Optional[typing.Union[int, typing.List, bool]]):
  print(n)

# @rattlebot.event
# async def on_message(msg: Message):
#   if msg.channel.name == 'rattlebot-testing' and msg.author != rattlebot.user:
#     await msg.channel.send('sks')
