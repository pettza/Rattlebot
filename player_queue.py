import os
import asyncio

from discord import FFmpegPCMAudio

from youtube_utils import ytdl
from utils import get_bot_voice_client


class PlayerQueue():
  def __init__(self, name, bot, voice_lock, channel_id=None):
    self.name = name
    self.bot = bot
    
    # Async loop
    self.loop = self.bot.loop
    self.voice_lock = voice_lock

    # Channel to report errors to
    self.channel_id = channel_id
    
    self.queue = []
    self.queue_event = asyncio.Event()
    self.finished_item_event = asyncio.Event()
    
    self.playing_task = None
    self.is_playing = False

    self.prefetch_task = None
    self.is_prefetching = False
    self.prefetched = None

  def start(self):
    self.playing_task = self.loop.create_task(self.play())
  
  def stop(self):
    if self.playing_task:
      self.playing_task.cancel()

    # Reset queue
    # Don't call self.skip because it might launch a prefetch task
    self.queue = []
    # Prefetching tasks don't need cancelling
    # if they exist they will cleanup and return
    # since the item they are responsible for is
    # missing from the queue

    # Cleanup tempfiles
    if self.prefetched:
      req = self.prefetched
      self.prefetched = None
      if req['type'] == 'file' and os.path.exists(req['filename']):
        os.remove(req['filename'])    

  def put(self, item):
    self.queue.append(item)

    if len(self.queue) == 1: # If queue was previously empty
      if not self.playing_task or self.playing_task.done():
        self.start()
      self.queue_event.set()
    
    self.prefetch()
  
  def skip(self, n):
    # Skips items
    if isinstance(n, int):
      self.queue = self.queue[n:]
    else:
      n = set(n)
      self.queue = \
        [e for i, e in enumerate(self.queue, 1) if i not in n]
    
    if isinstance(n, int) or 1 in n:
      self.prefetch_task = None # The previous task might need to cleanup, don't cancel it

      # Cleanup prefetched that wasn't played
      if self.prefetched:
        req = self.prefetched
        if req['type'] == 'file' and os.path.exists(req['filename']):
          os.remove(req['filename'])

      self.prefetched = None
      self.prefetch()

  def prefetch(self):
    """
    Launches a prefetching task if there isn't a prefetched item and a task is not already running
    """
    async def task():
      while not self.queue: # If queue is empty, wait
        # The queue might change between the setting
        # of the event and the waking of this task
        # or the event might have been set before 
        # being waited
        # Use while loop to adress this situations
        await self.queue_event.wait()
        self.queue_event.clear() # Reset event

      while self.queue:
        info = self.queue[0]
        self.is_prefetching = True
        title = info['title']
        print(f'Prefetching: {title}')
        
        if info['type'] == 'youtube':
          ytdl_info = await self.loop.run_in_executor(None, ytdl.extract_info, info['url'])
          
          # Item might have been skipped
          if not self.queue or info != self.queue[0]:
            print(f'Skip prefetching {title}')
            return
            
          if not ytdl_info:
            if self.channel_id is not None:
              channel = self.bot.get_channel(self.channel_id)
              if channel:
                await channel.send(f'Δεν μπόρεσα να κατεβάσω το {title} για κάποιο λόγο. Σοζ.')
              else:
                print("Couldn't get music channel")
            
            self.queue.pop(0)
            print(f'Failed to download {title}')
            print('Continuing to next item')
            continue
          
          filename = ytdl.prepare_filename(ytdl_info)
          
          # Item might have been skipped
          # delete file if that's the case
          if not self.queue or info != self.queue[0]:
            if os.path.exists(filename):
              os.remove(filename)
            print(f'Failed to download {title}')
            print('Continuing to next item')
            return

          self.prefetched = {
            'title': info['title'],
            'type': 'file',
            'filename': filename
          }
          break
        elif info['type'] == 'gtts':
          speech = info['speech']
          await self.loop.run_in_executor(None, speech.save, info['filename'])

          self.prefetched = {
            'title': info['title'],
            'type': 'file',
            'filename': info['filename']
          }
          break
        elif info['type'] == 'file':
          self.prefetched = {
            'title': info['title'],
            'type': 'no_delete_file',
            'filename': info['filename']
          }
          break
        else:
          raise NotImplementedError
        
      self.is_prefetching = False
      print(f'Prefetched: {title}')
    
    if not self.prefetched and (not self.prefetch_task or self.prefetch_task.done()):
      self.prefetch_task = asyncio.create_task(task())

  async def play(self):
    print(f'{self.name}: Waiting lock')
    async with self.voice_lock:
      print(f'{self.name}: Aquired lock')
      self.is_playing = True

      while self.prefetched or self.queue:
        while not self.prefetched and self.prefetch_task:
          # The current item being prefetched might be skipped
          # so wait with a timeout
          try:
            await asyncio.wait_for(asyncio.shield(self.prefetch_task), 4)
          except asyncio.TimeoutError:
            pass
        
        # Something might have failed to download
        # or might have been skipped
        if not self.prefetched:
          break
        
        req = self.prefetched
        self.queue.pop(0) # Remove the prefetched item from queue
        self.prefetched = None
        self.prefetch()
        
        def after(e=None):
          if req['type'] == 'file':
            # This check might be needless, but just for safety
            if os.path.exists(req['filename']):
              os.remove(req['filename'])
          
          async def task():
            self.finished_item_event.set()
          self.loop.create_task(task())

        title = req['title']
        print(f'Playing: {title}')

        if self.channel_id is not None:
          channel = self.bot.get_channel(self.channel_id)

          if channel:
            await channel.send(f'Now Playing: {title}')
          else:
            print("Couldn't get channel")

        voice_client = get_bot_voice_client(self.bot)
        if req['type'] == 'file':
          voice_client.play(FFmpegPCMAudio(req['filename']), after=after)
        elif req['type'] == 'url':
          voice_client.play(FFmpegPCMAudio(req['url']), after=after)
        elif req['type'] == 'no_delete_file':
          voice_client.play(FFmpegPCMAudio(req['filename']))
        else:
          raise NotImplementedError
        
        await self.finished_item_event.wait()
        self.finished_item_event.clear()
      
    self.is_playing = False
    print(f'{self.name}: Finished queue')

  # Forward list operations
  def __iter__(self):
    return self.queue.__iter__()
  
  def __bool__(self):
    return bool(self.queue)

  def __len__(self):
    return len(self.queue)

  def __getitem__(self, x):
    return self.queue[x]
