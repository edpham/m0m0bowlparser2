To run the code for the latest version of the m0m0 Bowl Parser, you need three text files:
    (1) a file containing all the transactions made from ESPN's fantasy football league (in reverse chronological order)
    (2) a file containing the draft results, having all the draft picks made by the teams and their costs (from ESPN's draft results page)
    (3) a file containing the teams' abbreviations and their full names (in the format: [team abbr] - [team name])
    
Once you have those two files, you need to run the following line in the command prompt:
    python m0m0bowlparser.py [path of the transactions file] [path of the draft results]
    
The file should be outputted into the file name "output.txt", where you can see the current costs for the players and which teams own what players.

If you have any questions, feel free to e-mail me at me @ edpham (dot) net.