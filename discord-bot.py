# -*- coding: utf-8 -*-
import os
from unicodedata import combining
import psycopg2
import datetime
import calendar
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN        = os.getenv('DISCORD_TOKEN')
GUILD        = os.getenv('DISCORD_GUILD')
DATABASE_URL = os.getenv('DATABASE_URL')

bot = commands.Bot(command_prefix=('SxK ', 'Sxk ', 'sxk '))

async def update_birthdays(cur):
  current_date = datetime.datetime.utcnow()
  cur.execute("(SELECT * FROM members "
              "WHERE "
              "  birthday > '2036-{0.month}-{0.day}' "
              "ORDER BY "
              "  birthday ASC) "
              "UNION ALL "
              "(SELECT * FROM members "
              "WHERE "
              "  birthday IS NOT NULL "
              "ORDER BY "
              "  birthday ASC) "
              "LIMIT 5;".format(current_date))
  
  channel = bot.get_channel(604388374324838532)
  birthday_list = await channel.fetch_message(657232655196094464)
  
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
  birthday_result = cur.fetchall()

  await birthday_list.edit(content="**BIRTHDAYS**\n"
                           "These knights will have a birthday soon!\n```"
                            + "\n".join("{0}{1}{2:>4} {3}".format(
                                 row[1],
                                 # Regular Python formatting works
                                 # incorrectly with Unicode characters,
                                 # so a manual method was implemented
                                 ' ' * (25-len(''.join(c for c in row[1]
                                                       if combining(c)==0))),
                                 ordinal(int(row[2].day)),
                                 months[int(row[2].month)-1])
                                 for row in birthday_result)
                            + "\n```")

# Command for administrators that works with a pinned message, blacklist.
# `SxK blacklist`: passing no arguments will briefly show the list in chat.
# `SxK blacklist name`: passing a name will add that name to the blacklist
# and update the pinned message.
# `SxK blacklist ~~name~~`: passing a name with strikethrough formatting
# will instead remove that name from the blacklist.
@bot.command()
@commands.has_role('Staff')
async def blacklist(ctx, arg=''):
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
  if not arg:
    message = await ctx.send(generate_blacklist(cur)
                             + '\nReact to this message to prevent timed deletion.\n'
                             'Doing so will result in outdated lists staying in history.')
    cur.close()
    conn.close()
    
    await asyncio.sleep(15)
    if not message.reactions:
      await message.edit('This message was edited to hide outdated lists '
                         'and reduce littering in chat.')
    return
  
  # And will insert or delete the name from the database otherwise.
  name = arg.split(" ")[0].title()
  
  # Delete command
  # `blacklist ~~name~~`
  if name[:2] == name[-2:] == "~~":
    name = name.strip("~*")
    cur.execute("DELETE FROM blacklist "
                "WHERE name=%s", [name])
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
                  "VALUES (%s);", [name])
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
async def birthday(ctx, arg=''):
  ordinal = lambda n: "%d%s" % (n, {1:"st", 2:"nd", 3:"rd"}
                                .get(n if n<20 else n%10, "th"))
  
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
  
  arg = arg.replace('!', '')
  
  # Checking birthday by given ping
  if arg[:2] == "<@" and arg[-1]==">":
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("SELECT birthday FROM members "
                "WHERE id=%s", [arg[2:-1]]) 
    
    birth_date = cur.fetchone()[0]
    if birth_date is not None:
      await ctx.send(f"{arg}'s birthday is on {ordinal(birth_date.day)} "
               f"of {months[birth_date.month-1]}.")
      
    else:
      await ctx.send("I don't know their birthday yet.")
    
    cur.close()
    conn.close()
    return
  
  
  # Finding birthdays by given month
  if arg.title() in months:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("SELECT id, birthday FROM members "
                "WHERE EXTRACT(MONTH FROM birthday)=%s "
                "ORDER BY "
                "  birthday ASC",
                [months.index(arg.title())+1])
    
    guild = bot.get_guild(508545461939077142)
    message = ''
    for member in cur.fetchall():
      user = guild.get_member(int(member[0]))
      if user is None: continue
      message += (f"{user.display_name} — {ordinal(member[1].day)} "
                  f"of {months[member[1].month-1]}\n")
    
    await ctx.send(message)
    
    cur.close()
    conn.close()
    return
  
  
  for i in ".-/":
    char_index = arg.find(i)
    if char_index >= 0: break
  
  try:
    if  char_index >= 0 \
    and int(arg[:char_index])               in range(1, 32) \
    and int(arg[char_index+1:char_index+3]) in range(1, 13):
      author_id = str(ctx.author.id)
      birth_date = f"2036-{arg[char_index+1:char_index+3]:0>2}-{arg[:char_index]:0>2}"
      
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()
      
      cur.execute("INSERT INTO members (id, name, birthday) "
                  "VALUES (%(id)s, %(name)s, %(birthday)s) "
                  "ON CONFLICT (id) DO UPDATE "
                  "SET birthday=%(birthday)s, "
                  "name=%(name)s;", {'id': str(author_id),
                                     'name': ctx.author.name,
                                     'birthday': birth_date})
      
      conn.commit()
      
      await update_birthdays(cur)
      
      cur.close()
      conn.close()
      
      await ctx.send("Success! Saved {0} of {1} birthday "
                     "for <@{2}>.".format(ordinal(int(birth_date[8:])),
                                          months[int(birth_date[5:7])-1],
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
      conn = psycopg2.connect(DATABASE_URL, sslmode='require')
      cur = conn.cursor()
      if (not calendar.isleap(current_date.year)
      and current_date.month == 2
      and current_date.day == 28):
        cur.execute("SELECT id FROM members "
                    "WHERE birthday=%s "
                    "OR birthday='2036-02-29'", [current_date.strftime('2036-%m-%d')])
      else:
        cur.execute("SELECT id FROM members "
                    "WHERE birthday=%s", [current_date.strftime('2036-%m-%d')])
      
      guild = bot.get_guild(508545461939077142)
      members = [m for m in cur.fetchall() if guild.get_member(int(m[0])) is not None]
      if len(members) == 1:
        await channel.send("@everyone, "
                           "it's <@{0}>'s birthday today! 🥳\n"
                           "🎉🎉 Woo! 🎉🎉".format(members[0][0]))
      elif len(members) > 1:
        await channel.send("@everyone, what a coincidence!\n"
                           "It's <@"
                           + ">, <@".join(member[0] for member in members[:-1])
                           + "> and <@{0}>'s birthday today!".format(members[-1][0])
                           + " 🥳\n🎉🎉 Woo! 🎉🎉")
      
      await update_birthdays(cur)
            
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