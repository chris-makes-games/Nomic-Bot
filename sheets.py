import gspread
import datetime
from dateutil.parser import parse

gc = gspread.service_account(filename="google_secret.json")
sh = gc.open("Nomic")
welcome = sh.worksheet("Welcome")
rulez = sh.worksheet("Da Rulez")
players = sh.worksheet("Players")
proposals = sh.worksheet("Proposals")

# checks if a user exists, adding points if they do and assigning if they don't
def new_user(username):
    if username in players.col_values(1):
        print("player already registered")
        add_points(username)
    else:
        data = [username, "", 1]
        players.append_row(data, 1)

# returns a list of all the rules
def send_rules():
  r = rulez.get_all_values()
  r.pop(0)
  return r

def send_leaderboard():
  r = welcome.range("A21:D27")
  print("fetching leaderboard...")
  print(str(len(r)))
  s = []
  f = []
  ticker = 0
  for l in r:
    if l.value == "":
      s.append("points:")
    else:
      s.append(l.value)
    ticker += 1
    if ticker == 4:
      f.append(s)
      s = []
      ticker = 0
  return f

def send_numbers():
  r = rulez.col_values(1)
  r.pop(0)
  return r

# returns a list of all the players
def send_players():
  r = players.get_all_values()
  r.pop(0)
  return r

def send_rule(number):
  try:
    r = rulez.find(number)
  except Exception as exp:
    print(exp)
    return ("Error, rule number not found")
  t = rulez.cell(r.row, (r.col + 1))
  return t.value

def finish():
  r = proposals.get_all_values()
  r.pop(0)
  now = datetime.datetime.now()
  for line in r:
    if line[2] == "PENDING":
      expire = parse(line[4])
      id = line[8]
      if now > expire:
        if line[6] == "" or line[6] == "None":
          print("Rule " + line[0] + " passed!")
          pass_law(line[8])
        else:
          print("closing proposal " + id + "...")
          cell = proposals.find(id)
          proposals.update_cell(cell.row, (cell.col - 6), "FAILED")


# makes sure a player is registered - unregistered may not vote
def check_register(username):
  if username in players.col_values(2):
    return True
  else:
    return False

def check_duplicate(text, flag):
  if text in proposals.col_values(1):
    data_list = []
    cell_list = []
    duplicates = proposals.findall(text)
    for cell in duplicates:
      cell_list.append(proposals.row_values(cell.row))
      data_list.append(cell_list)
      cell_list = []
    recent_cell = data_list[-1]
    time_cell = parse(recent_cell[0][4])
    if flag:
      return recent_cell[0][4]
    if datetime.datetime.now() > time_cell:
      return False
    else:
      return True
  else:
    return False

# returns length of the list of all REGISTERED players
def get_total_players():
  total = 0
  l = players.get_all_values()
  l.pop(0)
  for player in l:
    p = str(player[1])
    if p == "" or p == "None":
      continue
    if check_register(p):
      total += 1
  return total

# increments points of the user by one
def add_points(username):
    cell = players.find(username)
    points = players.cell(cell.row, (cell.col + 2))
    new_points = int(points.value) + 1
    print("Player " + username + " now has " + str(new_points) + " points\n")
    players.update_cell(cell.row, (cell.col + 2), new_points)

# creates a new proposal by appending data to list of proposals in gsheets.
def proposal(text, player, opposite):
  if check_duplicate(text, False):
    return("Duplicate")
  if check_register(player):
    if opposite:
      text = "<OPPOSITE>" + str(text)
    t = datetime.datetime.now()
    t = t + datetime.timedelta(days=1)
    t = str(t)
    p = get_total_players()
    p -= 1
    print("adding proposal to sheets...\n")
    data = [text, str(player), "PENDING", p, t, player, "None"]
    proposals.append_row(data, 1)
    text = text.replace("<OPPOSITE>", "")
    return(str(text))
  else:
    print("player " + player + " not registered")
    return("Not Registered")

def modify(text, player):
  if check_register(player):
    t = datetime.datetime.now()
    t = t + datetime.timedelta(days=1)
    t = str(t)
    p = get_total_players()
    p -= 1
    print("adding proposal to sheets...\n")
    data = [str(text), str(player), "PENDING", p, t, player, "None"]
    proposals.append_row(data, 1)
    return(str(text))
  else:
    print("player " + player + " not registered")
    return("Not Registered")
    
