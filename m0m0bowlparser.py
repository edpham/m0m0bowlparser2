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
    
    while True:
        line = file.readline()
        if not line: break
        
        # All the regex strings that we want to search for.
        team = re.search("[A-Z0-9]{2,4}", line)
        trans = re.search("[aA]dded|[dD]ropped|[dD]rafted|[tT]raded", line)
        player = re.search("[a-zA-Z\-\.]+\s[a-zA-Z\-\.]+,\s[a-zA-Z]+|[0-9a-zA-Z]+\sD/ST,\s[a-zA-Z]+", line)
        cost = re.search("\$\d+", line)
        date = re.search("[a-zA-Z]{3}, [a-zA-Z]{3} [0-9]{1,2}", line)
        accepted = re.search("[aA]ccepted [tT]rade", line)
        
        if accepted != None: tradeAccepted = True

                    
        # Have to use this since not all the players will start with costs via the transactions page
        costResult = "None"
        if cost != None: costResult = cost.group()
        # Have to check for "team != None" since it doesn't always find the team name
        if trans != None and team != None and not tradeAccepted: 
            if trans.group() == "traded" or trans.group() == "Traded":
                toWhom = re.search("to\s[a-zA-Z0-9]+", line)
                toWhom = re.sub("to ", "", toWhom.group())
                transactions.append([team.group(), trans.group(), player.group(), costResult, toWhom])
            else:    
                transactions.append([team.group(), trans.group(), player.group(), costResult, ""])
        
        if date != None: tradeAccepted = False
	
    # Puts the transactions list in chronological order.
    transactions.reverse()  
    # Output the results of all the transactions made (for debugging purposes)
    for transaction in transactions: output.write(str(transaction) + "\n")
		
    output.close()
    file.close()
    
    return transactions
        
def processTransactions(trans):
    rosters = {"Waivers": Roster()}
    
    for transaction in trans:
        if transaction[0] not in rosters: rosters[transaction[0]] = Roster()
        roster = rosters[transaction[0]]
        
        # When a player is first drafted
        if transaction[1].lower() == "drafted":
            # We want to take the draft results and add the costs that were given to them here.
            # Use another file to store the draft results and then take the costs for each player.
            # The second argument for the add() method shouldn't be transaction[3]
            roster.add(transaction[2], transaction[3])
            
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
    

	
transactions = readTransactions(sys.argv)
rosters = processTransactions(transactions)