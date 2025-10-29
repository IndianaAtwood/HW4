import random, os, json, math, sys
sys.path.append("..")

from Player import *
from Constants import *
from GameState import *
from AIPlayerUtils import *
from Move import Move
from Ant import UNIT_STATS

POP_FILE = "./tabra26_atwoodi26_population.txt"  # required relative path

class AIPlayer(Player):
    def __init__(self, playerId):
        super(AIPlayer, self).__init__(playerId, "GA_MiniMax_Tabra_Atwood")

        # Genetic algorithm parameters
        self.pop_size = 12
        self.games_per_gene = 4
        self.population = []
        self.fitnesses = []
        self.eval_counts = []
        self.current_gene_index = 0
        self.generation = 0
        self.mutation_rate = 0.1
        self.mutation_magnitude = 1.0
        self.depth = 2  # shallow minimax for speed
        self.whichPlayer = None

        # Generate population from file (if exists)
        self.load_or_init_population()

    # -------------------------------------------------------------
    # === GA Management ===
    # -------------------------------------------------------------
    def load_or_init_population(self):

        #load an existing population or make one
        if os.path.exists(POP_FILE):
            try:
                with open(POP_FILE, "r") as f:
                    data = json.load(f)
                self.population = data["population"]
                self.generation = data["generation"]

                print(f"generation loaded: {self.generation}")

            # If error, create a new population with random weights
            except Exception as e:
                print("pop not loaded: ", e)
                self.init_random_population()
        else:
            # Initiate random population
            self.init_random_population()

        # Initial vals set
        self.fitnesses = [0.0 for _ in self.population]
        self.eval_counts = [0 for _ in self.population]
        self.current_gene_index = 0

    # Generate random weights for initial run
    def init_random_population(self):

        #create random pop of genomes
        num_features = 12
        self.population = [
            [random.uniform(-10.0, 10.0) for _ in range(num_features)]
            for _ in range(self.pop_size)
        ]
        self.generation = 0
        print("new random pop made")

    # When generation is done, it is saved to the file
    def save_population(self):
        #write to popfile
        with open(POP_FILE, "w") as file:
            json.dump(
                {"generation": self.generation, "population": self.population}, file
            )

    # Crosses the genes for variation
    def crossover(self, p1, p2):
        
        # Perform uniform crossover
        c1 = [(a if random.random() < 0.5 else b) for a, b in zip(p1, p2)]
        c2 = [(b if random.random() < 0.5 else a) for a, b in zip(p1, p2)]
        return c1, c2

    # Mutation of the genes for GA (using mutuation rate)
    def mutate(self, gene):

        # Small random perturbations happen
        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                gene[i] += random.uniform(-self.mutation_magnitude, self.mutation_magnitude)
                gene[i] = max(-10.0, min(10.0, gene[i]))

        return gene

    # Ranks most effective genes, mutates new offspring
    #   and begins a new generation
    def next_generation(self):

        # Rank by fitness
        ranked = list(zip(self.population, self.fitnesses))
        ranked.sort(key=lambda x: x[1], reverse=True)

        # Parents selected
        top_half = [g for g, _ in ranked[: len(ranked)//2]]

        # Breed new offspring in while
        new_pop = []

        while len(new_pop) < self.pop_size:
            p1, p2 = random.sample(top_half, 2)
            c1, c2 = self.crossover(p1, p2)
            self.mutate(c1)
            self.mutate(c2)
            new_pop.extend([c1, c2])

        # Reset, advance generation counter
        self.population = new_pop[:self.pop_size]
        self.fitnesses = [0.0 for _ in self.population]
        self.eval_counts = [0 for _ in self.population]
        self.current_gene_index = 0
        self.generation += 1

        # Save generation
        self.save_population()
        print(f"[GA] === New Generation {self.generation} created ===")

    # Important game features for feeding into the GA
    def extract_features(self, state):

        # All features extracted below
        myInv = getCurrPlayerInventory(state)
        enemyInv = getEnemyInv(self, state)

        # 1. Food difference
        food_diff = (myInv.foodCount - enemyInv.foodCount) / 11.0

        # 2. Queen HP difference
        myQ, enQ = myInv.getQueen(), enemyInv.getQueen()
        queen_health_diff = 0
        if myQ and enQ:
            queen_health_diff = (myQ.health - enQ.health) / 10.0

        # 3–6. Count differences
        worker_diff = len(getAntList(state, myInv.player, (WORKER,))) - len(getAntList(state, enemyInv.player, (WORKER,)))
        drone_diff = len(getAntList(state, myInv.player, (DRONE,))) - len(getAntList(state, enemyInv.player, (DRONE,)))
        soldier_diff = len(getAntList(state, myInv.player, (SOLDIER,))) - len(getAntList(state, enemyInv.player, (SOLDIER,)))
        ranged_diff = len(getAntList(state, myInv.player, (R_SOLDIER,))) - len(getAntList(state, enemyInv.player, (R_SOLDIER,)))

        # 7. Offensive proximity (close to enemy queen/hill)
        my_off = getAntList(state, myInv.player, (SOLDIER, DRONE, R_SOLDIER))
        enQ, enH = enemyInv.getQueen(), enemyInv.getAnthill()
        offense_prox = 0
        if my_off and enQ and enH:
            prox = [10 - min(approxDist(a.coords, enQ.coords), approxDist(a.coords, enH.coords)) for a in my_off]
            offense_prox = sum(prox) / (10 * len(prox))

        # 8. Defense threat (enemy attackers near my queen/hill)
        enemy_off = getAntList(state, enemyInv.player, (SOLDIER, DRONE, R_SOLDIER))
        myQ, myH = myInv.getQueen(), myInv.getAnthill()
        defense_threat = 0
        if enemy_off and myQ and myH:
            prox = [10 - min(approxDist(a.coords, myQ.coords), approxDist(a.coords, myH.coords)) for a in enemy_off]
            defense_threat = sum(prox) / (10 * len(prox))

        # 9. Army strength ratio
        def army_power(inv):
            army = getAntList(state, inv.player, (SOLDIER, DRONE, R_SOLDIER))
            hp = sum(a.health for a in army)
            atk = sum(UNIT_STATS[a.type][ATTACK] for a in army)
            return hp + atk
        my_power = army_power(myInv)
        en_power = army_power(enemyInv)
        army_ratio = my_power / (en_power + 1.0)

        # 10. Queen safety (friendly nearby)
        queen_safety = 0
        if myQ:
            adj = listAdjacent(myQ.coords)
            allies = sum(1 for c in adj if getAntAt(state, c) and getAntAt(state, c).player == myInv.player)
            queen_safety = allies / 6.0

        # 11. Irrelevant: queen distance
        queen_distance = 0
        if myQ and enQ:
            queen_distance = approxDist(myQ.coords, enQ.coords) / 14.0

        # 12. Irrelevant: avg worker→queen distance
        workers = getAntList(state, myInv.player, (WORKER,))
        worker_to_queen = 0
        if myQ and workers:
            dists = [approxDist(a.coords, myQ.coords) for a in workers]
            worker_to_queen = sum(dists) / (10 * len(dists))

        return [
            food_diff, queen_health_diff, worker_diff, drone_diff,
            soldier_diff, ranged_diff, offense_prox, defense_threat,
            army_ratio, queen_safety, queen_distance, worker_to_queen
        ]

    # Determines the most effective state (using extract_features function)
    def utility(self, state):
        #new utility made by weighted linear combination
        gene = self.population[self.current_gene_index]
        feats = self.extract_features(state)
        return sum(w * f for w, f in zip(gene, feats))

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

    def getMove(self, state):

        if self.whichPlayer is None:
            self.whichPlayer = getCurrPlayerInventory(state).player

        children = self.expandNode(state)
        if not children:
            return Move(END, None, None)

        best_val = -math.inf
        best_move = None
        for move, nextState in children:
            val = self.minimax(nextState, self.depth-1, -math.inf, math.inf, True)
            if val > best_val:
                best_val = val
                best_move = move

        return best_move if best_move else Move(END, None, None)

    def expandNode(self, state):
        #lost of move, nextstate
        result = []
        for m in listAllLegalMoves(state):
            ns = getNextStateAdversarial(state, m)
            result.append((m, ns))
        return result

    # MiniMax function for finding successful states
    def minimax(self, state, depth, alpha, beta, maximizing):
        #recursive minimax using new utility
        if depth == 0 or getWinner(state) is not None:
            return self.utility(state)

        if maximizing:
            val = -math.inf
            for move, ns in self.expandNode(state):
                val = max(val, self.minimax(ns, depth-1, alpha, beta, False))
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return val
        else:
            val = math.inf
            for move, ns in self.expandNode(state):
                val = min(val, self.minimax(ns, depth-1, alpha, beta, True))
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return val

    def getAttack(self, state, attackingAnt, enemyLocs):
        return random.choice(enemyLocs)

    # Update generation's eval, and gene index,
    #   generation and fitness (if won)
    def registerWin(self, hasWon):

        #update stats when game ends
        i = self.current_gene_index
        self.eval_counts[i] += 1
        if hasWon:
            self.fitnesses[i] += 1

        # Move to next gene if done evaluating
        if self.eval_counts[i] >= self.games_per_gene:
            self.current_gene_index += 1

        # All genes evaluated, then evolve
        if self.current_gene_index >= len(self.population):
            self.next_generation()
