from discord.ext import commands
from gtts import gTTS

from utils import get_user_bot_connection_enum, UserBotConnectionEnum, snek_emoji


class Christmas(commands.Cog):
  """
  A seasonal cog with the holiday spirit
  """
  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  async def grothmas(self, ctx):
    c = get_user_bot_connection_enum(ctx)

    if c == UserBotConnectionEnum.BotNotConnected or c == UserBotConnectionEnum.NeitherConnected:
      await ctx.reply('I gave my wishes in the land of bots but there was no groth to hear.')
    else:
      await ctx.message.add_reaction(snek_emoji)
      
      text = 'Hronia polha grothy!'
      speech = gTTS(text=text, lang='en', slow=True)
      filename = f'wishes.mp3'

      queue = self.bot.get_cog('Greetings').queue
      queue.put({
        'title': text,
        'type': 'gtts',
        'speech': speech,
        'filename': filename
      })

  @commands.command()
  async def rattlebells(self, ctx):
    c = get_user_bot_connection_enum(ctx)

    if c == UserBotConnectionEnum.BotNotConnected or c == UserBotConnectionEnum.NeitherConnected:
      await ctx.reply("Alas, I sing but my sweet voice doesn't reach your grothic ears.")
    else:
      await ctx.message.add_reaction(snek_emoji)
      
      queue = self.bot.get_cog('Greetings').queue
      queue.put({
        'title': 'rattlebells',
        'type': 'file',
        'filename': 'rattlebells.mp3'
      })

