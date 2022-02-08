import asyncio
from urllib.parse import urlparse
import typing

from discord.ext import commands
import validators

from youtube_utils import info_from_yt_url, search_yt
from utils import get_bot_voice_client, music_channel_id, test_channel_id, check_channels
from player_queue import PlayerQueue


class Music(commands.Cog):
  def __init__(self, bot, voice_lock):
    self.bot = bot
    self.queue = PlayerQueue(
      'MusicQueue', 
      bot,
      voice_lock,
      channel_id=music_channel_id,
    )

  async def commands_check(self, ctx):
    if not check_channels(ctx, [music_channel_id, test_channel_id]):
      await ctx.reply('Για μουσική μόνο στο music channel.')
      return False
    
    if not get_bot_voice_client(self.bot):
      await ctx.reply('Πρέπει πρώτα να με κάνεις join, πριν παίξω μουσική.')
      return False
    
    return True
  
  async def playing_check(self, ctx):
    if not self.queue.is_playing:
      await ctx.reply('Δεν μπορώ να skipάρω όταν δεν παίζω κάτι')
      return False
    
    return True
  
  @commands.command(help='Searches YouTube for a piece or uses a link to play music')
  async def play(self, ctx, *, arg):
    if not await self.commands_check(ctx):
      return

    info = None
    
    if validators.url(arg):
      domain = urlparse(arg).netloc
      
      if 'youtube' in domain:
        info = await info_from_yt_url(arg, loop=self.bot.loop)
        if info:
          video_id = info['ytdl_info']['id']
          info['display_url'] = f'https://youtu.be/{video_id}'
          url = arg
      else:
        await ctx.reply(f'Δυστυχώς ακόμα δεν μπορώ να παίξω μουσική από {domain}.')
    else:
      results = await search_yt(arg)

      if results:
        first = results[0]
        url_suffix = first['url_suffix']
        url = f'www.youtube.com{url_suffix}'
        info = await info_from_yt_url(url, loop=self.bot.loop)
        if info:
          video_id = first['id'] 
          info['display_url'] = f'https://youtu.be/{video_id}' 
      else:
        await ctx.reply(f'Δεν ξέρω τι σκατά μουσική ακούς αλλά εγώ δεν βρήκα τίποτα στο YouTube για {arg}')
    
    if info:
      self.queue.put(info)
      disp_url = info.get('display_url', None) or url
      await ctx.reply(f'Queued: \n{disp_url}')
      print(f'Queued: \n{arg}')
      print(url)
    else:
      await ctx.reply('Δεν μπόρεσα να κατεβάσω το κομμάτι για κάποιο λόγο. Σοζ.')
  
  @commands.command()
  async def skip(self, ctx, n: typing.Optional[int]):
    if not await self.commands_check(ctx):
      return

    if not await self.playing_check(ctx):
      return
    
    if n is None:
      voice_client = get_bot_voice_client(self.bot)
      if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()
    elif isinstance(n, int):
      if n < 0:
        async with ctx.typing():
          await ctx.reply('Δεν μπορώ να skipάρω αρνητικό αριθμό κομματιών.')
          await ctx.send('Μάθε λίγη αριθμητική...')  
          await asyncio.sleep(1)
          await ctx.send('Γρόθε.')
      elif n == 0:
        async with ctx.typing():
          await ctx.reply('Ok...')
          await asyncio.sleep(2)
          await ctx.send('Skipάρω 0 κομμάτια.')
          await asyncio.sleep(1)
          await ctx.send('Done')
    else:
      print(f'Skipping {n} items')
      self.queue.skip(n)

  @commands.command()
  async def xkaxe(self, ctx):
    if not await self.commands_check(ctx):
      return

    if not await self.playing_check(ctx):
      return
    
    voice_client = get_bot_voice_client(self.bot)
    if voice_client.is_playing():
      voice_client.pause()

  @commands.command()
  async def resume(self, ctx):
    if not await self.commands_check(ctx):
      return

    if not await self.playing_check(ctx):
      return
    
    voice_client = get_bot_voice_client(self.bot)
    if voice_client.is_paused():
      voice_client.resume()
  
  @commands.command()
  async def show_queue(self, ctx):
    def to_str(idx,item):
      title = item['title']
      url = item['url']
      return f'{idx}. {title} ({url})' 

    if self.queue:
      async with ctx.typing():
        await ctx.reply('\n'.join(to_str(i, item) for i, item in enumerate(self.queue, 1)))
    else:
      await ctx.reply('Δεν έχω κάτι queued')