# after proposal created, updates the sheet with bot message id
def proposal_id(prop_id, prop_text, rule_number):
  print("adding a proposal ID number...")
  r = str(rule_number)
  data = str(prop_id)
  print(data)
  opp_text = "<OPPOSITE>" + prop_text
  mod_text = "Modification to rule " + r + ": "
  ab_text = "Abolish Rule " + r + ": "

  if check_duplicate(prop_text, False):
    dup = check_duplicate(prop_text, True)
    newest_cell = proposals.find(dup)
    proposals.update_cell(newest_cell.row, (newest_cell.col + 4), data)
    return

  if prop_text in proposals.col_values(1):
    prop_cell = proposals.find(prop_text)
  elif opp_text in proposals.col_values(1):
    prop_cell = proposals.find(opp_text)
  elif mod_text in proposals.col_values(1):
    prop_cell = proposals.find(mod_text)
  elif ab_text in proposals.col_values(1):
    prop_cell = proposals.find(ab_text)
  else:
    print("Error: Proposal text Not Found!! Unable to add ID")
    return
  proposals.update_cell(prop_cell.row, (prop_cell.col + 8), data)
  return

# recieves vote reaction information, parses, and updates cells
def vote(id, vote, user):
  try:
    prop_cell = proposals.find(str(id))
  except Exception as exp:
    return("Error, Proposal not found.\n" + str(exp))
  # finds all the relevant cells in the same row
  time_cell = proposals.cell(prop_cell.row, (prop_cell.col - 4))
  vote_cell = proposals.cell(prop_cell.row, (prop_cell.col - 5))
  status_cell = proposals.cell(prop_cell.row, (prop_cell.col - 6))
  text_cell = proposals.cell(prop_cell.row, (prop_cell.col - 8))
  # flips vote if the proposal is opposite
  if text_cell.value.startswith("<OPPOSITE>"):
    if vote:
      print("opposite vote detected, switching to nay")
      vote = False
    else:
      print("opposite vote detected, switching to yay")
      vote = True
  # gets current time data and cell time for later comparison
  t = datetime.datetime.now()
  p = str(time_cell.value)
  p = parse(p)
  print("time of vote:\n" + str(t))
  # returns error if user not registered
  if not check_register(user):
    return("Player Not Registered. In order to vote you must first redeem a nomic point during a big_sarnt stream. Then, register your discord ID using !register <your_twitch_username>")
  # returns error if voting period has expired
  if t > p:
    return("This proposal can no longer be voted on, the time is expired")
  # returns error if proposal already passed
  if str(status_cell.value) == "PASSED":
    return("This proposal can no longer be voted on, it passed already")
  # returns error if proposal already failed
  if str(status_cell.value) == "FAILED":
    return("This proposal can no longer be voted on, it failed. Try making a new proposal.")
  # returns error if player tries casting two of the same vote
  if not single_vote(id, user, vote):
    if vote:
      return("User " + user + " already voted yay")
    else:
      return("User " + user + " already voted nay")
  # if the reaction was a yay vote
  if vote:
    tally = int(vote_cell.value) - 1
    # passes the vote if this vote was the last vote needed
    if tally < 1:
      r = pass_law(id)
      proposals.update_cell(status_cell.row, status_cell.col, "PASSED")
      support(id, user, True)
      return(r)
    else:
      proposals.update_cell(vote_cell.row, vote_cell.col, tally)
      support(id, user, True)
      return("yay vote registered")
  # if the reaction was a nay vote
  else:
    tally = int(vote_cell.value) + 1
    proposals.update_cell(vote_cell.row, vote_cell.col, tally)
    support(id, user, False)
    return("nay vote registered")

