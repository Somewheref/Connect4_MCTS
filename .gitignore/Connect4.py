"""
Connect 4 (ai version)

Date: 2019.11.11

Summary:
asking user to input the row number,
than refresh the board and display the move.
taking O and X for the two checkers for players
"""


from os import system
from time import sleep
from sys import exit
from MCTS import UCT_ver1
from copy import deepcopy

# hyperparameters
WINNING_REWARD = 1
TIE_REWARD = 0
LOSING_REWARD = 0
VERBOSE = False


horizontal = 7
vertical = 6

# actual number of spaces when displaying
horizontal_length = 6 * horizontal + 1

player1 = 'O'
player2 = 'X'

current_player = player1

# directions to search when determine whether player wins
serach_directions = [[[1,0]],             # down
                     [[0,-1],[0,1]],    # left and right
                     [[1,-1],[-1,1]],   # left-down to right-up
                     [[-1,-1],[1,1]]]     # left-up to right-down

title = ' CONNECT 4 '

welcome_message = """
welcome to the CONNECT 4 designed by Stanly!

when playing, input the row number to drop the checker from top. (starting from 1)
also, you can type 'exit' and press enter to exit the game.

have fun playing!

[press enter to continue...]
"""


class Board():

    def __init__(self, start_player):
        self.board = []
        self.init_board()
        self.current_player = start_player

    
    def init_board(self):
        self.board = []
        for i in range(vertical):
            self.board.append([])
            for j in range(horizontal):
                self.board[i].append(0)      # setting all to zeros


    def display(self, board = None):
        'print the board, including clearing the screen, the title, grids and checkers'
        # clear the screen (Linux command, use 'cls' on windows)
        system('clear')

        if board is None:
            board = self.board
        elif type(board) == str:
            board = self.unpack_state(board)

        # print title
        print('-'*horizontal_length)
        print('{:*^43s}'.format(title))
        print('-'*horizontal_length)

        # print board
        for line in range(vertical):
            # print the grid along with the board
            for checker in board[line]:
                print('|',end=' ')
                if checker:         # if a checker is placed at that position
                    print('',checker,end='  ')
                else:               # else we just put a space (if it is 0)
                    print('  ',end='  ')
            print('|')
            
            # print the line of seperation below
            print('-'*horizontal_length)
        
        # the bottom axis
        print('',end='|')
        for i in range(1,horizontal+1):
            print('  %s  |' %i,end='')
        print()
        print('-'*horizontal_length)


    def drop_checker(self,row):
        'drop a checker on a row given a line, return the position if success or false otherwise'
        if row == 'exit':
            exit(0)
        try:
            row = int(row) - 1
            if row < 0:
                raise IndexError
            for line in range(vertical-1,-1,-1):
                # from bottom to top
                if self.board[line][row]:    # continue if this grid is occupied
                    continue
                else:                   # finds an empty grid
                    # set the player's checker
                    self.board[line][row] = self.current_player
                    # swap player
                    self.current_player = self.next_player()
                    return line,row
            # if all grids on the row has been occupied
            print('this row is full!')
            return False, False
        
        except ValueError:
            # the input is invalid
            print('invalid input!')
            return False, False

        except IndexError:
            # if player inputs a value out of range
            print('input out of boundary!')
            return False,False


    def get_possible_actions(self, state):
        # unpack state if it is a string
        if type(state) == str:
            state = self.unpack_state(state)
        possible_actions = []
        for i, cell in enumerate(state[0]):
            if not cell:
                possible_actions.append(i + 1)
        return possible_actions

    
    def next_state(self, action, board = None, player = None):
        action -= 1

        if board is None:
            board = deepcopy(self.board)
        elif type(board) == str:
            board = self.unpack_state(board)

        if player is None:
            player = self.current_player

        for line in range(vertical-1,-1,-1):
            # from bottom to top
            if board[line][action]:    # continue if this grid is occupied
                continue
            else:                   # finds an empty grid
                # copy the board
                board[line][action] = player
                return self.get_compact_state(board)


    def get_compact_state(self, board):
        'convert a list to compact string'
        string = ''
        for line in board:
            for char in line:
                string += str(char)
            string += '|'
        return string[:-1]

    
    def unpack_state(self, board):
        new_board = board.split('|')
        for i, line in enumerate(new_board):
            new_board[i] = [0 if x == "0" else x for x in line]
        return new_board


    def check_winning(self, pos, board = None, player = None):
        """check if game ends. return 0 if draw, +reward if wins and -reward if loses
        if row is a tuple (exact coordinate), than will use that for coordinate. Otherwise automatically detect for pos by considering it as row.
        if param board is not passed, then will use current board in this instance
        if param player is not passed, then will use current player"""
        
        if board is None:
            board = self.board
        elif type(board) == str:
            board = self.unpack_state(board)

        if player is None:
            player = "X" if self.current_player == "O" else "O"

        # find position if not specified
        if type(pos) != tuple:
            pos -= 1
            row = [line[pos] for line in board]
            line = [i + 1 for i, x in enumerate(row[1:]) if not row[i] and x]
            if len(line) == 0:
                pos = (0, pos)
            else:
                pos = (line[0], pos)
            last_player = board[pos[0]][pos[1]]
        else:
            last_player = board[pos[0]][pos[1]]
        
        for direction in serach_directions:
            total = 0       # counter recording how many checkers found in a line
            for dirt in direction:
                try:
                    for i in range(1,4):
                        # in case for negative index value (which is a special feature in python but detrimental here)
                        if pos[0] + dirt[0] * i < 0 or pos[1] + dirt[1] * i < 0:
                            break
                        if board[pos[0] + dirt[0] * i][pos[1] + dirt[1] * i] == last_player:   # checker of current player found
                            total += 1
                        else: 
                            break
                    if total >= 3:
                        if player == last_player:
                            return WINNING_REWARD
                        return LOSING_REWARD
                except IndexError:
                    continue

        # check for draw
        if all(board[0]):
            return TIE_REWARD
        
        return False


    def next_player(self, player = None):
        if player is None:
            player = self.current_player
        return player1 if player == player2 else player2

