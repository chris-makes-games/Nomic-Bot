import discord
from discord.ext import tasks
import os
import sheets
import asyncio
import time
from twitch import TwitchClient

# twitch secret token for API authentication
secret = os.environ['TOKEN']

# client object for discord interraction
class NomicBot(discord.Client):
  
  # initialzation to set up timer
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer.start()

  @tasks.loop(seconds=600)
  async def timer(self):
      await self.finisher()

  # when the bot wakes up
  async def on_ready(self):
    print("Discord Bot Online")
    print("Ready for User input")
    print("--------------------")

  # embeds a help message for the user on !help
  async def send_help(self, m):
    embed = discord.Embed(
        title="Click here for the Nomic Game Document",
        colour=0x1d4b02,
        description=
        "Thank you for checking out nomic! Be careful with these commands, you can't edit your proposals after sending the command!",
        url=
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQEPqgEa80j_D_4AY246NGi7JGKi7zanMJfd7dDFNhD8zVCOeUNaGFqe-Hkq_wBFcSty8l8Bh0Yrng6/pubhtml"
    )
    embed.add_field(name="!nomic",
                    value="Sends a message about nomic.",
                    inline=False)
    embed.add_field(name="!propose <type your new rule>",
                    value="Use this command to propose new rules. Beware: proposals cannot be changed once this command has been sent.",
                    inline=False)
    embed.add_field(name="!modify <rule number> <new text of the rule>",
                    value="This command can edit any rule already passed. Try not to use this command to change a rule completely... ",
                    inline=False)
    embed.add_field(name="!abolish <rule number>",
                    value="Proposes to abolish an established rule. The rule's number will be left open if it is abolished.",
                    inline=False)
    embed.add_field(name="!players",
                    value="Returns the list of players.",
                    inline=False)
    embed.add_field(name="!rules",
                    value="Returns the current rules.",
                    inline=False)
    embed.add_field(
        name="!register <your_twitch_username>",
        value=
        "Links your discord name to your twitch name on the sheet. This bot will need you to re-register if you change your discord name. You need to redeem nomic points on Big_Sarnts channel before using this command.",
        inline=False)
    await m.channel.send(embed=embed)

  # a general message about nomic for the user on !nomic
  async def nomic_info(self, m):
    embed = discord.Embed(
        title="Nomic",
        colour=0x1d4b02,
        description=
        "Nomic is the original creation of Peter Suber. It is a game about democracy and fluid rules. Most rules in the game can be changed or modified. Each player in the game is able to vote on new rules being passed, and can influence how the game is played. How we play and even how to win can be changed!\n\n You can direct message or @Big Sarnt if you have any questions. Feel free to check out the rules, propose new ones, and have fun!"
		)
    await m.channel.send(embed=embed)

  async def finisher(self):
    sheets.finish()

  # creates a new proposal after checking requirements. The proposal is a discord embed
  # users react on the embed to vote for the proposal
  async def proposal(self, m, opposite):
    try:
      text = str(m.content)
      text = text.split()[1]
    except IndexError:
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "Please specify your proposal like this:\n!propose <your proposal text here>"
      )
      await m.channel.send(embed=embed)
      return
    text = str(m.content)
    if not opposite:
      text = text.replace("!propose ", "")
      text = text.replace("!proposal ", "")
    else:
      text = text.replace("!opposite ", "")
    player = str(m.author)
    t = sheets.proposal(text, player, opposite)
    if t == "Duplicate":
      t = "Duplicate Rule"
      d = "That exact proposal already exists and is still pending. Please try a different proposal. You can try to propose again after the voting period expires."
      embed = discord.Embed(title=t, description=d)
    elif t == "Not Registered":
      t = "Not Registered"
      d = "Please register your discord ID to your twitch account first by using: \n!register <your_twitch_username>\nIn order to register, you must first redeem the Nomic channel point from Big_Sarnt's channel"
      embed = discord.Embed(title=t, description=d)
    else:
      d = t
      t = "New Proposal"
      embed = discord.Embed(title=t, description=d)
      embed.set_footer(text="vote by reacting to this message with \'yay\' or \'nay\' reacts")
    await m.channel.send(embed=embed)

  # leaderboard sends list of current top seven players
  async def leaderboard(self, m):
    r = sheets.send_leaderboard()
    embed = discord.Embed(title="Points Leaderboard")
    embed.set_footer(text="These are total points and may not be reflective of the winner depending on the rules.")
    for l in r:
      embed.add_field(name=(l[0] + " " + l[1]),
                      value=(l[2] + " " + l[3]),
                      inline=False)
    await m.channel.send(embed=embed)

  # like a proposal, but modifies a current rule
  async def modify(self, m):
    try:
      l = m.content
      l = l.split()
      number = l[1]
      player = str(m.author)
      text = str(m.content)
      text = text[10:]
      numbers = sheets.send_numbers()
    except Exception as exp:
      print("Error: " + str(exp))
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "No vailid rule number found. please specify your modification proposal like this:\n!modify <rule number> <your new text for the rule>"
      )
      await m.channel.send(embed=embed)
      return
    if number not in numbers:
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "No vailid rule number found. Please specify your modification proposal like this:\n!modify <rule number> <your new text for the rule>\n\nMake sure the number you enter cooresponds to a valid rule, and that the number is written as a number, not a word."
      )
      await m.channel.send(embed=embed)
      print("'" + number + "'" + " is not a rule number!")
      return
    elif number == '0':
      embed = discord.Embed(
          title="Rule Zero",
          description=
          "Sorry, but you can't change rule zero! Try entering in another rule number."
      )
      await m.channel.send(embed=embed)
      print("Can't change rule Zero!")
      return
    else:
      text = "Modification to rule " + l[1] + ": " + text
      t = sheets.proposal(text, player, False)
      if t == "Duplicate":
        t = "Duplicate Modification Proposal"
        d = "That exact proposal already exists and is still pending. Please try a different proposal. You can try to propose again after the voting period expires."
        embed = discord.Embed(title=t, description=d)
      elif t == "Not Registered":
        t = "Not Registered"
        d = "Please register your discord ID to your twitch account first by using: \n!register <your_twitch_username>\nIn order to register, you must first redeem the Nomic channel point from Big_Sarnt's channel"
        embed = discord.Embed(title=t, description=d)
      else:
        r = sheets.send_rule(number)
        d = t
        d = d.replace("Modification to rule " + l[1] + ": ", "")
        t = "New Modification Proposal"
        embed = discord.Embed(title=t)
        embed.add_field(name="Current Rule Text:", value=str(r), inline=False)
        embed.add_field(name="Modification to rule " + l[1] + ":\n", value=str(d), inline=False)
        embed.set_footer(text="vote by reacting to this message with \'yay\' or \'nay\' reacts")
    await m.channel.send(embed=embed)
    
  
	# like a proposal, but deletes a current rule
  async def abolish(self, m):
    try:
      l = m.content
      number = l.replace("!abolish ", "")
      player = str(m.author)
      numbers = sheets.send_numbers()
    except Exception as exp:
      print("Error: " + str(exp))
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "No valid rule number found. please specify your modification proposal like this:\n!abolish <rule number>"
      )
      await m.channel.send(embed=embed)
      return
    if number not in numbers:
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "No valid rule number found. Please specify your abolish proposal like this:\n!abolish <rule number>\n\nMake sure the number you enter cooresponds to a valid rule, and that the number is written as a number, not a word."
      )
      await m.channel.send(embed=embed)
      print("'" + number + "'" + " is not a rule number!")
      return
    elif number == '0':
      embed = discord.Embed(
          title="Rule Zero",
          description=
          "Sorry, but you can't abolish rule zero! Try entering in another rule number."
      )
      await m.channel.send(embed=embed)
      print("Can't change rule Zero!")
      return
    else:
      text = "Abolish Rule " + number
      t = sheets.proposal(text, player, False)
      if t == "Duplicate":
        t = "Duplicate Abolishment Proposal"
        d = "That exact proposal already exists and is still pending. Please try a different proposal. You can try to propose again after the voting period expires."
        embed = discord.Embed(title=t, description=d)
      elif t == "Not Registered":
        t = "Not Registered"
        d = "Please register your discord ID to your twitch account first by using: \n!register <your_twitch_username>\nIn order to register, you must first redeem the Nomic channel point from Big_Sarnt's channel"
        embed = discord.Embed(title=t, description=d)
      else:
        r = sheets.send_rule(number)
        t = "Proposal to Abolish Rule " + number
        embed = discord.Embed(title=t)
        embed.add_field(name="Current Rule Text:", value=str(r), inline=False)
        embed.set_footer(text="vote by reacting to this message with \'yay\' or \'nay\' reacts")
    await m.channel.send(embed=embed)

  # adds votes to document and keeps tally for passing proposals
  async def on_raw_reaction_add(self, payload):
    if payload.emoji.name == "yay":
      user = str(payload.member.name) + "#" + str(payload.member.discriminator)
      print("recieved yay vote")
      print("From: " + payload.member.name)
      r = sheets.vote(payload.message_id, True, user)
      print(r+"\n")
    if payload.emoji.name == "nay":
      user = str(payload.member.name) + "#" + str(payload.member.discriminator)
      print("recieved nay vote")
      print("From: " + payload.member.name)
      r = sheets.vote(str(payload.message_id), False, user)
      if r == "PASSED":
        embed = discord.Embed(
            title="New Law",
            description="A new law was passed!")
        await payload.message_channel.send(embed=embed)
      print(r + "\n")

  # creates an embed with a list of all players
  async def player_list(self, m):
    l = sheets.send_players()
    embed = discord.Embed(title="Players")
    total_players = 0
    for player in l:
      if player[1] == "":
        player[1] = "Unregistered."
      else:
        player[1] = "Registered as: " + player[1]
      embed.add_field(name=player[0],
        value=(player[2] + " points. " + player[1]),
        inline=False)
      total_players += 1
    embed.set_footer(text="Total Players: " + str(total_players))
    await m.channel.send(embed=embed)

  # sends an embed with link to the rules
  async def rules(self, m):
    l = sheets.send_rules()
    embed = discord.Embed(title="Click Here For the Rules",
    description="There are currently " + str(len(l)) + " rules, too many to paste here!",
    url="https://docs.google.com/spreadsheets/d/1ggv3Z_Rad1r9Kq9_dnDHJH_2hNbQiikQFCOutfVIciE/edit#gid=1023040527")
    await m.channel.send(embed=embed)

  # checks requirements and adds user's discord ID to their twitch ID
  async def register(self, m):
    try:
      player = m.content.split()[1]
    except IndexError:
      embed = discord.Embed(
          title="Incorrect Command",
          description=
          "Please specify your twitch username like this:\n!register <your_twitch_username>"
      )
      await m.channel.send(embed=embed)
      return
    print("sending " + player + " as player")
    disc = str(m.author)
    print("sending " + disc + " as disc")
    register_result = sheets.register(player, disc)
    embed = discord.Embed(title=register_result)
    await m.channel.send(embed=embed)

  # just a test embed for trying bot commands
  async def test(self, m):
    embed = discord.Embed(title="This was a test",
                          description="test completed")
    await m.channel.send(embed=embed)

  # detects when any message is sent on discord server
  # handles/ignores messages from itself and outside correct channel
  async def on_message(self, message):
    # first checks if message from self is a new proposal
    # if true, adds proposal ID to new proposal for reaction tracking
    # slightly different if the proposal is a modification
    if message.author == client.user:
      if "Proposal" in message.embeds[0].title:
        if message.embeds[0].title == "New Proposal":
          i = str(message.id)
          d = str(message.embeds[0].description)
          sheets.proposal_id(i, d, 0)

        # for a modification:
        elif message.embeds[0].title.startswith("New Modification Proposal"):
          t = message.embeds[0].fields[1].name.split()
          number = t[3]
          number = number.replace(":", "")
          id = str(message.id)
          name = message.embeds[0].fields[1].name
          value = message.embeds[0].fields[1].value
          text = str(name + " " + value)
          sheets.proposal_id(id, text, number)
        
        # for an abolition
        elif message.embeds[0].title.startswith("Proposal to Abolish Rule"):
          t = message.embeds[0].title.split()
          number = t[4]
          i = str(message.id)
          print(i)
          d = str("Abolish Rule " + number)
          sheets.proposal_id(i, d, number)

      else:
        return
    # handles incoming command, parsing to lowercase word
    if message.content.startswith('!'):
      s = message.content.split()[0]
      s = s.replace("!", "")
      s = s.lower()
      # list of all possible commands
      l = [
          "help", "nomic", "propose", "modify", "abolish", "players",
          "rules", "register", "test", "proposal", "opposite", "leaderboard"
      ]
      if message.channel.name == "nomic" \
      or message.channel.name == "nomic-test" \
      or message.channel.name == "nomic-info":
        print("\nrecieved command: " + s)
        print("From: " + str(message.author))
        if s == "help":
          await self.send_help(message)
        if s == "nomic":
          await self.nomic_info(message)
        if s == "propose" or s == "proposal":
          await self.proposal(message, False)
        if s == "opposite":
          await self.proposal(message, True)
        if s == "modify":
          await self.modify(message)
        if s == "abolish":
          await self.abolish(message)
        if s == "players":
          await self.player_list(message)
        if s == "rules":
          await self.rules(message)
        if s == "register":
          await self.register(message)
        if s == "test":
          await self.test(message)
        if s == "leaderboard":
          await self.leaderboard(message)
        if s not in l:
          print("recieved incorrect command: " + s)
          print("check spelling and try again")
      # check if command was outside nomic channel. ignores non-commands
      elif s in l:
        print("user " + str(message.author) +
              " tried to access nomic bot outside nomic channel")
        embed = discord.Embed(
            title="Nomic Channel",
            description=
            "I have been programmed to only aknowledge commands inside the nomic channel. Please try sending your command there."
				)
        await message.channel.send(embed=embed)
      else:
        return
    else:
      return

# Creating client objects
twitch_client = TwitchClient()
client = NomicBot()
loop = asyncio.get_event_loop()
# Start connection and get client connection protocol
connection = loop.run_until_complete(twitch_client.connect())
# adds twitch listener, twitch heartbeat, and dicord bot to tasks for loop
tasks = [
    asyncio.ensure_future(twitch_client.heartbeat(connection)),
    asyncio.ensure_future(twitch_client.receiveMessage(connection)),
    asyncio.ensure_future(client.run(secret)),
    
]
# main async loop for completing all three tasks
loop.run_until_complete(asyncio.wait(tasks))