def pass_law(id):
  prop_cell = proposals.find(str(id))
  status_cell = proposals.cell(prop_cell.row, (prop_cell.col - 6))
  player_cell = proposals.cell(prop_cell.row, (prop_cell.col - 7))
  text_cell = proposals.cell(prop_cell.row, (prop_cell.col - 8))
  
  l = rulez.col_values(1)
  l.pop(0)
  number = len(l)
  player = player_cell.value
  text = str(text_cell.value)
  if text.startswith("<OPPOSITE>"):
    words = text.replace("<OPPOSITE>", "")
  if text.startswith("Modification to rule"):
    words = text.split()
    number = words[3]
    number = number.replace(":", "")
    words = words[4:]
    words = " ".join(words)
    old_rule = rulez.find(number)
    data = [str(number), str(words)]
    rulez.update_cell(old_rule.row, old_rule.col, number)
    rulez.update_cell(old_rule.row, old_rule.col + 1, words)
  if text.startswith("Abolish Rule"):
    words = text.split()
    number = int(words[2])
    print("abolishing rule " + str(number) + "...")
    old_rule = rulez.find(str(number))
    rulez.delete_row(old_rule.row)
    proposals.update_cell(status_cell.row, status_cell.col, "PASSED")
    checker = True
    try:
      next = number + 1
      number_update = rulez.find(str(next))
    except Exception as exp:
      print("Deleted last Rule! " + str(exp))
      checker = False
    while checker:
      rulez.update_cell(number_update.row, number_update.col, number)
      next = int(number_update.value) + 1
      try:
        number_update = rulez.find(str(next))
      except Exception:
        print("done deleting")
        return
      number += 1
      if number_update.value == "" or number_update.value == "None":
        checker = False
        return
      

  else:
    data = [number, text, player]
    rulez.append_row(data)
    proposals.update_cell(status_cell.row, status_cell.col, "PASSED")
  return("PASSED")

# Returns false if user already cast vote of the same type
def single_vote(id, user, vote):
  prop_cell = proposals.find(str(id))
  opponents = proposals.cell(prop_cell.row, (prop_cell.col - 2))
  supporters = proposals.cell(prop_cell.row, (prop_cell.col - 3))
  if vote:
    if user in str(supporters.value):
      return False
    else:
      return True
  else:
    if user in str(opponents.value):
      return False
    else: 
      return True

# adds or removes the user to list of supporters or opponents based on their vote
def support(id, user, vote):
  prop_cell = proposals.find(str(id))
  opponents = proposals.cell(prop_cell.row, (prop_cell.col - 2))
  supporters = proposals.cell(prop_cell.row, (prop_cell.col - 3))
  if vote:
    if user in str(supporters.value):
      return
    if str(supporters.value) == "None" or "":
      print("no support yet")
      proposals.update_cell(supporters.row, supporters.col, user)
    else:
      new_list = (str(supporters.value) + ", " + user)
      proposals.update_cell(supporters.row, supporters.col, new_list)
    s = str(opponents.value)
    s = s.replace(", " + user, "")
    s = s.replace(user, "")
    if s == "":
      s = "None"
    proposals.update_cell(opponents.row, opponents.col, s)
  else:
    if user in str(opponents.value):
      return
    if str(opponents.value) == "None" or "":
      print("no opponents yet")
      proposals.update_cell(opponents.row, opponents.col, user)
    else:
      new_list = (str(opponents.value) + ", " + user)
      proposals.update_cell(opponents.row, opponents.col, new_list)
    s = str(supporters.value)
    s = s.replace(", " + user, "")
    s = s.replace(user, "")
    if s == "":
      s = "None"
    proposals.update_cell(supporters.row, supporters.col, s)



# adds players discord name to their twitch name
def register(player, disc):
  
  try:
    # looks for the player in twitch names
    if player in players.col_values(1):
      cell = players.find(player)
      new_name = players.cell(cell.row, (cell.col + 1))
      print("player " + player + " found")
      print(str(new_name.value))
    # if player not found, returns error
    else:
      print("twitch username '" + player + "' not found\n")
      return("Twitch username '" + player + "' not found\n\nCheck spelling and try again. Names are case sensitive! You need to redeem Nomic points on Big_Sarnts channel to start playing.")
    # if discord registered already, returns error
    if disc in players.col_values(2):
      print("1")
      print("Player's discord '" + str(disc) + "'\nalready registered")
      return("Player's discord '" + str(disc) + "' already registered\n")
    # returns error if discord name isnt empty or none
    elif str(new_name.value) != "" and str(new_name.value) != "None":
      print("player already registered")
      return("Player " + str(player) + " already registered to discord " + new_name.value + ". Command aborted. Contact Big_Sarnt if there is an error.")
    # finally registers player if no errors
    else:
      data = str(disc)
      print("updating Cell with discord info...")
      players.update_cell(new_name.row, new_name.col, data)
      print("player " + data + " registered")
      data = data[:-5]
      return("Thank you for registering, " + data + ". You are now bound by the rules. If you change your discord name, let Big Sarnt know because it breaks your registration!")
  
  # catch-all for error messages, will send message to discord
  except Exception as ex:
    template = "{0} exception. \n\ndetails:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print("ERROR: " + message)
    return ("ERROR: " + message)