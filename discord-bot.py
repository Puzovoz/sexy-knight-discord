# -*- coding: utf-8 -*-
import os
from unicodedata import combining
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

bot = commands.Bot(command_prefix='SxK ')

# Command for administrators that works with a pinned message, blacklist.
# `SxK blacklist`: passing no arguments will briefly show the list in chat.
# `SxK blacklist name`: passing a name will add that name to the blacklist
# and update the pinned message.
# `SxK blacklist ~~name~~`: passing a name with strikethrough formatting
# will instead remove that name from the blacklist.
@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist(ctx, arg=False):
  def generate_blacklist(cur):
    cur.execute("SELECT * FROM blacklist "
                "ORDER BY "
                "  name ASC;")    
    return "**BLACKLIST**\n" + "\n".join(i[0] for i in cur.fetchall())
  
  async def update_blacklist(cur):
    officers = bot.get_channel(614159495085686794)
    blacklist = await officers.fetch_message(657883991692541972)
    await blacklist.edit(content=generate_blacklist(cur))
  
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cur = conn.cursor()
  
  # The command will show the blacklist for 15 secs if no arguments are passed.
  if arg is False:
    await ctx.send(generate_blacklist(cur), delete_after=15)
    cur.close()
    conn.close()
    break
  
  # And will insert or delete the name from the database otherwise.
  name = arg.split(" ")[0].title()
  
  # Delete command
  # `blacklist ~~name~~`
  if name[:2] == name[-2:] == "~~":
    name = name.strip("~*")
    cur.execute("DELETE FROM blacklist "
                "WHERE name='{0}'".format(name))
    conn.commit()
    
    if cur.rowcount > 0:
      await update_blacklist(cur)
      await ctx.send("Removed {0} from the blacklist!".format(name))
    else:
      await ctx.send("Couldn't find {0} in the blacklist.".format(name))
  
  # Insert command
  # `blacklist name`
  else:
    try:
      name = name.strip("~*")
      cur.execute("INSERT INTO blacklist (name) "
                  "VALUES ('{0}');".format(name))
      conn.commit()
      
      await update_blacklist(cur)
      await ctx.send("Added {0} to the blacklist!".format(name))
      
    except psycopg2.errors.UniqueViolation:
      await ctx.send("Seems like this player is already "
                     "in the blacklist.\n"
                     "Check for errors and try again.")
      
  cur.close()
  conn.close()

# Command for setting a new birthday for the caller.
# The pinned message with birthday list will also be updated.
# Example: `SxK birthday 01.01`
@bot.command()
async def birthday(ctx, arg):
  try:
    if  int(arg[:2])  in range(1, 32) \
    and int(arg[3:5]) in range(1, 13) \
    and arg[2]        == ".":
      author_id = str(ctx.author.id)
      
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()
      
      cur.execute("INSERT INTO members (id, name, birthday) "
                  "VALUES ('{0}', '{1}', '{2}') "
                  "ON CONFLICT (id) DO UPDATE "
                  "SET birthday='{2}';".format(author_id,
                                               ctx.author.name,
                                               arg[:5]))
      
      conn.commit()
      
      months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
      ]
      ordinal = lambda n: "%d%s" % (n, {1:"st", 2:"nd", 3:"rd"}
                                    .get(n if n<20 else n%10, "th"))
      
      channel = bot.get_channel(604388374324838532)
      birthday_list = await channel.fetch_message(657232655196094464)
      cur.execute("SELECT * FROM members "
                  "WHERE "
                  "  birthday IS NOT NULL "
                  "ORDER BY "
                  "  SUBSTRING(birthday, 4, 2) ASC,"
                  "  SUBSTRING(birthday, 1, 2) ASC;")
      birthday_result = cur.fetchall()
      
      # Update pinned message with a list of all birthdays
      await birthday_list.edit(content="```\n"
                               + "\n".join("{0}{1}{2:>4} {3}".format(
                                 row[1],
                                 # Regular Python formatting works
                                 # incorrectly with Unicode characters,
                                 # so a manual method was implemented
                                 ' ' * (25-len(''.join(c for c in row[1]
                                                       if combining(c)==0))),
                                 ordinal(int(row[2][:2])),
                                 months[int(row[2][3:5])-1])
                                 for row in birthday_result)
                               + "\n```")
      
      cur.close()
      conn.close()
      
      await ctx.send("Success! Saved {0} of {1} birthday "
                     "for <@{2}>.".format(ordinal(int(arg[:2])),
                                          months[int(arg[3:5])-1],
                                          author_id))
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
    channel = bot.get_channel(604388374324838532)  # '#birthdays' ID
    if current_date.hour == 12 and channel:
      formatted_date = "{0.day}.{0.month}".format(current_date)      
      
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()
      cur.execute("SELECT * FROM members "
                  "WHERE birthday='{0}'".format(formatted_date))      
      
      for member in cur.fetchall():
        await channel.send("@everyone, "
                           "it's <@{0}>'s birthday today! 🥳\n "
                           "🎉🎉 Woo! 🎉🎉".format(member[0]))
      
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