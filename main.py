from flask import Flask
from threading import Thread

from bot import rattlebot, TOKEN

app = Flask('')

@app.route('/')
def main():
  return "Your Bot Is Ready"

def run():
  app.run(host="0.0.0.0", port=8000)

flask_thread = Thread(target=app.run, kwargs={'host':"0.0.0.0", 'port':8000})
flask_thread.start()

rattlebot.run(TOKEN)
