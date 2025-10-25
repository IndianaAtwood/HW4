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

# HW #2a - Informed Search Agent
# @authors - Malissa Chen, Hung Vu
# @date - 9/16/2025

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
        super(AIPlayer,self).__init__(inputPlayerId, "AwesomeAgent")

        # Variables for utility
        self.anthillBestDist = None
        self.tunnelBestDist = None
        self.bestRet = None
    
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
        # Part B start 

        # a.
        frontierNodes = []
        expandedNodes = []

        # b.
        rootNode = self.makeNode(None, currentState, 0, None) # root node is depth 0 and has no parent node
        frontierNodes.append(rootNode)

        # c.
        A_STAR_DEPTH = 3 # Can't change this (must search depth 3)
        for i in range(0, A_STAR_DEPTH):
            lowestNode = frontierNodes[0]
            for node in frontierNodes:
                if node["eval"] < lowestNode["eval"]:
                    lowestNode = node

            frontierNodes.remove(lowestNode)
            nodeList = self.expandNode(lowestNode)
            for node in nodeList:
                frontierNodes.append(node)
        # d.
        
        bestList = []
        lowestNode = frontierNodes[0]
        for node in frontierNodes:
            if node["eval"] < lowestNode["eval"]:
                lowestNode = node
                bestList.clear()
            if node["eval"] == lowestNode["eval"]:
                bestList.append(node)
        
        if len(bestList) > 0 :
            bestList.append(lowestNode)
            lowestNode = bestList[random.randint(0, len(bestList) - 1)]

        while(lowestNode["parent"]["parent"] != None):
            lowestNode = lowestNode["parent"]

        return lowestNode["move"]

        # Part B end

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
    #utility
    #Description: Looks at a GameState object and gives a 
    #   heuristic guess of good the game state is. 
    #   Estimates # of moves to reach its goal from current state 
    #
    #Parameters:
    #   currentState - The current GameState object
    #   
    #Returns: number of moves to get to the goal state
    def utility(self, currentState):
        # Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        enemyInv = getEnemyInv(self, currentState)
        
        # Get the three ways of winning, we want to return the method of
        # winning that will take the least ammount of moves

        foodTurns = 0
        queenTurns = 0
        anthillTurns = 0

        ######
        #FOOD#
        ######

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
        else: # Too many workers
            foodTurns += 100

        # Impact based on enemy worker
        if foodTurns != math.inf and numEnemyWorkers >= 1:
            foodTurns = foodTurns + math.ceil(foodTurns*numEnemyWorkers / 2)

        # Impact the turns based on if workers ants are carrying or not
        # Also impact based on how close they are to the food or tunnel/anthill based on that


        for worker in myWorkerList:
            # Workers should stay on our side
            if worker.coords[1] > 3:
                return math.inf
            if not worker.hasMoved:
                foodTurns += 10
            

            if worker.carrying:
                foodTurns -= 2
                distFromTunnel = stepsToReach(currentState, worker.coords, myTunnel.coords)
                distFromAnthill = stepsToReach(currentState, worker.coords, myAntHill.coords)
                if distFromAnthill < distFromTunnel:
                    bestDist = distFromAnthill
                    bestCoords = myAntHill.coords
                else:
                    bestDist = distFromTunnel
                    bestCoords = myTunnel.coords
                # Greater distance means more turns to take
                if bestDist == 0:
                    foodTurns -= 15
                elif bestDist == 1:
                    foodTurns -= 14
                elif bestDist == 2:
                    foodTurns -= 13
                elif (worker.coords == myFood[0].coords and 
                      myFood[0].coords in listReachableAdjacent(currentState, myFood[1].coords, UNIT_STATS[WORKER][MOVEMENT])):
                    foodTurns += 25 # Just go to the other food (too close it shouldn't matter)
                elif worker.coords == myFood[0].coords or worker.coords == myFood[1].coords:
                    foodTurns -= random.choice([-3, -2, 15])
                else:
                    foodTurns -= 12 - bestDist

            else:
                bestDist = math.inf
                distFromFoodOne = stepsToReach(currentState, worker.coords, myFood[0].coords)
                distFromFoodTwo = stepsToReach(currentState, worker.coords, myFood[1].coords)
                if distFromFoodTwo < distFromFoodOne:
                    bestDist = distFromFoodTwo
                    bestCoords = myFood[1].coords
                else:
                    bestDist = distFromFoodOne
                    bestCoords = myFood[0].coords

                # Greater distance means more turns to take
                if bestDist == 0:
                    foodTurns -= 15
                elif bestDist == 1:
                    foodTurns -= 14
                elif bestDist == 2:
                    foodTurns -= 13
                elif (worker.coords == myAntHill.coords and 
                      myAntHill.coords in listReachableAdjacent(currentState, myTunnel.coords, UNIT_STATS[WORKER][MOVEMENT])):
                    foodTurns += 25 # Just go to the other return src (too close it shouldn't matter)
                elif worker.coords == myAntHill.coords or worker.coords == myTunnel.coords:
                    foodTurns -= random.choice([-3, -2, 15])
                else:
                    foodTurns -= 12 - bestDist 

            # If they're close to enemies, punish that harshly
            adjacentToWorker = listAdjacent(worker.coords)
            for coord in adjacentToWorker:
                ant = getAntAt(currentState, coord)
                if ant != None and ant.player == PLAYER_TWO:
                    foodTurns += 2 * approxDist(worker.coords, ant.coords)
        
        ## Combat ##

        #######
        #QUEEN#
        #######

        myQueen = myInv.getQueen()
        enemyQueen = enemyInv.getQueen()

        if myQueen == None or enemyQueen == None: return -math.inf
        queenHealthDifference = enemyQueen.health - myQueen.health
        
        # For a queen win, estimate that it'll take 10 turns to reduce 1 health
        queenTurns = 10 * enemyQueen.health

        if enemyQueen.health <= 0:
            return -math.inf

        #########
        #ANTHILL#
        #########

        anthillHealthDifference = enemyAntHill.captureHealth - myAntHill.captureHealth

        # For a anthill win, estimate that it'll take 30 turns to reduce 1 health
        anthillTurns = 30 * enemyAntHill.captureHealth
        attackAntList = getAntList(currentState, myInv.player, (QUEEN, SOLDIER, DRONE, R_SOLDIER))
        enemyAntList = getAntList(currentState, enemyInv.player, (SOLDIER, DRONE, R_SOLDIER, WORKER, QUEEN))

        antTypeCount = [0,0,0,0,0] 

        combatScore = (len(enemyAntList)*2 - len(attackAntList))*10
        for attackAnt in attackAntList:
            if attackAnt.hasMoved:
                combatScore -= 5
            else:
                combatScore += 5

            # Good if our ants are towards the enemy
            if attackAnt.coords[1] >= 5:
                combatScore -= 2
            # Find the closest enemy and worker
            closestEnemy = None
            closestWorker = None
            shortestDist = math.inf
            for enemy in enemyAntList:
                enemyDist = stepsToReach(currentState, enemy.coords, attackAnt.coords)
                if closestEnemy == None or enemyDist < shortestDist:
                    shortestDist = enemyDist
                    closestEnemy = enemy
                    if enemy.type == WORKER:
                        closestWorker = enemy

            if closestEnemy == None:
                break
            # Unique combat for each ant type
            if attackAnt.type == QUEEN:
                if attackAnt.health <= 4:
                    # Run away when low
                    combatScore -= shortestDist
                elif closestEnemy.type != WORKER:
                    combatScore += shortestDist
                for coord in listReachableAdjacent(currentState, attackAnt.coords, UNIT_STATS[QUEEN][MOVEMENT]):
                    if getAntAt(currentState, coord) != None and getAntAt(currentState, coord).type == WORKER:
                        foodTurns -= 3
            elif attackAnt.type == DRONE: # get workers
                if closestWorker != None:
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
        
            # If we're within range the enemies next move, bad
            if enemyDist <= UNIT_STATS[enemy.type][MOVEMENT] and closestEnemy.type != WORKER:
                combatScore += 1

            # If we can kill the closest ant, good
            if (attackAnt.type != R_SOLDIER and
                attackAnt.coords in listAdjacent(closestEnemy.coords) and
                UNIT_STATS[attackAnt.type][ATTACK] >= closestEnemy.health):
                combatScore -= 10

            # If we;re on the enenmy anthill, good
            if attackAnt.coords == enemyAntHill.coords:
                combatScore -= 10
            
            if approxDist(attackAnt.coords, enemyTunnel.coords) <= 3:
                combatScore -= 1

            # Protect the anthill when hp low
            if myAntHill.captureHealth == 1 and attackAnt.coords == myAntHill.coords:
                combatScore -= 5
            # When it's not low we get off important structures
            elif (attackAnt.coords == myTunnel.coords or
                attackAnt.coords == myFood[0].coords or attackAnt.coords == myFood[1].coords):
                combatScore += 10

        numDrones = len(getAntList(currentState, myInv.player, (DRONE,)))
        numSoldiers = len(getAntList(currentState, myInv.player, (SOLDIER,)))
        numR_Soldiers = len(getAntList(currentState, myInv.player, (R_SOLDIER,)))

        # Should have at least one troop
        if (numDrones + numSoldiers + numR_Soldiers) == 0:
            combatScore += 200

        # Have a drone against a worker
        if numDrones == 1 and numEnemyWorkers == 1:
            combatScore -= 5
        elif numEnemyWorkers == 0:
            combatScore -= 20

        # Have at least a soldier when enemy has threats
        if (numSoldiers == 0 and len(enemyAntList) != (numEnemyWorkers + 1)):
            combatScore += 5
        else:
            combatScore -= 10

        # Having at least one range and soldiers match the enemy count is good, other equal soldiers is good
        if numR_Soldiers == 1 and (numSoldiers - 1) == len(enemyAntList):
            combatScore -= 3
        elif numSoldiers == len(enemyAntList):
            combatScore -= 2


        bestGuess = min(queenTurns, anthillTurns, foodTurns) + combatScore + math.floor(foodTurns/4)

        return bestGuess

    ##
    # makeNode
    # description: creates a search tree node
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
    # Description: finds the node with the best evaluation (utility)
    #
    # Parameters: 
    # nodeList - the list of nodes to search 
    #
    # Returns: our "node" representation
    def bestMove(self, nodeList):
        # Type checking
        if not isinstance(nodeList, list):
            return None

        # start with the first node as the best
        bestNode = nodeList[0]

        # List to track nodes that have equal evaluation to the best node
        bestList = []

        # go through each node in the list
        for node in nodeList:
            # if this node has a smaller eval score than our current best
            if node["eval"] < bestNode["eval"]:
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
    # Description: takes an existing node and return a list of nodes 
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
            nextState = getNextState(initState, m)
            # these nodes are +1 depth from initial, and their parent is always the initNode
            node = self.makeNode(m, nextState, (initDepth + 1), initNode) 
            nodes.append(node)

        return nodes
    
    ##
    # 
    # incHueristic
    # Description: increases the value of hueristic value given the hueristic and an integer
    #
    #
    def incHueristic(self, hue, val):
        if val == 0:
            return hue
        return (hue +  (val * 0.001)) / (1 + (val * 0.001))

    ##
    # 
    # decHueristic
    # Description: decreases the value of hueristic value given the hueristic and an integer
    #
    #
    def decHueristic(self, hue, val):
        return hue / (1 + (val * 0.001))

