import os
import re
import sys

class Roster:
    def __init__(self):
        self.roster = {}
        self.spots = 0
    
    def add(self, player, cost):
        self.roster[player] = cost
    
    def remove(self, player):
        cost = self.roster[player]
        if player not in self.roster: 
            print player + "not found!"
        else:
            del self.roster[player]
        return cost
    
    def getPlayer(self, player):
        return self.roster[player]
        
    def getRoster(self):
        return self.roster
        
    def findPlayer(self, player):
        if player in self.roster: 
            return True
        else:
            return False
   

def readTransactions(args):
    transactions = []

    counter = 1
    file = open(args[1], "r")
    output = open("transactions_processed.txt", "w") # To use for debugging purposes
    tradeAccepted = False
    addedNoCost = None
    
    while True:
        line = file.readline()
        if not line: break
        
        # All the regex strings that we want to search for.
        team = re.search("[A-Z0-9]{2,4}", line)
        trans = re.search("[aA]dded|[dD]ropped|[dD]rafted|[tT]raded", line)
        player = re.search("([a-zA-Z\-\.]+\s[a-zA-Z\-\.]+\*?,\s[a-zA-Z]+)|([0-9a-zA-Z]+\sD/ST,\s[a-zA-Z]+)", line)
        cost = re.search("\$\d+", line)
        date = re.search("[a-zA-Z]{3}, [a-zA-Z]{3} [0-9]{1,2}", line)
        accepted = re.search("[aA]ccepted [tT]rade", line)
        
        if accepted != None: tradeAccepted = True
                           
        # Have to use this since not all the players will start with costs via the transactions page
        costResult = ""
        if cost != None: costResult = cost.group()
        if cost == None and trans != None and trans.group() == "added":
            addedNoCost = [team.group(), trans.group(), re.sub("\*", "", player.group()), "", ""]
        
        # Have to check for "team != None" since it doesn't always find the team name
        if trans != None and team != None and not tradeAccepted: 
            
            # Getting rid of those injury stars (*)
            player = re.sub("\*", "", player.group())
            if trans.group() == "traded" or trans.group() == "Traded":
                toWhom = re.search("to\s[a-zA-Z0-9]+", line)
                toWhom = re.sub("to ", "", toWhom.group())
                transactions.append([team.group(), trans.group(), player, costResult, toWhom])
            elif addedNoCost != None and trans.group() == "dropped" and cost != None:
                addedNoCost[3] = cost.group()
                transactions.append(addedNoCost)
                transactions.append([team.group(), trans.group(), player, "", ""])
                addedNoCost = None
            elif addedNoCost == None:
                transactions.append([team.group(), trans.group(), player, costResult, ""])
            else:
                None
        
        if date != None: tradeAccepted = False
	
    # Puts the transactions list in chronological order.
    transactions.reverse()  
    # Output the results of all the transactions made (for debugging purposes)
    for transaction in transactions: output.write(str(transaction) + "\n")
		
    output.close()
    file.close()
    
    return transactions
    
def readDraftResults(args):
    file = open(args[2], "r")
    draft = {}
    while True:
        line = file.readline()
        if not line: break
        
        player = re.search("([a-zA-Z\-\.]+\s[a-zA-Z\-\.]+\*?,\s[a-zA-Z]+)|([0-9a-zA-Z]+\sD/ST D/ST)", line)
        cost = re.search("\$\d+", line)
                       
        if player != None and cost != None:
            if re.search("D/ST", player.group()) != None:
                player =  defenseFix(player.group())
            else:    
                player = re.sub("\*", "", player.group())
            draft[player] = cost.group()
    
    file.close()
    return draft
        
def processTransactions(trans, draft):
    rosters = {"Waivers": Roster()}
    
    for transaction in trans:
        if transaction[0] not in rosters: rosters[transaction[0]] = Roster()
        roster = rosters[transaction[0]]
        
        # When a player is first drafted
        if transaction[1].lower() == "drafted":
            # We want to take the draft results and add the costs that were given to them here.
            # Use another file to store the draft results and then take the costs for each player.
            # The second argument for the add() method shouldn't be transaction[3]
            cost = draft[transaction[2]]   
            roster.add(transaction[2], cost)
            
        # When a player is first added to the roster.
        elif transaction[1].lower() == "added":
            waivers = rosters["Waivers"]
            # If they weren't dropped to the waivers already (for the drafted players or picked up before)
            if waivers.findPlayer(transaction[2]):
                cost = waivers.remove(transaction[2])
                roster.add(transaction[2], cost)
            # If it's the first time that they've been picked up.
            else:
                roster.add(transaction[2], transaction[3])
                
        # When a player is dropped from a team.
        elif transaction[1].lower() == "dropped":
            # print transaction, roster.getRoster(), '\n'
            cost = roster.remove(transaction[2])
            waivers = rosters["Waivers"]
            waivers.add(transaction[2], cost)
            
        # How to handle trades.
        elif transaction[1].lower() == "traded":
			# This is where I want to remove the person from one roster, but add them to the other one.
			# Will need to use remove() and add() methods from the Roster() class to pull this off.
            cost = roster.remove(transaction[2])
            teamTradedTo = rosters[transaction[4]]
            teamTradedTo.add(transaction[2], cost)
            
        else:
            print "Found an error with the results. " + str(transaction)
        
    return rosters
    
def outputRosters(rosters):
    teams = open("teams.txt", "r")
    output = open("output.txt", "w")
    while True:
        line = teams.readline()
        if not line: break
        line = line.split("-")
        fullname = line[1].strip()
        nickname = line[0].strip()

        team = rosters[nickname]
        roster = team.getRoster()
        
        output.write(fullname + "\n")
        for player in roster: output.write(player + "\t" + roster[player] + "\n")
        output.write("\n")
    
    waivers = rosters["Waivers"].getRoster().keys()
    waivers.sort()
    
    output.write("WAIVERS/FREE AGENTS\n")
    for player in waivers: output.write(player + "\t" + rosters["Waivers"].getRoster()[player] + "\n") 
    
    
    output.close()
    teams.close()    

        
    
# defenseFix()
# This is kinda dumb, but for some reason, ESPN returns "(Team name) D/ST D/ST" instead of
# "(Team name) D/ST, (Team city)". So to fix it, have to use this trick and have to store all the teams
# in a dictionary.
def defenseFix(defense):
    defenses = {
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
    
    for d in defenses:
        if defense.startswith(d): return d + " D/ST, " + defenses[d]
    
    
if __name__ == "__main__":
    transactions = readTransactions(sys.argv)
    draftresults = readDraftResults(sys.argv)
    rosters = processTransactions(transactions, draftresults)
    outputRosters(rosters)