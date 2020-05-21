"""
UCT
c * sqrt((2 * ln(N(v))) / (N(v')))
where:
- v': current node
- v : parent node
- N : number of visit
- c : constant controlling exploitation and exploration

MCTS
1. selection
2. expand
3. random trajectories
4. backup
"""

import random
import time
import math
import json
from os.path import isfile, getsize

# hyperparameters
DEFAULT_TIME_LIMIT = 3
#DEFAULT_C = 1 / math.sqrt(2.0)  # suggested by Kocsis, Szepesvari
DEFAULT_C = 2
DEFAULT_MAX_ACTIONS = 1000
FILE_NAME = "stat.json"
MEMEORY_LIMIT = 20   #MB

class Stats():
    __slots__ = ('values', 'visits')

    def __init__(self, values = 0.0, visits = 0):
        self.values = values
        self.visits = visits

    def to_dict(self):
        return {'values':self.values, 'visits':self.visits}

    def load_dict(self, d):
        self.values = d["values"]
        self.visits = d["visits"]


class UCT(object):
    """
    Base class of MCTS classes.
    """

    def __init__(self, board, name, **kwargs):
        self.board = board
        self.name = name
        self.file_name = self.name + '_' + FILE_NAME
        self.C = kwargs.get('C', DEFAULT_C)
        self.time_limit = kwargs.get('time_limit', DEFAULT_TIME_LIMIT)
        self.max_actions = kwargs.get('max_actions', DEFAULT_MAX_ACTIONS)
        self.stats = {}
        self.history = []
        self.verbose = kwargs.get('verbose', True)
        self.max_depth = 0
        self.current_player = None

        self.load()


    def update(self, state, next_player):
        self.history.append(state)
        self.current_player = next_player

    
    def get_action(self):
        state = self.history[-1]

        # do not run when we can only perform one or no actions
        actions = self.board.get_possible_actions(state)
        if not actions:
            return None
        if len(actions) == 1:
            return actions[0]

        start_time = time.time()
        games = 0
        while time.time() - start_time < self.time_limit:
            self.simulate()
            games += 1

        # find the optimum action
        optimum_action = self.evaluate_actions(actions)[0]

        # log info
        if self.verbose:
            stat = self.stats[self.board.next_state(optimum_action)]
            print("finished %d simulations in %ss" %(games, round(time.time() - start_time, 2)))
            print("choosing action: %d (%d/%d)" %(optimum_action, stat.values, stat.visits))
            input("press enter to continue...")

        return optimum_action

    
    def evaluate_actions(self, actions):
        'returns the optimum action'
        actions_stats = [(a, self.stats[self.board.next_state(a, self.history[-1], player = self.current_player)]) for a in actions]
        return max(actions_stats, key = lambda x: (x[1].values / (x[1].visits or 1)))
    

    def simulate(self):
        
        # cache variables to optimize a little
        C, max_actions, stats = self.C, self.max_actions, self.stats
        # current state
        state = self.history[-1]

        visited_states = []
        reward = 0
        player = self.current_player

        expand = True
        for i in range(1, self.max_actions + 1):
            # state-action pairs
            actions = self.board.get_possible_actions(state)
            actions_states = [(a, self.board.next_state(a, state, player)) for a in actions]
            # if this state is not yet expanded
            if expand and not all(s[1] in stats for s in actions_states):
                # create stats for the possible states
                stats.update((S, Stats()) for a, S in actions_states if S not in stats)
                expand = False
                if i > self.max_depth:
                    self.max_depth = i
                
            # if this state has been explored more than once
            if expand:
                actions_states = [(a, S, stats[S]) for a, S in actions_states]
                # use UCT algorithm
                log_total = math.log(sum(st.visits for _, _, st in actions_states) or 1)
                # c * sqrt((2 * ln(N(v))) / (N(v')))
                value_actions = [
                    (a, S, (e.values / (e.visits or 1)) + C * math.sqrt(2 * log_total / (e.visits or 1)))
                    for a, S, e in actions_states
                ]
                max_value = max(v for _, _, v in value_actions)
                actions_states = [(a, S) for a, S ,v in value_actions if v == max_value]
            
            action, state = random.choice(actions_states)
            visited_states.append(state)

            if self.verbose:
                print("simulating actions:")
                self.board.display(state)
                time.sleep(0.25)

            reward = self.board.check_winning(action, state, self.current_player)

            if reward is not False:
                break

            # swap player
            player = self.board.next_player(player)

        # back propagation
        if self.verbose:
            print("game ends with a reward of %s." %reward)
            input("press enter to continue...")

        for state in visited_states:
            if state not in stats:
                continue
            stats[state].visits += 1
            stats[state].values += reward


    def save(self):
        with open(self.file_name, "w") as f:
            if not getsize(self.file_name) > MEMEORY_LIMIT * 1024 * 1024:
                d = {}
                for key, stat in self.stats.items():
                    d.update({key: stat.to_dict()})
                json.dump(d, f, indent = 2)
            else:
                print("WARNING: file size of %s exceeds memory limit, saving failed." %self.file_name)

    def load(self):
        if not isfile(self.file_name):
            return
        print("loading file %s" %self.file_name)
        with open(self.file_name, "r") as f:
            for state, stat in json.load(f).items():
                self.stats.update({state: Stats(stat["values"], stat["visits"])})
        print("loading complete.")



class UCT_ver1(UCT):
    """
    ## MCTS.UCT_ver1

    parameters:
    - board: the Board class in Connect4
    - (optional) C: exploratation constant
    - (optional) time_limit: the time limit for one step
    - (optional) max_actions: the maximum actions per step
    - (optional) verbose: whether to log info
    """

    def __init__(self, board, **kwargs):
        super().__init__(board, **kwargs)