# Unit testing
def test_utility():
    player = AIPlayer(0)
    
    # create minimal dummy objects
    class DummyAnt:
        def __init__(self, ant_type, health=10):
            self.type = ant_type
            self.health = health
            self.coords = (0, 0)
            self.carrying = False
            self.hasMoved = False

    class DummyConstruction:
        def __init__(self, constr_type):
            self.type = constr_type
            self.captureHealth = 3
            self.coords = (0, 0)

    class DummyFood:
        def __init__(self, coords):
            self.coords = coords

    class DummyInventory:
        def __init__(self, player_id, foodCount=5):
            self.player = player_id
            self.foodCount = foodCount
            
        def getQueen(self):
            return DummyAnt(QUEEN, 10)
            
        def getAnthill(self):
            return DummyConstruction(ANTHILL)
        
        def getTunnels(self):
            return [DummyConstruction(TUNNEL)]

    class DummyState:
        def __init__(self):
            self.inventories = [DummyInventory(0), DummyInventory(1)]
            self.whoseTurn = 0

    # dummy the required functions
    import sys
    current_module = sys.modules[__name__]
    
    def dummy_getCurrPlayerInventory(state):
        return state.inventories[0]
    
    def dummy_getEnemyInv(player, state):
        return state.inventories[1]
        
    def dummy_getAntList(state, player, types):
        return []
        
    def dummy_getConstrList(state, player, types):
        return [DummyConstruction(types[0])] if types else []
    
    def dummy_getCurrPlayerFood(player, state):
        return [DummyFood((0,1)), DummyFood((1,1))]

    # store originals and set dummies
    originals = {}
    for func in ['getCurrPlayerInventory', 'getEnemyInv', 'getAntList', 'getConstrList']:
        originals[func] = getattr(current_module, func, None)
        
    setattr(current_module, 'getCurrPlayerInventory', dummy_getCurrPlayerInventory)
    setattr(current_module, 'getEnemyInv', dummy_getEnemyInv)
    setattr(current_module, 'getAntList', dummy_getAntList)
    setattr(current_module, 'getConstrList', dummy_getConstrList)
    setattr(current_module, 'getCurrPlayerFood', dummy_getCurrPlayerFood)

    try:
        state = DummyState()
        value = player.utility(state)
        if not isinstance(value, (int, float)):
            print(f"utility test failed: utility did not return number: {value}")
    except Exception as e:
        print(f"utility test failed: {e}")
    finally:
        # restore originals
        for func, original in originals.items():
            if original:
                setattr(current_module, func, original)
def test_getMove():
    player = AIPlayer(0)

    # test that the method exists
    if not hasattr(player, 'getMove'):
        print("getMove test failed: getMove method does not exist")
        return
    if not callable(getattr(player, 'getMove')):
        print("getMove test failed: getMove is not callable")
        return

def test_bestMove():
    player = AIPlayer(0)

    nodes = [
        {"move": "A", "state": None, "depth": 1, "eval": 0.3, "parent": None},
        {"move": "B", "state": None, "depth": 1, "eval": 0.9, "parent": None},
        {"move": "C", "state": None, "depth": 1, "eval": 0.7, "parent": None},
    ]

    best = player.bestMove(nodes)
    assert best["move"] == "A", f"bestMove failed: got {best['move']}"

if __name__ == "__main__":
    test_utility()
    test_getMove()
    test_bestMove()
    