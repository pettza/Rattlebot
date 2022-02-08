from enum import Enum, auto

snek_emoji = '\U0001F40D'

music_channel_id = 651462331519205407
test_channel_id  = 864508141021429781

class UserBotConnectionEnum(Enum):
  NeitherConnected = auto()
  BotNotConnected  = auto()
  UserNotConnected = auto()
  NotOnSameChannel = auto()
  OnSameChannel    = auto()

def get_user_bot_connection_enum(ctx):
    if ctx.author.voice:
      if ctx.voice_client:
        if ctx.voice_client.channel == ctx.author.voice.channel:
          return UserBotConnectionEnum.OnSameChannel
        else:
          return UserBotConnectionEnum.NotOnSameChannel
      else:
        return UserBotConnectionEnum.BotNotConnected
    else:
      if ctx.voice_client:
        return UserBotConnectionEnum.UserNotConnected
      else:
        return UserBotConnectionEnum.NeitherConnected


def get_bot_voice_client(bot):
  if bot.voice_clients:
    return bot.voice_clients[0]
  
  return None


def check_channels(ctx, channel_id_list):
  return ctx.channel.id in channel_id_list
