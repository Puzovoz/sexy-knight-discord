import os
import json
import datetime
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='%')

with open("database.json", encoding="utf-8") as json_file:
  data = json.load(json_file)

members = data["members"]
for member in filter(lambda m: "birthday" in members[m], members.keys()):
  if "birthday" in members[member]:
    print(members[member]["birthday"])

# Command for setting a new birthday for the caller.
# Example: `%birthday 01.01`
@bot.command()
async def birthday(ctx, arg):
  try:
    if  int(arg[:2])  in range(1, 32) \
    and int(arg[3:5]) in range(1, 13) \
    and arg[2]        == ".":
      author_id = str(ctx.author.id)
      if author_id in data["members"]:
        members[author_id]["birthday"] = arg[:5]
        
      # Make a new entry in case a member is not yet in the database
      else:
        data["members"][author_id] = {
          "name": ctx.author.name,
          "birthday": arg[:5]
        }
      
      with open("database.json", "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2)
        
      # State that saving the birthday was successful
      await ctx.send("Success! Saved `" + arg + "`.")
    else:
      await ctx.send("That doesn't look right.\n"
                     "Make sure you send your birthday in `dd.mm` format. "
                     "Like this, for example: `24.05`.")
  except ValueError:
    await ctx.send("Uh oh. Did you try to write your birthday with words?\n"
                   "I'm not smart enough to understand that yet, try using "
                   "`dd.mm` format, like this: `24.05`.")

async def check_for_birthday():
  while True:
    current_date = datetime.datetime.utcnow()
    if current_date.hour == 12:
      formatted_date = "{0.day}.{0.month}".format(current_date)
      channel = client.get_channel(604388374324838532)  # '#birthdays' ID
      
      # Filter finds members whose birthdays we know
      members = data["members"]
      for member_id in filter(lambda m: "birthday" in members[m], members.keys()):
        if channel and formatted_date == members[member_id]["birthday"]:
          # Send a message if any members have a birthday today
          await channel.send("@everyone, "
                             "it's <@{0}>'s birthday today! 🥳\n "
                             "🎉🎉 Woo! 🎉🎉").format(member_id)
      
      # Prevent the bot from sending announcements
      # multiple times in a single day
      await asyncio.sleep(3600)
    
    # The coroutine works once 15 minutes
    await asyncio.sleep(900)

if __name__ == "__main__":
  bot.loop.create_task(check_for_birthday())
  bot.run(TOKEN)