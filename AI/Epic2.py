import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

import math

# Title: CS421-Homework-3-MiniMax-with-Alpha-Beta-Pruning
# @authors - Nick Tabra, Hung Vu
# @date - 10/7/2025

# File copied from Random.py and modified

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "EpicAgentName2")
        self.whichPlayer = None
    
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        # track which side we're on
        if self.whichPlayer == None:
            self.whichPlayer = getCurrPlayerInventory(currentState).player

        depth = 3
        root = self.makeNode(None, currentState, 0, None)
        bestMove = None
        bestVal = -math.inf

        children = self.expandNode(root)
        if not children:
            return Move(END, None, None)


        for child in children:
            val = self.miniMax(child, depth-1, -math.inf, math.inf, currentState)
            if val > bestVal:
                bestVal = val
                bestMove = child["move"]

        #fallback in case nothing gets chosen
        if bestMove is None:
            return Move(END, None, None)
        
        return bestMove

    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass


    ##
    #
    #miniMax
    #Description: Takes an initial node, runs a minimax algorithm, adjusting the eval of the nodes
    #
    #Parameters:
    #   initNode - the inital node
    #   depth - the depth to look down (how many moves ahead)
    #   maximizing - 0-1 val (0 if we are max, 1 if were min)
    #
    #Return:
    #   best child node
    def miniMax(self, node, depth, alpha, beta, currentState):
        state = node["state"]

        # base case
        if depth == 0 or getWinner(state) is not None:
            return self.utility(state)

        myInv = getCurrPlayerInventory(currentState)

        isMax = (state.whoseTurn == self.whichPlayer)
        nodeList = self.expandNode(node)

        # fallback if no legal moves (END only)
        if not nodeList:
            return self.utility(state) + random.uniform(-2, 2)

        # ----------- TOP-N-PERCENT NODE FILTER -----------
        keep_ratio = 0.05  # keep the top 30% of nodes
        nodeList.sort(key=lambda n: n["eval"], reverse=isMax)
        k = max(1, int(len(nodeList) * keep_ratio))
        nodeList = nodeList[:k]
        # -------------------------------------------------

        # α-β search
        if isMax:
            value = -math.inf
            for child in nodeList:
                val = self.miniMax(child, depth - 1, alpha, beta, currentState)
                value = max(value, val)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # prune
            return value
        else:
            value = math.inf
            for child in nodeList:
                val = self.miniMax(child, depth - 1, alpha, beta, currentState)
                value = min(value, val)
                beta = min(beta, value)
                if alpha >= beta:
                    break  # prune
            return value






    ##
    # makeNode
    # description: creates a search tree node (copied from HW#2)
    #
    # paramaters:
    # move - move taken from parent state
    # state - resulting gamestate after the move
    # depth - depth in the search tree
    # parent - parent node (or none if the root)
    #
    # returns dict representing the node
    ##
    def makeNode(self, move, state, depth, parent):
        return{
            "move": move,
            "state": state,
            "depth": depth,
            "eval": self.utility(state) + depth, 
            "parent": parent
        }
    
    ##
    # bestNode
    # Description: finds the node with the best evaluation (utility) (copied from HW#2)
    #
    # Parameters: 
    # nodeList - the list of nodes to search 
    # maximizing - the current player's turn to choose for (for minimax)
    #
    # Returns: our "node" representation
    def bestMove(self, nodeList, maximizing):
        # Type checking
        if not isinstance(nodeList, list):
            print("bestMove: ", nodeList , " is not a list of node")
            return None
        # start with the first node as the best
        bestNode = nodeList[0]

        # List to track nodes that have equal evaluation to the best node
        bestList = []

        # (HW3) Get the node based on player turn max (us) vs mini (opp)

        # go through each node in the list
        if maximizing == PLAYER_ONE:
            for node in nodeList:
                # if this node has a smaller eval score than our current best
                if node["eval"] < bestNode["eval"]:
                    #update bestNode
                    bestNode = node
                    #clear the list equal and best nodes (a new best node is found, so no similar nodes)
                    bestList.clear()
                elif node["eval"] == bestNode["eval"]:
                    bestList.append(node)
        elif maximizing == PLAYER_TWO:
            for node in nodeList:
                # if this node has a bigger eval score than our current best
                if node["eval"] > bestNode["eval"]:
                    #update bestNode
                    bestNode = node
                    #clear the list equal and best nodes (a new best node is found, so no similar nodes)
                    bestList.clear()
                elif node["eval"] == bestNode["eval"]:
                    bestList.append(node)
            
        # If we have multiple best nodes, randomly choose between them (avoid cycling moves)
        if len(bestList) > 0 :
            bestList.append(bestNode)
            return bestList[random.randint(0, len(bestList) - 1)]
        else:
            # There's only one best node    
            return bestNode

    ##
    # expandNode
    # Description: takes an existing node and return a list of nodes (copied from hw2)
    #
    # Parameters:
    # initNode - the initial node
    #
    # Returns: list of nodes
    def expandNode(self, initNode):
        if initNode == None:
            return None
        moves = listAllLegalMoves(initNode["state"])
        initState = initNode["state"]
        initDepth = initNode["depth"]

        nodes = []

        # build nodes for each possible moves
        for m in moves:
            nextState = getNextStateAdversarial(initState, m)
            # these nodes are +1 depth from initial, and their parent is always the initNode
            node = self.makeNode(m, nextState, (initDepth + 1), initNode) 
            nodes.append(node)

        return nodes

    ## 
    #utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   currentState - The current GameState object
    #   
    #Returns: number from -10000 to 10000
    def utility(self, currentState):
        # Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        enemyInv = getEnemyInv(self, currentState)

        # initial utility starts at 0 (game is "even")
        ret_utility = 0

        # Food related
        ret_utility += self.food_utility(myInv, enemyInv) + self.worker_utility(myInv, currentState)

        # Combat related
        ret_utility += self.combat_utility(myInv, enemyInv, currentState)

        if self.whichPlayer == currentState.whoseTurn:
            return ret_utility
        else:
            return -ret_utility

    ## 
    #food_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   
    #Returns: number from -10000 to 10000
    def food_utility(self, myInv, enemyInv):
        myFoodCount = myInv.foodCount
        enemyFoodCount = enemyInv.foodCount

        # Check for wins
        if myFoodCount == FOOD_GOAL:
            return 10000
        elif enemyFoodCount == FOOD_GOAL:
            return -10000
        
        # Affect the utility based on difference
        myHue = round((myFoodCount / FOOD_GOAL) * 900)
        enemyHue = -round((enemyFoodCount / FOOD_GOAL) * 900)

        # Return difference and worker utility
        return myHue + enemyHue

    ##
    #worker_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -1000 to 1000
    def worker_utility(self, myInv, currentState):
        workerHue = 0
        enemyId = (myInv.player+1) % 2

        myReturns = getConstrList(currentState, myInv.player, (ANTHILL, TUNNEL))
        enemyReturns = getConstrList(currentState, enemyId, (ANTHILL, TUNNEL))

        myWorkers = getAntList(currentState, myInv.player, (WORKER,))
        enemyWorkers = getAntList(currentState, enemyId, (WORKER,))
        
        foodList = getConstrList(currentState, None, (FOOD,))
        


        if len(myReturns) == 0 or len(enemyReturns) == 0 or len(foodList) == 0:
            return 0
        
        if len(myWorkers) == 0:
            workerHue -= 500

        if len(enemyWorkers) == 0:
            workerHue += 500

        if len(myWorkers) > 2:
            workerHue -= 1000 + 100*len(myWorkers)
        
        if len(enemyWorkers) > 2:
            workerHue += 1000 + 100*len(enemyWorkers)

        for worker in myWorkers:
            if worker.carrying and worker.coords in myReturns:
                workerHue += 50
            elif worker.carrying:
                distOne = approxDist(worker.coords, myReturns[0].coords)
                distTwo = approxDist(worker.coords, myReturns[1].coords)
                workerHue += 25 - min(distOne, distTwo)
            elif worker.coords in foodList:
                workerHue += 50
            else:
                distOne = approxDist(worker.coords, foodList[0].coords)
                distTwo = approxDist(worker.coords, foodList[1].coords)
                distThree = approxDist(worker.coords, foodList[2].coords)
                distFour = approxDist(worker.coords, foodList[3].coords)
                workerHue += 15 - min(distOne, distTwo, distThree, distFour)
            

        for worker in enemyWorkers:
            if worker.carrying and worker.coords in myReturns:
                workerHue -= 50
            elif worker.carrying:
                distOne = approxDist(worker.coords, enemyReturns[0].coords)
                distTwo = approxDist(worker.coords, enemyReturns[1].coords)
                workerHue -= 25 - min(distOne, distTwo)
            elif worker.coords in foodList:
                workerHue -= 50
            else:
                distOne = approxDist(worker.coords, foodList[0].coords)
                distTwo = approxDist(worker.coords, foodList[1].coords)
                distThree = approxDist(worker.coords, foodList[2].coords)
                distFour = approxDist(worker.coords, foodList[3].coords)
                workerHue -= 15 - min(distOne, distTwo, distThree, distFour)


        return workerHue

    ##
    #combat_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -10000 to 10000
    def combat_utility(self, myInv, enemyInv, currentState):
        # Check for wins
        myQueen = myInv.getQueen()
        enemyQueen = enemyInv.getQueen()

        myAntHill = myInv.getAnthill()
        enemyAntHill = enemyInv.getAnthill()

        if myQueen == None or myQueen.health <= 0:
            return -10000
        elif enemyQueen == None or enemyQueen.health <= 0:
            return 10000
        elif myAntHill.captureHealth == 0:
            return -10000
        elif enemyAntHill.captureHealth == 0:
            return 10000

        
        # Affect the utility based on difference in queen hp
        myQueenHue = round((myQueen.health / UNIT_STATS[QUEEN][HEALTH]) * 4500)
        enemyQueenHue = -round((enemyQueen.health / UNIT_STATS[QUEEN][HEALTH]) * 4500)

        # Affect the utility based on difference in queen hp
        myAnthillHue = round((myAntHill.captureHealth / CONSTR_STATS[ANTHILL][CAP_HEALTH]) * 4500)
        enemyAnthillHue = -round((enemyAntHill.captureHealth / CONSTR_STATS[ANTHILL][CAP_HEALTH]) * 4500)

        # Contributes to combat hueristic
        combatHue = myQueenHue + enemyQueenHue + myAnthillHue + enemyAnthillHue
        
        # Each ant type contributes to hueristic
        combatHue += self.drone_utility(myInv, enemyInv, currentState)
        combatHue += self.soldier_utility(myInv, enemyInv, currentState)
        combatHue += self.queen_utility(myInv, enemyInv, currentState)
        combatHue += self.ranged_utility(myInv, enemyInv, currentState)
        
        # Total army composition affects hueristic
        combatHue += self.attack_inventory_utility(myInv, enemyInv, currentState)

        return combatHue

    ##
    #attack_inventory_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -500 to 500
    def attack_inventory_utility(self, myInv, enemyInv, currentState):
        inventoryHue = 0

        myArmy = getAntList(currentState, myInv.player, (SOLDIER,DRONE,R_SOLDIER))
        enemyArmy = getAntList(currentState, enemyInv.player, (SOLDIER,DRONE,R_SOLDIER))

        if len(myArmy) == len(enemyArmy):
            inventoryHue += 0
        elif len(myArmy) == len(enemyArmy) + 1:
            inventoryHue += 50
        elif len(enemyArmy) == len(myArmy) + 1:
            inventoryHue -= 50
        elif len(myArmy) > len(enemyArmy) + 1:
            inventoryHue -= 50 * (len(myArmy) - len(enemyArmy))
        elif len(enemyArmy) > len(myArmy) + 1:
            inventoryHue += 50 * (len(enemyArmy) - len(myArmy))
        
        if len(myArmy) == 0 and len(enemyArmy) == 0:
            inventoryHue == 0
        elif len(myArmy) == 0:
            inventoryHue -= 250
        elif len(enemyArmy) == 0:
            inventoryHue += 250

        return inventoryHue


    ##
    #soldier_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -500 to 500
    def soldier_utility(self, myInv, enemyInv, currentState):
        soldierHue = 0

        myAntList = getAntList(currentState, myInv.player, (SOLDIER,DRONE,R_SOLDIER, QUEEN))
        enemyAntList = getAntList(currentState, enemyInv.player, (SOLDIER,DRONE,R_SOLDIER, QUEEN))

        mySoldiers = getAntList(currentState, myInv.player, (SOLDIER,))
        enemySoldiers = getAntList(currentState, enemyInv.player, (SOLDIER,))
        
        myWorkers = getAntList(currentState, myInv.player, (SOLDIER,))
        enemyWorkers = getAntList(currentState, enemyInv.player, (SOLDIER,))


        


        if len(enemyAntList) > 0:
            soldierHue -= len(enemyAntList)*5
            if len(mySoldiers) > 0:
                soldierHue += 50
            for soldier in mySoldiers:
                soldierHue += 50 - 5*approxDist(soldier.coords, enemyAntList[0].coords)

                for coord in listAdjacent(soldier.coords):
                    ant = getAntAt(currentState, coord)
                    if ant != None and ant.player == enemyInv.player and ant.health <= UNIT_STATS[SOLDIER][ATTACK]:
                        soldierHue += 100
                    elif ant != None and ant.player == enemyInv.player:
                        soldierHue += 25
        elif len(enemyWorkers) > 0:
            for soldier in mySoldiers:
                soldierHue += 100 - 10*approxDist(soldier.coords, enemyWorkers[0].coords)
        else:
            soldierHue += 125
            for soldier in mySoldiers:
                if soldier.coords == enemyInv.getAnthill().coords:
                    soliderHue += 125
        
        
        
        if len(myAntList) > 0:
            soldierHue += len(enemyAntList)*5
            if len(enemySoldiers) > 0:
                soldierHue -= 50
            for soldier in enemySoldiers:
                soldierHue -= 50 - 5*approxDist(soldier.coords, myAntList[0].coords)
                
                for coord in listAdjacent(soldier.coords):
                    ant = getAntAt(currentState, coord)
                    if ant != None and ant.player == myInv.player and ant.health <= UNIT_STATS[SOLDIER][ATTACK]:
                        soldierHue -= 100
                    elif ant != None and ant.player == myInv.player:
                        soldierHue -= 25
        elif len(myWorkers) > 0:
            for soldier in enemySoldiers:
                soldierHue += 100 - 10*approxDist(soldier.coords, myWorkers[0].coords)
        else:
            soldierHue -= 125
            for soldier in enemySoldiers:
                if soldier.coords == myInv.getAnthill().coords:
                    soliderHue -= 125

        return soldierHue


    ##
    #drone_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -500 to 500
    def drone_utility(self, myInv, enemyInv, currentState):
        droneHue = 0
        myWorkers = getAntList(currentState, myInv.player, (WORKER,))
        enemyWorkers = getAntList(currentState, enemyInv.player, (WORKER,))

        myDrones = getAntList(currentState, myInv.player, (DRONE,))
        enemyDrones = getAntList(currentState, enemyInv.player, (DRONE,))

        if enemyInv.foodCount >= 4 and len(myDrones) == 1 and len(enemyWorkers) > 0:
            droneHue += 100
        if myInv.foodCount >= 4 and len(enemyDrones) == 1 and len(myWorkers) > 0:
            droneHue -= 100

        if len(myDrones) > 1:
            droneHue -= 200
        if len(enemyDrones) > 1:
            droneHue += 200

        if len(enemyWorkers) == 0:
            droneHue += 150
            for drone in myDrones:
                droneHue += 50 - 5*approxDist(drone.coords, enemyInv.getQueen().coords)
                droneHue += 50 - 5*approxDist(drone.coords, enemyInv.getAnthill().coords)
                if drone.coords == enemyInv.getAnthill().coords:
                    droneHue += 125
        else:
            for drone in myDrones:
                if drone.coords in listAdjacent(enemyWorkers[0].coords):
                    droneHue += 125
                else:
                    droneHue += 125 - 10*approxDist(drone.coords, enemyWorkers[0].coords)
                    
        if len(myWorkers) == 0:
            droneHue -= 150   
            for drone in enemyDrones:
                droneHue -= 50 - 5*approxDist(drone.coords, myInv.getQueen().coords)
                droneHue -= 50 - 5*approxDist(drone.coords, myInv.getAnthill().coords)
                if drone.coords == myInv.getAnthill().coords:
                    droneHue -= 125
        else:
            for drone in enemyDrones:
                if drone.coords in listAdjacent(myWorkers[0].coords):
                    droneHue -= 125
                else:
                    droneHue -= 125 - 10*approxDist(drone.coords, myWorkers[0].coords)
        
        return droneHue

    ##
    #queen_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -500 to 500
    def queen_utility(self, myInv, enemyInv, currentState):
        queenHue = 0
        myQueen = myInv.getQueen()
        enemyQueen = enemyInv.getQueen()

        myArmy = getAntList(currentState, myInv.player, (SOLDIER,DRONE,R_SOLDIER))
        enemyArmy = getAntList(currentState, enemyInv.player, (SOLDIER,DRONE,R_SOLDIER))

        if myQueen.health > 4 and len(enemyArmy) > 0:
            queenHue += 25 - approxDist(myQueen.coords, enemyArmy[0].coords)
        
        for coord in listAdjacent(myQueen.coords):
            ant = getAntAt(currentState, coord)
            if ant != None and ant.player == enemyInv.player and ant.health <= UNIT_STATS[QUEEN][ATTACK]:
                queenHue -= 15
            elif ant != None and ant.player == enemyInv.player:
                queenHue += 25
              
        
        if enemyQueen.health > 4 and len(myArmy) > 0:
            queenHue -= 25 - approxDist(enemyQueen.coords, myArmy[0].coords)
        for coord in listAdjacent(enemyQueen.coords):
            ant = getAntAt(currentState, coord)
            if ant != None and ant.player == myInv.player and ant.health <= UNIT_STATS[QUEEN][ATTACK]:
                queenHue += 15
            elif ant != None and ant.player == myInv.player:
                queenHue -= 25
        
        return queenHue
            
    ##
    #ranged_utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #
    #Parameters:
    #   myInv - our inv
    #   enemyInv - enemy inv
    #   currentState - the current GameState object
    #   
    #Returns: number from -500 to 500
    def ranged_utility(self, myInv, enemyInv, currentState):
        rangedHue = 0
        
        myRangers = getAntList(currentState, myInv.player, (R_SOLDIER,))
        enemyRangers = getAntList(currentState, enemyInv.player, (R_SOLDIER,))

        # No ranged troops 
        if len(myRangers) > 0:
            rangedHue -= 100
        if len(enemyRangers) > 0:
            rangedHue += 100
        
        return rangedHue



        
    # Everything below is not used just referenced

    #utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #   Estimates # of moves to reach its goal from current state (copied from HW2)
    #
    #Parameters:
    #   currentState - The current GameState object
    #   
    #Returns: number of moves to get to the goal state
    def utility_(self, currentState):
        # Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        enemyInv = getEnemyInv(self, currentState)
        
        foodTurns = 0
        queenTurns = 0
        anthillTurns = 0

        ###### FOOD ######
        myWorkerList = getAntList(currentState, myInv.player, (WORKER,))
        myFood = getCurrPlayerFood(self, currentState)
        myFoodCount = myInv.foodCount
        numWorkers = len(myWorkerList)
        myAntHill = myInv.getAnthill()
        myTunnel = myInv.getTunnels()[0]

        enemyWorkerList = getAntList(currentState, enemyInv.player, (WORKER,))
        enemyFoodCount = enemyInv.foodCount
        numEnemyWorkers = len(enemyWorkerList)
        enemyAntHill = enemyInv.getAnthill()
        enemyTunnel = enemyInv.getTunnels()[0]

        # Catch error when starting game (the food doesn't exist yet)
        if len(myFood) == 0:
            return -1

        # Food win/loss
        if myFoodCount == FOOD_GOAL:
            return -math.inf
        elif enemyFoodCount == FOOD_GOAL:
            return math.inf
        
        foodTurns = (FOOD_GOAL - myFoodCount) * 5

        # If we have no workers, it's impossible to win off food
        if numWorkers == 0:
            foodTurns += 100
        elif numWorkers == 1:
            foodTurns -= 10
        else:
            foodTurns += 100

        # Impact based on enemy worker count
        if foodTurns != math.inf and numEnemyWorkers >= 1:
            foodTurns = foodTurns + math.ceil(foodTurns * numEnemyWorkers / 2)

        for worker in myWorkerList:
            if worker.coords[1] > 3:
                foodTurns += 1000
            if not worker.hasMoved:
                foodTurns += 10
            
            if worker.carrying:
                foodTurns -= 2
                distFromTunnel = stepsToReach(currentState, worker.coords, myTunnel.coords)
                distFromAnthill = stepsToReach(currentState, worker.coords, myAntHill.coords)
                bestDist = min(distFromAnthill, distFromTunnel)
                if bestDist == 0:
                    foodTurns -= 15
                else:
                    foodTurns -= 12 - bestDist
            else:
                distFromFoodOne = stepsToReach(currentState, worker.coords, myFood[0].coords)
                distFromFoodTwo = stepsToReach(currentState, worker.coords, myFood[1].coords)
                bestDist = min(distFromFoodOne, distFromFoodTwo)
                if bestDist == 0:
                    foodTurns -= 15
                else:
                    foodTurns -= 12 - bestDist 

            # Punish being near enemies
            for coord in listAdjacent(worker.coords):
                ant = getAntAt(currentState, coord)
                if ant and ant.player == PLAYER_TWO:
                    foodTurns += 2 * approxDist(worker.coords, ant.coords)

        ###### COMBAT / QUEEN ######
        myQueen = myInv.getQueen()
        enemyQueen = enemyInv.getQueen()
        if myQueen is None or enemyQueen is None:
            return -math.inf

        # --- NEGATED queen logic begins ---
        queenHealthDifference = -(enemyQueen.health - myQueen.health)
        queenTurns = -(10 * enemyQueen.health)  # flip
        if enemyQueen.health <= 0:
            return -math.inf
        # --- NEGATED queen logic ends ---

        ###### ANTHILL ######
        anthillHealthDifference = enemyAntHill.captureHealth - myAntHill.captureHealth
        anthillTurns = 30 * enemyAntHill.captureHealth

        attackAntList = getAntList(currentState, myInv.player, (QUEEN, SOLDIER, DRONE, R_SOLDIER))
        enemyAntList = getAntList(currentState, enemyInv.player, (SOLDIER, DRONE, R_SOLDIER, WORKER, QUEEN))

        combatScore = (len(enemyAntList) * 2 - len(attackAntList)) * 10
        for attackAnt in attackAntList:
            if attackAnt.hasMoved:
                combatScore -= 5
            else:
                combatScore += 5

            if attackAnt.coords[1] >= 5:
                combatScore -= 2

            closestEnemy = None
            closestWorker = None
            shortestDist = math.inf
            for enemy in enemyAntList:
                enemyDist = stepsToReach(currentState, enemy.coords, attackAnt.coords)
                if closestEnemy is None or enemyDist < shortestDist:
                    shortestDist = enemyDist
                    closestEnemy = enemy
                    if enemy.type == WORKER:
                        closestWorker = enemy

            if closestEnemy is None:
                break

            if attackAnt.type == QUEEN:
                # --- NEGATED queen scoring ---
                if attackAnt.health <= 4:
                    combatScore += shortestDist   # inverted sign
                elif closestEnemy.type != WORKER:
                    combatScore -= shortestDist   # inverted sign
                for coord in listReachableAdjacent(currentState, attackAnt.coords, UNIT_STATS[QUEEN][MOVEMENT]):
                    if getAntAt(currentState, coord) and getAntAt(currentState, coord).type == WORKER:
                        foodTurns += 3             # inverted sign
                # --- end negated block ---
            elif attackAnt.type == DRONE:
                if closestWorker is not None:
                    combatScore += approxDist(attackAnt.coords, closestWorker.coords)
                else:
                    combatScore += shortestDist
            elif attackAnt.type == R_SOLDIER:
                if UNIT_STATS[R_SOLDIER][RANGE] == shortestDist:
                    combatScore -= 1
                else:
                    combatScore += shortestDist
            elif attackAnt.type == SOLDIER:
                combatScore += shortestDist
            
            if enemyDist <= UNIT_STATS[enemy.type][MOVEMENT] and closestEnemy.type != WORKER:
                combatScore += 1

            if (attackAnt.type != R_SOLDIER and
                attackAnt.coords in listAdjacent(closestEnemy.coords) and
                UNIT_STATS[attackAnt.type][ATTACK] >= closestEnemy.health):
                combatScore -= 10

            if attackAnt.coords == enemyAntHill.coords:
                combatScore -= 10
            
            if approxDist(attackAnt.coords, enemyTunnel.coords) <= 3:
                combatScore -= 1

            if myAntHill.captureHealth == 1 and attackAnt.coords == myAntHill.coords:
                combatScore -= 5
            elif (attackAnt.coords == myTunnel.coords or
                attackAnt.coords == myFood[0].coords or attackAnt.coords == myFood[1].coords):
                combatScore += 10

        numDrones = len(getAntList(currentState, myInv.player, (DRONE,)))
        numSoldiers = len(getAntList(currentState, myInv.player, (SOLDIER,)))
        numR_Soldiers = len(getAntList(currentState, myInv.player, (R_SOLDIER,)))

        if (numDrones + numSoldiers + numR_Soldiers) == 0:
            combatScore += 200

        if numDrones == 1 and numEnemyWorkers == 1:
            combatScore -= 5
        elif numEnemyWorkers == 0:
            combatScore -= 20

        if (numSoldiers == 0 and len(enemyAntList) != (numEnemyWorkers + 1)):
            combatScore += 5
        else:
            combatScore -= 10

        if numR_Soldiers == 1 and (numSoldiers - 1) == len(enemyAntList):
            combatScore -= 3
        elif numSoldiers == len(enemyAntList):
            combatScore -= 2

        # --- NEGATED queen movement logic ---
        if myQueen:
            qx, qy = myQueen.coords
            dist = approxDist(myQueen.coords, myAntHill.coords)
            if dist == 0:
                combatScore -= 3000   # flipped sign
            elif 1 <= dist <= 3:
                combatScore += 50     # flipped sign
            else:
                combatScore -= 100    # flipped sign
        # --- end negated queen movement logic ---

        bestGuess = min(queenTurns, anthillTurns, foodTurns) + combatScore + math.floor(foodTurns / 4)
        return -bestGuess
