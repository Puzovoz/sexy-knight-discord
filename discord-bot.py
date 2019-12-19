import os
import json
import datetime
import discord
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

with open("database.json", encoding="utf-8") as json_file:
  data = json.load(json_file)

async def check_for_birthday():  
  while True:
    current_date = "{0.day}.{0.month}".format(datetime.datetime.utcnow())
    channel = client.get_channel(604388374324838532)  # '#birthdays ID'
    
    # Filter finds members whose birthdays we know
    for member in filter(lambda x: "birthday" in x, data["members"]):
      if channel and current_date == member["birthday"]:
        await channel.send("@everyone, "
                           "it's <@member[id]>'s birthday today! 🥳\n "
                           "🎉🎉 Woo! 🎉🎉").format(member)
    
  # The coroutine works once a day
  await asyncio.sleep(86400)

if __name__ == "__main__":
  client.loop.create_task(check_for_birthday())
  client.run(TOKEN)