def is_ended(x,y,board,winner_message):
    'local function to check for winning'

    result = board.check_winning((x,y))
    if result is False:
        return False
    
    if result:
        print(winner_message)
    else:
        print('tie!')

    return True


def player_computer():

    board = Board(start_player = player2)
    ai_1 = UCT_ver1(board, name = 'ai1', verbose = VERBOSE)

    try:
        # mainloop
        while True:

            # ask player to choose player
            board.current_player = player2

            # display initial board
            board.display()

            # game loop
            while True:
                # ask player for input
                print("%s's turn (you)" %(board.current_player))
                player_input = input('> ')

                # set checker and input validation
                x,y = board.drop_checker(player_input)
                if x is not False:
                    board.display()
                    # check if the player wins
                    if is_ended(x,y,board, '%s (you) wins the game!' %(board.current_player)):
                        break
                    else:
                        # ai plays
                        print("%s's turn (computer)" %(current_player))
                        ai_1.update(board.get_compact_state(board.board), board.current_player)
                        # calculate the optimal action
                        action = ai_1.get_action()
                        x, y = board.drop_checker(action)
                        board.display()
                        # check if ai wins
                        if is_ended(x,y,board,'%s (computer) wins the game!' %(board.current_player)):
                            break

                else:
                    sleep(1)
                    board.display()

            
            # ask for player whether he or she want to play another one
            continue_choice = input('Another game? (Y/N)')
            if continue_choice in ('Y','y'):
                board.init_board()
                continue
            else:
                break
        
    finally:
        print('*' * 50)
        print("saving progress...")
        ai_1.save()
        print("progress saved successfully.")

    # when player quits
    print('\nThank you for playing Connect 4! Please like and subscribe :)\n')


def computer_computer():
    board = Board(start_player = player2)
    ai_1 = UCT_ver1(board, name = 'ai1', verbose = VERBOSE)
    ai_2 = UCT_ver1(board, name = 'ai2', verbose = VERBOSE)

    try:
        while True:
            board.current_player = player1
            board.display()

            while True:
                # ai_1 plays
                print("%s's turn (computer1)" %(current_player))
                ai_1.update(board.get_compact_state(board.board), board.current_player)
                # calculate the optimal action
                action = ai_1.get_action()
                x, y = board.drop_checker(action)
                board.display()
                # check if ai wins
                if is_ended(x,y,board,'%s (computer) wins the game!' %(board.current_player)):
                    break
                
                # ai_2 plays
                print("%s's turn (computer2)" %(current_player))
                ai_2.update(board.get_compact_state(board.board), board.current_player)
                # calculate the optimal action
                action = ai_2.get_action()
                x, y = board.drop_checker(action)
                board.display()
                # check if ai wins
                if is_ended(x,y,board,'%s (computer2) wins the game!' %(board.current_player)):
                    break

            # save after every round
            ai_1.save()
            ai_2.save()
            
            board.init_board()
    finally:
        print('*' * 50)
        print("saving progress...")
        ai_1.save()
        ai_2.save()
        print("progress saved successfully.")


if __name__ == "__main__":
    
    # display welcome message
    system('clear')
    #input(welcome_message)

    # choose mode
    ##  1. player - computer
    ##  2. computer - computer
    mode = input("enter mode:\n1. player - computer\n2. computer - computer\n> ")

    if mode == "1":
        player_computer()
    elif mode == "2":
        computer_computer()

    