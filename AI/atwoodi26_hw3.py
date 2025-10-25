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
import pdb
import math

# HW #3 - MiniMax
# @authors - Malissa Chen, Indiana Atwood
# @date - 10/7/2025

########################
###   MINIMAX FUNCTIONS
########################

def enemyWon(state):
    me = state.whoseTurn
    enemyInventory = getEnemyInv(not me, state)
    
    # Game over if a Queen dies or no legal moves
    if enemyInventory.getQueen() is None or enemyInventory.getQueen().health <= 0:
        return True
    # Game over if enemy gains 11 food
    elif enemyInventory.foodCount == 11:
        return True
    else:
        return False

# minimax function (used help for design with ChatGPT)
def minimax_ab(state, depth, alpha, beta, myPlayerId, maxMoves):
    # base case, if depth exceeds 3 or the enemy won
    if depth >= 3 or enemyWon(state):
        val = utility(state, myPlayerId)
        return val, None

    legal_moves = listAllLegalMoves(state)

    # Move ordering, restricts to 12 most effective nodes (for computational time)
    #   efficiency determined by worker ants moving closer to their goal (moves away are discarded)
    def move_heuristic(move):
        nextState = getNextStateAdversarial(state, move)
        myInv = getCurrPlayerInventory(nextState)
        workers = getAntList(nextState, myInv.player, (WORKER,))
        score = 0
        for worker in workers:
            if worker.carrying:
                tunnel = getConstrList(nextState, myInv.player, (TUNNEL,))[0]
                score -= abs(worker.coords[0] - tunnel.coords[0]) + abs(worker.coords[1] - tunnel.coords[1])
            else:
                food = getConstrList(nextState, None, (FOOD,))[0]
                score -= abs(worker.coords[0] - food.coords[0]) + abs(worker.coords[1] - food.coords[1])
        return score

    # Technique learned from the internet to find critical nodes
    legal_moves.sort(key=move_heuristic)
    legal_moves = legal_moves[:maxMoves]

    # minimax algorithm found online, finds the most effective future state (maxDepth = 3)
    bestMove = None
    maximizingPlayer = (state.whoseTurn == myPlayerId)

    if maximizingPlayer:
        maxEval = -math.inf
        for move in legal_moves:
            nextState = getNextStateAdversarial(state, move)
            eval, _ = minimax_ab(nextState, depth+1, alpha, beta, myPlayerId, maxMoves)
            if eval > maxEval:
                maxEval = eval
                bestMove = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return maxEval, bestMove
    else:
        minEval = math.inf
        for move in legal_moves:
            nextState = getNextStateAdversarial(state, move)
            eval, _ = minimax_ab(nextState, depth+1, alpha, beta, myPlayerId, maxMoves)
            if eval < minEval:
                minEval = eval
                bestMove = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return minEval, bestMove
    
# Determines the distance between selected Ant and its target
def getDistance(antID, target, inventory):
    antX, antY = None, None
    for ant in inventory.ants:
        if ant.UniqueID == antID:
            antX, antY = ant.coords
            break

    # Error handling
    if antX is None or antY is None:
        return 100  

    if target is None:
        return 100  

    targetX, targetY = target.coords
    return abs(antX - targetX) + abs(antY - targetY)

#######################
###   UTILITY FUNCTION
#######################

def utility(state, myPlayerId):
    my_inv = state.inventories[myPlayerId]
    enemy_inv = state.inventories[not myPlayerId]

    score = 0.0

    # Heavily reward food collection
    score += my_inv.foodCount * 100

    my_workers = getAntList(state, myPlayerId, (WORKER,))
    tunnels = getConstrList(state, myPlayerId, (TUNNEL,))
    anthill = getConstrList(state, myPlayerId, (ANTHILL,))
    foods = getConstrList(state, None, (FOOD,))   

    targets = tunnels + anthill

    # Bonus for workers carrying food on their way back
    #   used ChatGPT to find a more efficient method of computation (see the "c in targets" line)
    my_workers = getAntList(state, myPlayerId, (WORKER,))
    for worker in my_workers:
        if worker.carrying:
            if targets:
                dist_home = min(abs(worker.coords[0] - t.coords[0]) +
                                abs(worker.coords[1] - t.coords[1]) for t in targets)
                score += max(0, 30 - dist_home * 3)
            score += 25  # reward for carrying
        else:
            # not carrying, go to food
            if foods:
                dist_food = min(abs(worker.coords[0] - f.coords[0]) +
                                abs(worker.coords[1] - f.coords[1]) for f in foods)
                score += 20 - dist_food * 2

    # Only want two workers at a time
    num_workers = len(my_workers)
    if num_workers == 2:
        score += 100
    else:
        score -= -1000 

    # Enemy ants
    enemy_workers = getAntList(state, not myPlayerId, (WORKER,))
    enemy_queen = enemy_inv.getQueen()
    enemy_anthill = getConstrList(state, not myPlayerId, (ANTHILL,))
    enemy_drones = getConstrList(state, not myPlayerId, (DRONE,))
   
    # Reward if enemy workers are fewer (means we likely killed one)
    num_enemy_workers = len(enemy_workers)
    score += (2 - num_enemy_workers) * 75

    # Reward if enemy queen is damaged or dead
    if enemy_queen is None:
        score += 1000
    else:
        score += (10 - enemy_queen.health) * 30

    # Reward if enemy drone is dead
    num_enemy_combat = len(enemy_drones)
    score += (3 - num_enemy_combat) * 40  # reward if we've killed their military


    # Reward if anthill is damaged
    if enemy_anthill:
        anthill = enemy_anthill[0]
        score += (3 - anthill.captureHealth) * 50  # capture progress gives points

    # same as workers, we only want two soldiers (reward instead of penalize)
    my_soldiers = getAntList(state, myPlayerId, (SOLDIER,))
    if my_soldiers:
        score += 200
    if len(my_soldiers) == 2:
        score += 1000

    # if there are no workers, target the Queen (so their food gathering stops)
    if enemy_workers:
        target = enemy_workers[0]
    else:
        target = enemy_queen

    # move soldiers to the predefined target
    for ant in my_soldiers:
        dist = getDistance(ant.UniqueID, target, my_inv)
        # Closer is better, capped at some max reward
        score += 25 - dist * 2

    # ####################
    # ENEMY SUPPRESSION
    # Reduces the heuristic score based on enemy actions
    # (ChatGPT suggestion)
    # ####################
    # Penalize enemy food collection
    score -= enemy_inv.foodCount * 150

    # Penalize enemy offensive presence
    enemy_offensive = getAntList(state, not myPlayerId, (SOLDIER, DRONE, R_SOLDIER))
    score -= len(enemy_offensive) * 10

    return score

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
        super(AIPlayer,self).__init__(inputPlayerId, "Testing")
    
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
        # Restricts searched nodes to 12 states that show ants are moving toward goals
        maxMoves = 12
        moves = listAllLegalMoves(currentState)
        if not moves:
            return Move((0,0), END)

        _, move = minimax_ab(currentState, 0, -math.inf, math.inf, self.playerId, maxMoves)

        if move is None:
            return moves[random.randint(0, len(moves)-1)]
        
        return move
    
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
