import random, os, json, math, sys
sys.path.append("..")

from Player import *
from Constants import *
from GameState import *
from AIPlayerUtils import *
from Move import Move
from Ant import UNIT_STATS

POP_FILE = "C:/Users/india/Desktop/AI/HW4/indiana_population.txt"  # required relative path


class AIPlayer(Player):

    def __init__(self, playerId):
        super(AIPlayer, self).__init__(playerId, "GA_MiniMax_Tabra")

        # genetic algo params
        self.pop_size = 12
        self.games_per_gene = 4
        self.population = []
        self.fitnesses = []
        self.eval_counts = []
        self.current_gene_index = 0
        self.generation = 0
        self.mutation_rate = 0.1
        self.mutation_magnitude = 2.0
        self.depth = 2  # shallow minimax for speed
        self.whichPlayer = None

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

            except Exception as e:

                print("pop not loaded: ", e)
                self.init_random_population()
        else:
            #initiate random pop
            self.init_random_population()

        #initial vals set
        self.fitnesses = [0.0 for _ in self.population]
        self.eval_counts = [0 for _ in self.population]
        self.current_gene_index = 0

    def init_random_population(self):
        #create random pop of genomes
        num_features = 12
        self.population = [
            [random.uniform(-10.0, 10.0) for _ in range(num_features)]
            for _ in range(self.pop_size)
        ]
        self.generation = 0
        print("new random pop made")

    def save_population(self):
        #write to popfile
        with open(POP_FILE, "w") as f:
            json.dump(
                {"generation": self.generation, "population": self.population}, f
            )

    def crossover(self, p1, p2):
        #perform uniform crossover

        c1 = [(a if random.random() < 0.5 else b) for a, b in zip(p1, p2)]
        c2 = [(b if random.random() < 0.5 else a) for a, b in zip(p1, p2)]
        return c1, c2

    def mutate(self, gene):
        #small random perturbations happen

        for i in range(len(gene)):
            if random.random() < self.mutation_rate:
                gene[i] += random.uniform(-self.mutation_magnitude, self.mutation_magnitude)
                gene[i] = max(-10.0, min(10.0, gene[i]))

        return gene

    def next_generation(self):
        #breed for top performers next gen:

        #rank by fitness
        ranked = list(zip(self.population, self.fitnesses))
        ranked.sort(key=lambda x: x[1], reverse=True)

        #parents selected
        top_half = [g for g, _ in ranked[: len(ranked)//2]]

        #breed new offspring in while
        new_pop = []

        while len(new_pop) < self.pop_size:
            p1, p2 = random.sample(top_half, 2)
            c1, c2 = self.crossover(p1, p2)
            self.mutate(c1)
            self.mutate(c2)
            new_pop.extend([c1, c2])

        #reset, advance generation counter
        self.population = new_pop[:self.pop_size]
        self.fitnesses = [0.0 for _ in self.population]
        self.eval_counts = [0 for _ in self.population]
        self.current_gene_index = 0
        self.generation += 1

        #save generation
        self.save_population()
        print(f"[GA] === New Generation {self.generation} created ===")


    def extract_features(self, state):
        myInv = getCurrPlayerInventory(state)
        enemyInv = getEnemyInv(self, state)

        myQ, enQ = myInv.getQueen(), enemyInv.getQueen()
        # safe tunnel access
        tunnels = myInv.getTunnels()
        myT = tunnels[0] if tunnels else None

        # find food (neutral)
        foodList = getConstrList(state, None, (FOOD,))
        food = foodList[0] if foodList else None

        # 1. Food difference (important)
        food_diff = (myInv.foodCount - enemyInv.foodCount) / 11.0

        # workers list
        workers = getAntList(state, myInv.player, (WORKER,))

        # 2. Worker progress (not carrying -> move toward food) (important)
        worker_to_food = 0.0
        if workers and food:
            vals = []
            for w in workers:
                if not getattr(w, "carrying", False):
                    d = approxDist(w.coords, food.coords)
                    vals.append(max(0.0, 1.0 - d / 10.0))
            if vals:
                worker_to_food = sum(vals) / len(vals)

        # 3. Worker progress (carrying -> move toward tunnel/anthill) (important)
        worker_to_tunnel = 0.0
        if workers and myT:
            vals = []
            for w in workers:
                if getattr(w, "carrying", False):
                    d = approxDist(w.coords, myT.coords)
                    vals.append(max(0.0, 1.0 - d / 10.0))
            if vals:
                worker_to_tunnel = sum(vals) / len(vals)

        # 4. Worker count normalized (important) — ideal <= 2, normalized so ~1 = 2 workers
        worker_count = min(len(workers), 4) / 2.0

        # 5. Soldier count normalized (important) — encourage at least one
        soldiers = getAntList(state, myInv.player, (SOLDIER,))
        soldier_count = min(len(soldiers), 4) / 2.0

        # 6-7. Simple count diffs (important)
        drone_diff = len(getAntList(state, myInv.player, (DRONE,))) - len(getAntList(state, enemyInv.player, (DRONE,)))
        soldier_diff = len(getAntList(state, myInv.player, (SOLDIER,))) - len(getAntList(state, enemyInv.player, (SOLDIER,)))

        # 8. Soldier proximity to enemy queen (important)
        soldier_proximity = 0.0
        if soldiers and enQ:
            dists = [approxDist(s.coords, enQ.coords) for s in soldiers]
            soldier_proximity = max(0.0, 1.0 - (sum(dists) / (10.0 * len(dists))))

        # 9. Enemy threat near my queen (important)
        enemy_off = getAntList(state, enemyInv.player, (SOLDIER, DRONE, R_SOLDIER))
        enemy_threat = 0.0
        if myQ and enemy_off:
            dists = [approxDist(a.coords, myQ.coords) for a in enemy_off]
            nearby = [d for d in dists if d <= 2]
            enemy_threat = len(nearby) / (len(enemy_off) + 1.0)

        # 10. Army ratio (important)
        def power(inv):
            ants = getAntList(state, inv.player, (SOLDIER, DRONE, R_SOLDIER))
            atk = sum(UNIT_STATS[a.type][ATTACK] for a in ants)
            hp = sum(a.health for a in ants)
            return atk + hp
        army_ratio = power(myInv) / (power(enemyInv) + 1.0)

        # 11. Irrelevant filler: queen_distance (irrelevant)
        queen_distance = 0.0
        if myQ and enQ:
            queen_distance = approxDist(myQ.coords, enQ.coords) / 14.0

        # 12. Irrelevant filler: avg worker->queen distance (also irrelevant)
        worker_to_queen = 0.0
        if workers and myQ:
            dists = [approxDist(w.coords, myQ.coords) for w in workers]
            worker_to_queen = (sum(dists) / (10.0 * len(dists)))

        return [
            food_diff, worker_to_food, worker_to_tunnel, worker_count, soldier_count,
            drone_diff, soldier_diff, soldier_proximity, enemy_threat, army_ratio,
            queen_distance, worker_to_queen
        ]


    def utility(self, state):
        gene = [float(w) for w in self.population[self.current_gene_index]]
        feats = self.extract_features(state)
        score = sum(w * f for w, f in zip(gene, feats))

        return score
    
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

    def registerWin(self, hasWon):
        #update stats when game ends
        i = self.current_gene_index
        self.eval_counts[i] += 1
        if hasWon:
            self.fitnesses[i] += 1

        # Move to next gene if done evaluating
        if self.eval_counts[i] >= self.games_per_gene:
            self.current_gene_index += 1

        # All genes evaluated → evolve
        if self.current_gene_index >= len(self.population):
            self.next_generation()
