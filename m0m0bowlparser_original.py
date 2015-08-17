import os
import re
import sys

# The Roster class
class Roster:
   # __init__
   # The initialization of the class
   def __init__(self):
      self.roster = {}    # The initial roster dict.
    
   def add(self, player, cost):
      self.roster[player] = cost  # Store the player as the key, the cost as the value.
    
   def remove(self, player):
      cost = self.roster[player]  # Get the cost for that player being removed.
      del self.roster[player]     # Delete the player from the team's roster dict.
      return cost                 # Return the cost for future use.
    
   def getPlayer(self, player):    # Return the player's cost.
      return self.roster[player]  
        
   def getRoster(self):            # Return the team's roster.
      return self.roster          
        
   def findPlayer(self, player):   # Return true if the player is in the roster. Else return false.
      if player in self.roster: 
         return True
      else:
         return False
    
   def totalValue(self):
      total = 0
      for player in self.roster:
         total = int(self.roster[player][1:]) + total        
      return "$" + str(total)
   

def readTransactions(args):
   transactions = []

   counter = 1
   file = open(args[1], "r")
   tradeAccepted = False       # Check to see if a trade was already accepted (but not processed).
   addedNoCost = None          # This is where the player added, but no cost bug happens and the values are stored..
    
   while True:
      line = file.readline()
      if not line: break
        
      # All the regex strings that we want to search for.
      team = re.search("[A-Z0-9]{2,4}", line)
      trans = re.search("[aA]dded|[dD]ropped|[dD]rafted|[tT]raded", line)
      player = re.search("([a-zA-Z\-\.\']+\s[a-zA-Z\-\.]+[IVSJr\s\.]*\*?,\s[a-zA-Z]+)|([0-9a-zA-Z]+\sD/ST,\s[a-zA-Z]+)", line)
      cost = re.search("\$\d+", line)
      date = re.search("[a-zA-Z]{3}, [a-zA-Z]{3} [0-9]{1,2}", line)
      accepted = re.search("[aA]ccepted [tT]rade", line)
        
      # Using this to stop trades accepted (and duplicate player moves). Only care about trade processed.
      if accepted != None: tradeAccepted = True
                           
      # Have to use this since not all the players will start with costs via the transactions page
      costResult = ""
      if cost != None: costResult = cost.group()
        
      # This is to handle the issues with players being added from FA, but there's no value.
      # The value is in the next transaction message.
      if cost == None and trans != None and trans.group() == "added":   
         addedNoCost = [team.group(), trans.group(), re.sub("\*", "", player.group()), "", ""]
        
      # Have to check for "team != None" since it doesn't always find the team name
      if trans != None and team != None and not tradeAccepted: 
            
         # Getting rid of those injury stars (*)
         player = re.sub("\*", "", player.group())
            
         # If there's a trade transaction, get the team that they were traded to and store it into the list.
         if trans.group() == "traded" or trans.group() == "Traded":
            toWhom = re.search("to\s[a-zA-Z0-9]+", line)
            toWhom = re.sub("to ", "", toWhom.group())
            transactions.append([team.group(), trans.group(), player, costResult, toWhom])
            
         # If there's the add transaction but no cost. This will take the cost that was associated
         # with the dropped player and put it with the added player. (Stupid ESPN)
         elif addedNoCost != None and trans.group() == "dropped" and cost != None:
            addedNoCost[3] = cost.group()
            transactions.append(addedNoCost)
            transactions.append([team.group(), trans.group(), player, "", ""])
            addedNoCost = None
            
            # If there's an added or dropped player with no issues, store it.
         elif addedNoCost == None:
            transactions.append([team.group(), trans.group(), player, costResult, ""])
         else:
            None
        
      # When you find another date, reset tradeAccepted back to False again.
      if date != None: tradeAccepted = False
   
   # Puts the transactions list in chronological order.
   transactions.reverse()  
   file.close()
    
   return transactions
    
def readDraftResults(args):
   file = open(args[2], "r")
   draft = {}          # The dict containing all the drafted players.
   while True:
      line = file.readline()
      if not line: break
        
      player = re.search("([a-zA-Z\-\.\']+\s[a-zA-Z\-\.]+[IVSJr\s\.]*\*?,\s[a-zA-Z]+)|([0-9a-zA-Z]+\sD/ST D/ST)", line)
      cost = re.search("\$\d+", line)
                       
      if player != None and cost != None:
         if re.search("D/ST", player.group()) != None:   # If there's a D/ST picked up
            player =  defenseFix(player.group())        # Use the defenseFix() method to fix it.
         else:    
            player = re.sub("\*", "", player.group())   # Else remove any injury stars from the name.
         draft[player] = cost.group()                    # And add that player to the drafted list, with their cost.
    
   file.close()
   return draft        # Return the dictionary of the drafted players.
        
