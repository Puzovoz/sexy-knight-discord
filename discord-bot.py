import os
import psycopg2
import datetime
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN        = os.getenv('DISCORD_TOKEN')
GUILD        = os.getenv('DISCORD_GUILD')
DATABASE_URL = os.getenv('DATABASE_URL')

bot = commands.Bot(command_prefix='%')

# Command for setting a new birthday for the caller.
# Example: `%birthday 01.01`
@bot.command()
async def birthday(ctx, arg):
  try:
    if  int(arg[:2])  in range(1, 32) \
    and int(arg[3:5]) in range(1, 13) \
    and arg[2]        == ".":
      author_id = str(ctx.author.id)
      
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()      
      cur.execute("SELECT * FROM members "
                  "WHERE id='{0}';".format(ctx.author.id))
      member_info = cur.fetchone()
      if member_info:
        cur.execute("UPDATE members "
                    "SET birthday='{0}' "
                    "WHERE id='{1}';".format(arg[:5], member_info[0]))
        
      # Make a new entry in case a member is not yet in the database
      else:
        cur.execute("INSERT INTO members (id, name, birthday) "
                    "VALUES ('{0}', '{1}', '{2}');".format(author_id,
                                                           ctx.author.name,
                                                           arg[:5]))
      
      conn.commit()
      cur.close()
      conn.close()
      # State that saving the birthday was successful
      await ctx.send("Success! Saved `" + arg + "` birthday "
                     "for <@{0}>.".format(author_id))
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
      
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()
      cur.execute("SELECT * FROM members "
                  "WHERE birthday='{0}'".format(formatted_date))      
      
      for member in cur.fetchall():
        await channel.send("@everyone, "
                           "it's <@{0}>'s birthday today! 🥳\n "
                           "🎉🎉 Woo! 🎉🎉").format(member_id)
      
      cur.close()
      conn.close()
      
      # Prevent the bot from sending announcements
      # multiple times in a single day
      await asyncio.sleep(3600)
    
    # The coroutine works once 15 minutes
    await asyncio.sleep(900)

if __name__ == "__main__":
  bot.loop.create_task(check_for_birthday())
  bot.run(TOKEN)