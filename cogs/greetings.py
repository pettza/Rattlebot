import asyncio

from discord.ext import commands
from gtts import gTTS

from utils import get_bot_voice_client, snek_emoji, get_user_bot_connection_enum, UserBotConnectionEnum
from player_queue import PlayerQueue

class Greetings(commands.Cog):
  """
  A Cog that greets members joining or leaving the voice channel
  that the bot is connencted to.
  """
  def __init__(self, bot, voice_lock):
    self.bot = bot
    self.queue = PlayerQueue('GreetingsQueue', bot, voice_lock)
    self.greetings_on = True

  @commands.Cog.listener()
  async def on_voice_state_update(self, member, before, after):
    voice_client = get_bot_voice_client(self.bot)
    if not self.greetings_on or member == self.bot.user or not voice_client:
      return

    music_cog = self.bot.get_cog('Music')
    if music_cog.queue.is_playing or len(music_cog.queue) > 0:
      return
    
    if before.channel != after.channel and after.channel is not None and after.channel == voice_client.channel:
      text = f'Bre khalos ton {member.nick or member.name}'
      #text = f'Kalhi hronia grotheh'
      speech = gTTS(text=text, lang='en', slow=True)
      filename = f'welcome_{member.name}.mp3'
      
      # Wait a bit before playing because it takes a bit
      # before a member is able to listen in the channel
      await asyncio.sleep(5)
      
      self.queue.put({
        'title': text,
        'type': 'gtts',
        'speech': speech,
        'filename': filename
      })

    if after.channel is None and before.channel is not None and before.channel == voice_client.channel:
      text = 'Ta lehghameh grotheh'
      speech = gTTS(text=text, lang='en', slow=True)
      filename = f'goodbye_{member.name}.mp3'
      
      self.queue.put({
        'title': text,
        'type': 'gtts',
        'speech': speech,
        'filename': filename
      })

  @commands.command()
  async def greetings(self, ctx, *, arg):
    arg_l = arg.lower()
    
    if arg_l == 'on':
      self.greetings_on = True
      await ctx.message.add_reaction(snek_emoji)
    elif arg_l == 'off':
      self.greetings_on = False
      await ctx.message.add_reaction(snek_emoji)
    else:
      await ctx.reply(f'Οι προσφωνήσεις και αποχεραιτισμοί μπορούν να είναι είτε on είτε off, όχι {arg}.')
      await ctx.reply('Γρόθε.')
  
  @commands.command()
  async def rattle(self, ctx):  
    c = get_user_bot_connection_enum(ctx)

    if c == UserBotConnectionEnum.NotOnSameChannel or c == UserBotConnectionEnum.UserNotConnected:
      await ctx.reply('Rattlάρω μόνο για αυτούς που είναι εκεί για να με ακούσουν γρόθε.')
    elif c == UserBotConnectionEnum.BotNotConnected:
      await ctx.reply('If a rattlebot rattles while it is not connected to a channel for anyone to hear, will there be rattling at all?')
      await ctx.send('Riddle me that γρόθε.')
    elif c == UserBotConnectionEnum.NeitherConnected: 
      await ctx.reply('If a rattlebot rattles while it is not connected to a channel for anyone to hear, will there be rattle at all?')
      await ctx.send('Riddle me that γρόθε.')
      await ctx.send('Επίσης δεν είσαι καν σε voice channel...')
      await ctx.send('γρόθε')
    elif c == UserBotConnectionEnum.OnSameChannel:
      await ctx.message.add_reaction(snek_emoji)
      
      text = 'Rattlesake!'
      speech = gTTS(text=text, lang='en', slow=True)
      filename = f'rattle.mp3'
      
      self.queue.put({
        'title': text,
        'type': 'gtts',
        'speech': speech,
        'filename': filename
      })