def processTransactions(trans, draft):
   rosters = {"Waivers": Roster()}
   originalTeams = {}
   
   for transaction in trans:
      if transaction[0] not in rosters: 
        rosters[transaction[0]] = Roster()
      roster = rosters[transaction[0]]
        
      # When a player is first drafted
      if transaction[1].lower() == "drafted":
         # We want to take the draft results and add the costs that were given to them here.
         # Use another file to store the draft results and then take the costs for each player.
         # The second argument for the add() method shouldn't be transaction[3]
         cost = draft[transaction[2]]        # Get the player's cost from the draft list.
         roster.add(transaction[2], cost)    # Add the player to that roster with the draft cost.
         originalTeams[transaction[2]] = (transaction[0], draft[transaction[2]])
            
      # When a player is first added to the roster.
      elif transaction[1].lower() == "added":
         waivers = rosters["Waivers"]
         # If they weren't dropped to the waivers already (for the drafted players or picked up before)
         if waivers.findPlayer(transaction[2]):
            cost = waivers.remove(transaction[2])   # Get the cost of the player, remove from the waivers
            if transaction[2] in originalTeams and transaction[0] == originalTeams[transaction[2]][0]:
              roster.add(transaction[2], originalTeams[transaction[2]][1])
            else:
              roster.add(transaction[2], transaction[3])        # Add the player with the cost that was stored in the waivers.
         # If it's the first time that they've been picked up.
         else:
            roster.add(transaction[2], transaction[3])
                
      # When a player is dropped from a team.
      elif transaction[1].lower() == "dropped":
         cost = roster.remove(transaction[2])    # Remove the player from the team.
         waivers = rosters["Waivers"]            # Get the waivers roster
         waivers.add(transaction[2], cost)       # Add them to the waivers "roster"
            
      # How to handle trades.
      elif transaction[1].lower() == "traded":
         # This is where I want to remove the person from one roster, but add them to the other one.
         # Will need to use remove() and add() methods from the Roster() class to pull this off.
         cost = roster.remove(transaction[2])    # Remove them from the team, get the cost of that player.
         teamTradedTo = rosters[transaction[4]]  # Get the team they're being trade to's roster.
         teamTradedTo.add(transaction[2], cost)  # Add them to that roster.
        
        # Output an error if you can't process the transaction.
      else:
         print "Found an error with the results. " + str(transaction)

   return rosters

# outputRosters()
# Outputs the draft picks for each team into the output file, as well as all the
# free agents/waivers.
def outputRosters(rosters, args):
   teams = open(args[3], "r")  # Use the teams dictionary to identify full names from nicknames.
   output = open(args[4], "w")# The output file.
   values = []
   while True:
      line = teams.readline()
      if not line: break
      line = line.split("-")      
      fullname = line[1].strip()  # Stripping of white space at the end of the lines.
      nickname = line[0].strip()  # Stripping of white space at the end of the lines.
      finish = line[2].strip()

      roster = rosters[nickname].getRoster() # Get the dict that has all the players/costs for that team.
      
        
      # Output the team names, then the players and costs for that team.
      output.write(fullname + "\n")
      ordered = [(int(roster[player][1:]), player) for player in roster.keys()]
      ordered = sorted(ordered, key = lambda x : (-x[0], x[1]))
      for item in ordered: output.write("{:>4}  {}\n".format("$" + str(item[0]), item[1]))
      value = rosters[nickname].totalValue()
      output.write("-- Total Value:\t" + value + "\n")
      output.write("\n")
      values.append((fullname, value, finish))
      
   waivers = rosters["Waivers"].getRoster().keys() # Get the keys.
   waivers.sort()  # Sort the keys in alphabetical order.
   
    # Outputs all the players that had costs and picked up from the waivers/free agents.
   output.write("WAIVERS/FREE AGENTS\n")
   for player in waivers: output.write("{:>5}  {}\n".format(rosters["Waivers"].getRoster()[player], player)) 
   output.write("\n")
   
   values = sorted(values, key = lambda x: (-int(x[1][1:]), x[0]))   # A way to sort the teams' values. Also, converting
                                                                     # the $ into ints before sorting through them.
   output.write("Value\tFinish\tTeam Name\n")
   output.write("=================================\n")
   # for team in values:  output.write(team[1] + "\t" + team[2] + "\t\t" + team[0] + "\n")   # Output, go.
   for team in values: output.write("{:>5}\t{:>4}\t{}\n".format(team[1], team[2], team[0]))
   output.close()
   teams.close()    

        
    
# defenseFix()
# This is kinda dumb, but for some reason, ESPN returns "(Team name) D/ST D/ST" instead of
# "(Team name) D/ST, (Team city)". So to fix it, have to use this trick and have to store all the teams
# in a dictionary.
def defenseFix(defense):
    defenses = { # The dict that associates the team nickname to the city (shorthand)
        "Ravens": "Bal",
        "Bengals": "Cin",
        "Browns": "Cle",
        "Steelers": "Pit",
        "Texans": "Hou",
        "Colts": "Ind",
        "Jaguars": "Jac",
        "Titans": "Ten",
        "Bills": "Buf",
        "Dolphins": "Mia",
        "Patriots": "NE",
        "Jets": "NYJ",
        "Broncos": "Den",
        "Chiefs": "KC",
        "Raiders": "Oak",
        "Chargers": "SD",
        "Bears": "Chi",
        "Lions": "Det",
        "Packers": "GB",
        "Vikings": "Min",
        "Falcons": "Atl",
        "Panthers": "Car",
        "Saints": "NO",
        "Buccaneers": "TB",
        "Cowboys": "Dal",
        "Giants": "NYG",
        "Eagles": "Phi",
        "Redskins": "Wsh",
        "Cardinals": "Ari",
        "49ers": "SF",
        "Seahawks": "Sea",
        "Rams": "StL"
    }
    
    # If the team that was passed through the method starts with one of those nicks in
    # the dict, return "(mascot name) D/ST, (city name, shorthand)"
    for d in defenses:
        if defense.startswith(d): return d + " D/ST, " + defenses[d]

    # If the code can't find the team, output an error.
    print "Team not found!"
    
def main(argv):
   transactions = readTransactions(argv)
   draftresults = readDraftResults(argv)
   rosters = processTransactions(transactions, draftresults)
   outputRosters(rosters, argv)

if __name__ == "__main__":
   main(sys.argv)