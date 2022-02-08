import asyncio

import youtube_dl
from youtube_dl import DownloadError
from youtube_search import YoutubeSearch


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s-%(autonumber)d.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


async def search_yt(search_str, loop=None):
  loop = loop or asyncio.get_event_loop()
  results = await loop.run_in_executor(None, lambda: YoutubeSearch(search_str, max_results=10).to_dict())
  return results


async def info_from_yt_url(url, loop=None):
  loop = loop or asyncio.get_event_loop()

  try:
    info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

    if 'entries' in info:
      # take first item from a playlist
      info = info['entries'][0]

    ret = dict()
    ret['title'] = info['title']
    ret['type'] = 'youtube'
    ret['url'] = url
    ret['ytdl_info'] = info

    return ret
  except (Exception, DownloadError) as e:
    print(e)
    return None
