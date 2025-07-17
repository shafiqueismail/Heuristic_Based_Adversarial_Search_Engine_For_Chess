import math
import copy
import time
import argparse
import sys, traceback

NumOfMoves = 0
WhiteMoveCounter = 1
BlackMoveCounter = 1
TIME_LIMIT = 0  
player1_color = 'w'
algorithm = None
max_turns = 10
mode = None
chosen_heuristic = 'e0'
chosen_heuristic_1 = 'e0'
chosen_heuristic_2 = 'e0'

class MiniChess:
    def __init__(self):
        self.current_game_state = self.init_board()
        self.new_game_state = self.init_board()
        self.move_counter = 0
        self.ai_color = None
        self.ai_colorH = None
        self.trace_file_name = None
        self.heuristic_name = None

        # Simple cache to remember positions
        self.transposition_table = {}

        # New attributes for AI stats
        self.cumulative_states_explored = 0
        self.states_explored_by_depth = {}  # e.g. {1: 0, 2: 0, ...}
        self.total_branching_sum = 0
        self.minimax_calls = 0
        self.last_move_info = None  # Track the most recent move and turn

    def init_board(self):
        state = {
            "board":
                [['bK', 'bQ', 'bB', 'bN', '.'],
                 ['.', '.', 'bp', 'bp', '.'],
                 ['.', '.', '.', '.', '.'],
                 ['.', 'wp', 'wp', '.', '.'],
                 ['.', 'wN', 'wB', 'wQ', 'wK']],
            "turn": 'white',
        }
        return state

    def display_board(self, game_state):
        print()
        for i, row in enumerate(game_state["board"], start=1):
            print(str(6 - i) + "  " + ' '.join(piece.rjust(3) for piece in row))
        print()
        print("     A   B   C   D   E")
        print()

    def is_valid_move(self, game_state, move):
        start, end = move
        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col]

        if piece == '.':  # No piece to move
            return False

        piece_color = 'white' if piece[0] == 'w' else 'black'

        if piece_color != game_state["turn"]:  # Check if it's the correct turn
            return False

        valid_moves = self.valid_moves(game_state)

        return move in valid_moves

    def valid_moves(self, game_state):
        moves = []
        board = game_state["board"]
        turn = game_state["turn"]

        for row in range(5):
            for col in range(5):
                piece = board[row][col]
                if piece != '.' and ((turn == "white" and piece[0] == 'w') or (turn == "black" and piece[0] == 'b')):
                    moves.extend(self.get_piece_moves(board, row, col, piece))

        return moves

    def get_piece_moves(self, board, row, col, piece):
        piece_type = piece[1]
        if piece_type == 'K':
            return self.king_moves(board, row, col)
        elif piece_type == 'Q':
            return self.queen_moves(board, row, col)
        elif piece_type == 'B':
            return self.bishop_moves(board, row, col)
        elif piece_type == 'N':
            return self.knight_moves(board, row, col)
        elif piece_type == 'p':
            return self.pawn_moves(board, row, col, piece[0])
        return []

    def king_moves(self, board, row, col):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        return self.get_moves_in_directions(board, row, col, directions, limit=1)

    def queen_moves(self, board, row, col):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        return self.get_moves_in_directions(board, row, col, directions)

    def bishop_moves(self, board, row, col):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self.get_moves_in_directions(board, row, col, directions)

    def knight_moves(self, board, row, col):
        moves = []
        possible_jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in possible_jumps:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 5 and 0 <= new_col < 5 and (
                    board[new_row][new_col] == '.' or board[new_row][new_col][0] != board[row][col][0]):
                moves.append(((row, col), (new_row, new_col)))
        return moves

    def pawn_moves(self, board, row, col, color):
        moves = []
        direction = -1 if color == 'w' else 1
        new_row = row + direction

        if 0 <= new_row < 5:
            # Forward move (only if the destination is empty)
            if board[new_row][col] == '.':
                moves.append(((row, col), (new_row, col)))

            # Capture diagonally
            for new_col in [col - 1, col + 1]:
                if 0 <= new_col < 5 and board[new_row][new_col] != '.' and board[new_row][new_col][0] != color:
                    moves.append(((row, col), (new_row, new_col)))

        return moves

    def get_moves_in_directions(self, board, row, col, directions, limit=5):
        moves = []
        piece_color = board[row][col][0]
        for dr, dc in directions:
            for step in range(1, limit + 1):
                new_row, new_col = row + dr * step, col + dc * step
                if 0 <= new_row < 5 and 0 <= new_col < 5:
                    if board[new_row][new_col] == '.':
                        moves.append(((row, col), (new_row, new_col)))
                    elif board[new_row][new_col][0] != piece_color:
                        moves.append(((row, col), (new_row, new_col)))
                        break  # Stop moving in this direction if capturing an enemy piece
                    else:
                        break  # Stop if blocked by own piece
                else:
                    break  # Stop if out of bounds
        return moves

    def make_move(self, game_state, move, log_move=True, simulation=False,
                  elapsed_time=None, ai_eval_score=None, ai_final_score=None):
        """
        elapsed_time: time in seconds for the AI move
        ai_eval_score: heuristic score of the resulting board
        ai_final_score: final minimax/alpha-beta search score
        """
        global WhiteMoveCounter
        global BlackMoveCounter
        global NumOfMoves

        start, end = move
        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col]
        captured_piece = self.captured_piece(game_state, end)

        # Check if the move is valid
        if not self.is_valid_move(game_state, move):
            print("Invalid move. Try again.")
            return game_state

        if piece == '.':
            print("ERROR: Trying to move an empty square!")
            return game_state  # Prevent breaking the board


        # Move the piece
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece

        pawn_to_queen = self.handle_pawn_promotion(game_state)

        # If this is a real (non-simulation) move, log & update counters
        if not simulation:

            # Store the last move info for end-of-game logs
            current_player = "White" if piece[0] == 'w' else "Black"
            if current_player == "White":
                turn_number = WhiteMoveCounter
            else:
                turn_number = BlackMoveCounter
            self.last_move_info = (current_player, turn_number, move)

            # Write move info to our trace file
            if log_move and self.trace_file_name:

                # Convert from board indices to something like C3 -> C4
                # Example: col -> letter, row -> number
                start_col_letter = chr(ord('A') + start_col)
                end_col_letter = chr(ord('A') + end_col)
                start_row_num = str(5 - start_row)
                end_row_num = str(5 - end_row)

                action_str = f"Moved {piece} from {start_col_letter}{start_row_num} to {end_col_letter}{end_row_num}"
                
                with open(self.trace_file_name, "a") as f:
                    f.write("\n====================================\n")
                    f.write(f"Player: {current_player}\n")
                    
                    if current_player == "White":
                        f.write(f"Turn #{WhiteMoveCounter}\n")
                    else:
                        f.write(f"Turn #{BlackMoveCounter}\n")
                    f.write(f"Action: {action_str}\n")
                    
                    if captured_piece != '.':
                        f.write(f"Captured piece: {captured_piece}\n")
                    
                    if pawn_to_queen:
                        f.write(f"Pawn Promotion: {piece} became a queen!\n")
                    
                    # If AI info is provided, log it
                    if elapsed_time is not None:
                        f.write(f"Time for this action: {elapsed_time:.2f} sec\n")

                    #calcualting evaluation total of all the pieces on the board currently
                    total_eval = 0
                    for row in game_state["board"]: 
                        for piece in row:
                            if piece == 'wp':
                                total_eval += 1
                            elif piece == 'wB' or piece == 'wN':
                                total_eval += 3
                            elif piece == 'wQ':
                                total_eval += 9
                            elif piece == 'wK':
                                total_eval += 999
                            elif piece == 'bp':
                                total_eval -= 1
                            elif piece == 'bB' or piece == 'bN':
                                total_eval -= 3
                            elif piece == 'bQ':
                                total_eval -= 9
                            elif piece == 'bK':
                                total_eval -= 999
                    if total_eval is not None:
                        f.write(f"Heuristic score of resulting board: {total_eval}\n")
                    if ai_final_score is not None:
                        f.write(f"Minimax/Alpha-Beta search score: {ai_final_score}\n")

                    # Show new board configuration
                    f.write("New Board Configuration:\n")
                    for row_data in game_state["board"]:
                        f.write(" ".join(row_data) + "\n")

                    global mode
                    # Example of AI-specific cumulative info
                    if ((current_player.lower() == self.ai_color) or (current_player.lower() == self.ai_colorH)) and mode in ['2', '3']:
                        f.write("\nAI Cumulative Info:\n")
                        # (a) number of states explored
                        f.write(f" - Cumulative states explored: {self.format_number(self.cumulative_states_explored)}\n")

                        # (b) states by depth (e.g. 1=144, 2=1.1k,...)
                        states_by_depth_str = ", ".join(
                            f"{d}={self.format_number(count)}" for d, count in sorted(self.states_explored_by_depth.items())
                        )
                        f.write(f" - Cumulative states explored by depth: {states_by_depth_str}\n")

                        # (c) percentages by depth
                        total_states = float(self.cumulative_states_explored) if self.cumulative_states_explored else 1.0
                        percents_by_depth_str = ", ".join(
                            f"{d}={((count / total_states) * 100):.1f}%" for d, count in sorted(self.states_explored_by_depth.items())
                        )
                        f.write(f" - Cumulative % states explored by depth: {percents_by_depth_str}\n")

                        # (d) average branching factor
                        if self.minimax_calls > 0:
                            avg_branching = self.total_branching_sum / float(self.minimax_calls)
                        else:
                            avg_branching = 0.0
                        f.write(f" - Average branching factor: {avg_branching:.1f}\n")

            # Update move counters and check for draw
            piece_eliminated = self.check_game_end_conditions(game_state, piece, end_row, end_col)
            self.update_move_counters(captured_piece)
            self.check_for_draw()

        # Switch turns
        game_state["turn"] = "black" if game_state["turn"] == "white" else "white"

        return game_state

    def handle_pawn_promotion(self, game_state):
        pawn_to_queen = False
        for col in range(5):
            if game_state["board"][0][col] == 'wp':
                game_state["board"][0][col] = 'wQ'
                pawn_to_queen = True
            elif game_state["board"][4][col] == 'bp':
                game_state["board"][4][col] = 'bQ'
                pawn_to_queen = True
        return pawn_to_queen

    def check_game_end_conditions(self, game_state, piece, end_row, end_col):
        white_king_exists = False
        black_king_exists = False

        # Check if the kings are still on the board
        for row in game_state["board"]:
            for piece in row:
                if piece == 'wK':
                    white_king_exists = True
                elif piece == 'bK':
                    black_king_exists = True

        if not white_king_exists:
            self.end_game("Black wins!", "BLACK WINS")
        elif not black_king_exists:
            self.end_game("White wins!", "WHITE WINS")

        return game_state["board"][end_row][end_col]  # Return the piece that was eliminated (if any)    
    
    def end_game(self, message, log_message):
        """
        Called when the game ends (king gone or draw).
        Writes final result in trace_file_name with last move info & winner.
        """
        if self.trace_file_name:
            with open(self.trace_file_name, "a") as f:
                if self.last_move_info:
                    winner, turn_num, last_move = self.last_move_info
                    start, end = last_move
                    start_col_letter = chr(ord('A') + start[1])
                    end_col_letter = chr(ord('A') + end[1])
                    start_row_num = str(5 - start[0])
                    end_row_num = str(5 - end[0])
                    final_move_str = f"({start_col_letter}{start_row_num} -> {end_col_letter}{end_row_num})"
                    f.write(
                        f"\n=== GAME OVER ===\n"
                        f"Final result: {log_message}\n"
                        f"Decision move: {final_move_str}\n"
                        f"Occurred at turn #{turn_num}\n"
                    )
                else:
                    # Fallback if no last_move_info
                    f.write(f"\n=== GAME OVER ===\nFinal result: {log_message}\n")

        print(message)
        sys.exit(0)

    def update_move_counters(self, captured_piece):
        global WhiteMoveCounter
        global BlackMoveCounter

        if captured_piece != '.':
            self.move_counter = 0
        else:
            self.move_counter += 1

        if self.current_game_state["turn"] == "white":
            WhiteMoveCounter += 1
        else:
            BlackMoveCounter += 1

    def check_for_draw(self):
        if self.move_counter >= 10:
            if self.trace_file_name:
                with open(self.trace_file_name, "a") as f:
                    f.write("\n=== GAME OVER ===\nResult: DRAW\n")
                    if self.last_move_info:
                        player, turn_num, last_move = self.last_move_info
                        f.write(f"Draw occurred after {player}'s turn at turn #{turn_num}\n")
            print("No one won... It's a draw!")
            sys.exit(0)

    def captured_piece(self, game_state, end):
        end_row, end_col = end
        piece = game_state["board"][end_row][end_col]
        return piece if piece != '.' else '.'

    # Check if the king is on the board
    def king_exists(self, game_state, simulation=False):

        white_king = False
        black_king = False

        for row in game_state["board"]:
            for piece in row:
                if piece == "wK":
                    white_king = True
                elif piece == "bK":
                    black_king = True

        if simulation:
            return white_king and black_king  # Just return status, don't exit game

        if not white_king:
            self.end_game("Black wins!", "BLACK WINS")
        elif not black_king:
            self.end_game("White wins!", "WHITE WINS")

        return white_king and black_king

    def is_king_in_danger(self, game_state, king_color):
        """
        Determines if a king of the given color can be captured by the opponent 
        in their very next move. This is used to give priority to moves that save the king.
        """
        king_positions = []
        # Look for the positions of the king whose color is king_color
        for r in range(5):
            for c in range(5):
                piece = game_state["board"][r][c]
                if piece != '.' and piece[0] == king_color and piece[1] == 'K':
                    king_positions.append((r, c))

        # If we can't find such a king, we assume it's 'in danger' by default, 
        # because there's effectively no king left
        if not king_positions:
            return True

        # Temporarily switch the turn to the opponent to find their valid moves
        original_turn = game_state["turn"]
        game_state["turn"] = "white" if original_turn == "black" else "black"

        opponent_moves = self.valid_moves(game_state)

        # Restore the original turn
        game_state["turn"] = original_turn

        # If any of the opponent's moves could end on the king's position, the king is in danger
        king_set = set(king_positions)
        for om in opponent_moves:
            _, end_pos = om
            if end_pos in king_set:
                return True
        return False


    def parse_input(self, move):
        try:
            start, end = move.split()
            start = (5 - int(start[1]), ord(start[0].upper()) - ord('A'))
            end = (5 - int(end[1]), ord(end[0].upper()) - ord('A'))
            return (start, end)
        except:
            return None

    def play(self):
        print("Welcome to Mini Chess!")

        print("Choose the mode:"
              "\n1. Player vs Player"
              "\n2. Player vs AI"
              "\n3. AI vs AI")

        global mode, algorithm, player1_color, TIME_LIMIT, max_turns, chosen_heuristic, chosen_heuristic_1, chosen_heuristic_2

        mode = input("Enter the mode number: ")
        if mode == '1':
            print("Player vs Player mode selected.")
        elif mode == '2':
            print("Player vs AI mode selected.")
        elif mode == '3':
            print("AI vs AI mode selected.")
        else:
            print("Invalid mode. Exiting game.")
            exit(1)

        if mode == '2' or mode == '3':
            print("Which color should player 1 be? (w/b): ")
            player1_color = input().strip().lower()
            if player1_color == 'w':
                print("Player 1 is white and starts first.")
                self.current_game_state["turn"] = 'white'
                self.ai_color = "black"  
                self.ai_colorH = "white"
            elif player1_color == 'b':
                print("Player 1 is black and starts second (after first AI).")
                self.current_game_state["turn"] = 'white'
                self.ai_color = "white"
                self.ai_colorH = "black"  
            else:
                print("Invalid color. Exiting game.")
                exit(1)

            print("Do you want minimax or alpha-beta pruning? (m/a): ")
            algorithm = input().strip().lower()
            if algorithm not in ['m', 'a']:
                print("Invalid algorithm. Exiting game.")
                exit(1)

            print("Select timeout time for the AI: ")
            TIME_LIMIT = int(input().strip())

            print("Select max number of turns (in total): ")
            max_turns = int(input().strip())

            print(f"Choose a heuristic between e0, e1, e2, e3, e4 for AI {self.ai_color}:")
            chosen_heuristic_1 = input().strip().lower()
            if chosen_heuristic_1 not in ['e0', 'e1', 'e2', 'e3', 'e4']:
                print("Invalid heuristic. Exiting game.")
                exit(1)
            if mode == '3':
                print(f"Chose a heuristic for the second AI {self.ai_colorH}: ")
                chosen_heuristic_2 = input().strip().lower()
                if chosen_heuristic_2 not in ['e0', 'e1', 'e2', 'e3', 'e4']:
                    print("Invalid heuristic. Exiting game.")
                    exit(1)

        print("Enter 'exit' to quit the game.")

        # Determine the flag for alpha-beta
        alpha_beta_on = (algorithm == 'a')
        # Build the trace file name
        self.trace_file_name = f"gameTrace-{str(alpha_beta_on).lower()}-{TIME_LIMIT}-{max_turns}.txt"

        player1_name = "White" if player1_color == 'w' else "Black"

        # Write initial game parameters to trace file
        with open(self.trace_file_name, "w") as f:
            f.write(f"Game Parameters:\n")
            f.write(f" - Timeout (t): {TIME_LIMIT}\n")
            f.write(f" - Max Turns (m): {max_turns}\n")
            f.write(f" - Player 1 color: {player1_name.upper()}\n")
            if mode == '2':
                if player1_color == 'w':
                    f.write(" - Player 1 = Human & Player 2 = AI\n")
                else:
                    f.write(" - Player 1 = AI & Player 2 = Human\n")
            elif mode == '3':
                f.write(" - Player 1 = AI & Player 2 = AI\n")
            else:
                f.write(" - Player 1 = Human & Player 2 = Human\n")
            f.write(f" - Alpha-Beta: {alpha_beta_on}\n")
            # Example: using a placeholder for your heuristic name
            if mode in ['2', '3'] and hasattr(self, "heuristic_name"):
                f.write(f" - AI (one) Heuristic: {chosen_heuristic_1}\n")
                if mode == '3':
                    f.write(f" - AI (two) Heuristic: {chosen_heuristic_2}\n")
            f.write("\nInitial Board Configuration:\n")
            for row in self.current_game_state["board"]:
                f.write(" ".join(row) + "\n")

        while True:
            # Display the current state of the board each time before a move
            self.display_board(self.current_game_state)

            if mode == '3':
                # In 'AI vs AI' mode, both sides are controlled by the AI
                print(f"AI ({self.current_game_state['turn']}) is thinking...")
                start_time = time.time()

                # Determine if AI should play as the "maximizing" side
                # Typically, white is considered the maximizing player
                ai_is_white = (self.current_game_state['turn'] == 'white')
                
                if (self.current_game_state['turn'] == self.ai_color):
                    chosen_heuristic = chosen_heuristic_1
                else:
                    chosen_heuristic = chosen_heuristic_2

                # Use the minimax (or alpha-beta) approach to find the best move
                best_eval, move = self.use_minimax(self.current_game_state, alpha=-math.inf, beta=math.inf, maximizing_player=ai_is_white, start_time=start_time)

                # If the AI has no valid moves, it loses
                if move is None:
                    print(f"AI ({self.current_game_state['turn']}) has no valid moves. It loses!")
                    exit(1)

                print(f"AI ({self.current_game_state['turn']}) move: {move}")
                # Apply the chosen move to the current game state
                elapsed_time = time.time() - start_time
                self.current_game_state = self.make_move(self.current_game_state, move, simulation=False, elapsed_time=elapsed_time, ai_eval_score=best_eval, ai_final_score=best_eval)

            elif self.current_game_state['turn'] == self.ai_color:
                # If we are in 'Player vs AI' mode and it's AI's turn
                print("AI is thinking...")
                
                chosen_heuristic = chosen_heuristic_1

                start_time = time.time()

                # Determine if the AI is maximizing (if it is playing as white)
                best_eval, move = self.use_minimax(self.current_game_state, alpha=-math.inf, beta=math.inf, maximizing_player=(self.ai_color == 'white'), start_time=start_time)

                if move is None:
                    print(f"AI ({self.ai_color}) has no valid moves. It loses!")
                    exit(1)

                print(f"AI ({self.ai_color}) move: {move}")
                # Apply the AI's chosen move
                elapsed_time = time.time() - start_time
                self.current_game_state = self.make_move(self.current_game_state, move, simulation=False, elapsed_time=elapsed_time, ai_eval_score=best_eval, ai_final_score=best_eval)

            else:
                # If it's not AI vs AI and not AI's turn, then it's a human player's turn
                move = input(f"{self.current_game_state['turn'].capitalize()} to move: ").strip()
                if move.lower() == 'exit':
                    # Allow the player to exit the game
                    print("Game exited.")
                    exit(1)

                # Convert the player's textual input (e.g., "a2 b3") into board coordinates
                move = self.parse_input(move)

                # Validate the move before applying it
                if not move or not self.is_valid_move(self.current_game_state, move):
                    print("Invalid move. Try again.")
                    continue

                # If the move is valid, apply it to the game state
                self.current_game_state = self.make_move(self.current_game_state, move, simulation=False)

            # For modes involving an AI (either 'Player vs AI' or 'AI vs AI'), track the number of moves
            if mode == '2' or mode == '3':
                global NumOfMoves
                # If the number of moves has reached the maximum limit, end the game
                if NumOfMoves > max_turns and WhiteMoveCounter == BlackMoveCounter and WhiteMoveCounter > max_turns and BlackMoveCounter > max_turns:
                    print("Max number of turns reached. Exiting game.")
                    exit(1)
                NumOfMoves += 1

    def use_minimax(self, game_state, alpha, beta, maximizing_player, start_time):
        """
        Initiates a minimax (or alpha-beta if chosen) search to find the best move 
        for the current player. We iteratively deepen up to depth 50 or until the time limit expires.
        """
        global chosen_heuristic

        best_move = None
        # Assume the best evaluation starts at negative infinity for maximizing, or positive infinity for minimizing
        best_eval = -math.inf if maximizing_player else math.inf
        depth = 1

        # We'll increment depth by 1, but we often break sooner if the time limit is reached
        while depth <= 25:

            current_eval, current_move = self.minimax(game_state, depth, alpha, beta, maximizing_player, start_time)

            # If we found a move at this depth, update the best found so far
            if current_move is not None:
                best_eval = current_eval
                best_move = current_move

            # If our allotted time limit is exceeded, we stop searching deeper
            if (time.time() - start_time) >= TIME_LIMIT:
                break

            depth += 1

        return best_eval, best_move

    def minimax(self, game_state, depth, alpha, beta, maximizing_player, start_time):
        """
        Core minimax (or alpha-beta) search:
          1) We terminate (return an evaluation score) if we reach depth 0, 
             the king no longer exists, or time is up.
          2) We generate all valid moves.
          3) We check conditions:
             - if our king is in danger, we first look for moves to save it.
             - if it is not in danger, see if we can capture the opponent's king.
             - otherwise, classify moves as safe or risky (where the king ends up in danger).
          4) We evaluate and sort these moves. Because of the transposition table,
             repeated states aren't re-evaluated.
          5) Use alpha-beta pruning if selected.
        """

        global chosen_heuristic
        # Each time we enter a node, we add 1 to cumulative_states_explored
        self.cumulative_states_explored += 1

        # Track by depth
        if depth not in self.states_explored_by_depth:
            self.states_explored_by_depth[depth] = 0
        self.states_explored_by_depth[depth] += 1

        # 1) Early-stop if we've reached the limit in depth, the king is gone, or we've hit our time limit
        if depth == 0 or not self.king_exists(game_state, simulation=True) or (time.time() - start_time) >= TIME_LIMIT:
            if chosen_heuristic == 'e1':
                return self.evaluate_board_e1(game_state), None
            elif chosen_heuristic == 'e2':
                return self.evaluate_board_e2(game_state), None
            elif chosen_heuristic == 'e3':
                return self.evaluate_board_e3(game_state), None
            elif chosen_heuristic == 'e4':
                return self.evaluate_board_e4(game_state), None
            else:
                return self.evaluate_board_e0(game_state), None

        # Determine the current king's color and the opponent's color
        king_color = 'w' if game_state['turn'] == "white" else 'b'
        opponent_color = 'b' if king_color == 'w' else 'w'

        # Create a transposition key (essentially a snapshot of the board + whose turn + depth + if maximizing)
        trans_key = (tuple(tuple(row) for row in game_state["board"]), game_state['turn'], depth, maximizing_player)

        # If we've seen this exact scenario before, retrieve its stored result
        if trans_key in self.transposition_table:
            return self.transposition_table[trans_key]

        # Generate all possible valid moves for the current player
        all_moves = self.valid_moves(game_state)

        # Count these as a branching opportunity (one node branching into len(all_moves) children)
        self.total_branching_sum += len(all_moves)
        self.minimax_calls += 1

        # 2) If the king is in danger, we want to filter moves that fix this problem
        king_danger = self.is_king_in_danger(game_state, king_color)
        danger_safe_moves = []
        for move in all_moves:
            # Simulate the move
            temp_state = copy.deepcopy(game_state)
            temp_state = self.make_move(temp_state, move, log_move=False, simulation=True)

            # If the king is no longer in danger after this move, keep it as a 'safe' move
            if not self.is_king_in_danger(temp_state, king_color):
                danger_safe_moves.append(move)

        # 3) If the king is not in danger, see if we can capture the opponent's king right away
        king_capture_moves = []
        if not king_danger:
            for move in all_moves:
                temp_state = copy.deepcopy(game_state)
                temp_state = self.make_move(temp_state, move, log_move=False, simulation=True)

                # If the opponent's king doesn't exist after our move, it's a king-capturing move
                if not self.king_exists(temp_state, simulation=True) and not self.is_king_in_danger(temp_state, king_color):
                    king_capture_moves.append(move)

        # Choose which set of moves to evaluate based on the above logic
        if king_danger and danger_safe_moves:
            moves = danger_safe_moves  # Only moves that keep the king safe
        elif king_capture_moves:
            moves = king_capture_moves  # Moves that let us capture the opponent's king
        else:
            # If none of the above situations apply, we categorize moves as 'safe' or 'risky'
            safe_moves = []
            risky_moves = []
            for move in all_moves:
                temp_state = copy.deepcopy(game_state)
                temp_state = self.make_move(temp_state, move, log_move=False, simulation=True)
                # If we're still safe after this move, put it in safe_moves, else in risky
                if not self.is_king_in_danger(temp_state, king_color):
                    safe_moves.append(move)
                else:
                    risky_moves.append(move)

            # If there are safe moves, we do them first, otherwise do the entire move list
            moves = safe_moves + risky_moves if safe_moves else all_moves

        move_evaluations = []

        # Evaluate each move in the chosen set
        for move in moves:
            # If our time is about to run out, break early to avoid going over time
            if (time.time() - start_time) >= TIME_LIMIT - 0.15:
                break

            # Simulate the move
            new_game_state = copy.deepcopy(game_state)
            new_game_state = self.make_move(new_game_state, move, log_move=False, simulation=True)

            # Recursively call minimax (with one less depth) and toggling maximizing_player
            eval_score, _ = self.minimax(new_game_state, depth - 1, alpha, beta, not maximizing_player, start_time)
            move_evaluations.append((move, eval_score))

            # 4) Alpha-beta pruning logic if algorithm == 'a'
            if algorithm == 'a':
                if maximizing_player:
                    alpha = max(alpha, eval_score)
                else:
                    beta = min(beta, eval_score)
                if beta <= alpha:  # If the window is closed, no need to explore further
                    break

        # 5) Sort the evaluated moves to pick the best according to the current player's color and role
        if (player1_color == 'w'):
            # If the player 1 color is white:
            if game_state['turn'] == "white":
                # This means white is playing, so we sort in descending order to get the highest eval first
                move_evaluations.sort(key=lambda x: x[1], reverse=True)                
                # print(f"TRUE Move evaluations at depth {depth} for {game_state['turn']} ({'max' if maximizing_player else 'min'}):")
                # for mv, eval_score in move_evaluations:
                #     print(f"Move: {mv} - Eval: {eval_score}")

            else:
                # If black is playing (and player1 is still white), we also sort in descending order 
                # but the logic might lean differently based on your approach
                move_evaluations.sort(key=lambda x: x[1], reverse=True)
                # print(f"notFALSE Move evaluations at depth {depth} for {game_state['turn']} ({'max' if maximizing_player else 'min'}):")
                # for mv, eval_score in move_evaluations:
                #     print(f"Move: {mv} - Eval: {eval_score}")

        else:
            # If the player 1 color is black:
            if game_state['turn'] == "black":
                # Sort in ascending order for black if we consider black as the minimizing side
                move_evaluations.sort(key=lambda x: x[1], reverse=False)
                # print(f"FALSE2 Move evaluations at depth {depth} for {game_state['turn']} ({'max' if maximizing_player else 'min'}):")
                # for mv, eval_score in move_evaluations:
                #     print(f"Move: {mv} - Eval: {eval_score}")

            else:
                # Otherwise sort in descending for white
                move_evaluations.sort(key=lambda x: x[1], reverse=True)
                # print(f"TRUE2 Move evaluations at depth {depth} for {game_state['turn']} ({'max' if maximizing_player else 'min'}):")
                # for mv, eval_score in move_evaluations:
                #     print(f"Move: {mv} - Eval: {eval_score}")


        # After sorting, the first element in move_evaluations is the best move for the current side
        if move_evaluations:
            best_eval = move_evaluations[0][1]
            best_move = move_evaluations[0][0]
        else:
            # If we have no moves, set best_eval accordingly and best_move to None
            best_eval = -math.inf if maximizing_player else math.inf
            best_move = None

        # Store the result in the transposition table to avoid recalculating
        self.transposition_table[trans_key] = (best_eval, best_move)

        return best_eval, best_move

    def evaluate_board_e0(self, game_state):
        e0 = {
            'wp': 1, 'wB': 3, 'wN': 3, 'wQ': 9, 'wK': 999,
            'bp': 1, 'bB': 3, 'bN': 3, 'bQ': 9, 'bK': 999
        }

        white_score = 0
        black_score = 0

        for row in game_state["board"]:
            for piece in row:
                if piece in e0:
                    if piece[0] == 'w':
                        white_score += e0[piece]
                    else:
                        black_score += e0[piece]

        board_eval = white_score - black_score
        return board_eval if self.ai_color == "white" else -board_eval

    def evaluate_board_e1(self, game_state):
        """
        Add a small bonus for pieces near the center and penalize isolated kings.
        """
        center_positions = {(2,2), (2,3), (3,2), (3,3)}
        score = 0
        
        # Basic piece values
        piece_values = {
            'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999
        }
        
        for r in range(5):
            for c in range(5):
                piece = game_state["board"][r][c]
                if piece != '.':
                    sign = 1 if piece[0] == 'w' else -1
                    p_type = piece[1]
                    
                    # Add base piece value
                    if p_type in piece_values:
                        score += sign * piece_values[p_type]
                    
                    # Give extra points for controlling/occupying center squares
                    if (r, c) in center_positions:
                        score += 0.2 * sign

                    # Slight penalty if the king is on the edge (to encourage safer middle positions)
                    if p_type == 'K' and (r == 0 or r == 4 or c == 0 or c == 4):
                        score -= 0.3 * sign
        
        # Flip if AI is black
        return score if self.ai_color == "white" else -score


    def evaluate_board_e2(self, game_state):
        """
        Evaluate board by counting mobility: how many moves are available to each side.
        """
        # Temporarily store current turn
        original_turn = game_state["turn"]
        
        # Count white moves
        game_state["turn"] = "white"
        white_moves = self.valid_moves(game_state)
        white_mobility = len(white_moves)
        
        # Count black moves
        game_state["turn"] = "black"
        black_moves = self.valid_moves(game_state)
        black_mobility = len(black_moves)
        
        # Restore original turn
        game_state["turn"] = original_turn
        
        # Combine mobility difference with a simple material count
        material_score = self.evaluate_board_e0(game_state)
        mobility_score = (white_mobility - black_mobility) * 0.3
        
        return (material_score + mobility_score) if self.ai_color == "white" else -(material_score + mobility_score)

    def evaluate_board_e3(self, game_state):
        """
        King safety through threatened squares and quick checks:
        - Give a bonus if the opponent's king squares are threatened.
        - Penalize if your king squares are threatened.
        """
        # Base material score
        base_score = self.evaluate_board_e0(game_state)
        
        # Temporarily switch to opponent's turn to find which squares they threaten
        original_turn = game_state["turn"]
        opponent_turn = 'white' if original_turn == 'black' else 'black'
        game_state["turn"] = opponent_turn
        opponent_moves = self.valid_moves(game_state)
        threatened_squares = {move[1] for move in opponent_moves}
        
        # Restore original turn
        game_state["turn"] = original_turn
        
        # Find king positions
        w_king_positions = []
        b_king_positions = []
        for r in range(5):
            for c in range(5):
                piece = game_state["board"][r][c]
                if piece == 'wK':
                    w_king_positions.append((r,c))
                elif piece == 'bK':
                    b_king_positions.append((r,c))

        king_safety_score = 0
        # Penalize threatened squares around your king, reward threatened squares near opponent's king
        for (r,c) in w_king_positions:
            if (r,c) in threatened_squares:
                king_safety_score -= 5  # penalty if white king is threatened
        for (r,c) in b_king_positions:
            if (r,c) in threatened_squares:
                king_safety_score += 5  # reward if black king is threatened when it's your move
        
        total_score = base_score + king_safety_score
        return total_score if self.ai_color == "white" else -total_score

    def evaluate_board_e4(self, game_state):
        """
        Piece-Square Table & Aggression:
        - Distinct tables for white and black pieces so orientation doesn't cause inaccuracies.
        - Reward advanced positions for pawns, center squares for knights/bishops, etc.
        - Slight bonus for threatening opponent's high-value pieces.
        """

        piece_square_table = {
            
            # Black tables (row 0 is black’s back rank, row 4 is black’s front)
            'bp': [
                [2,  2,  2,  2,  2 ],
                [2.25,  2.3,  2.3,  2.3,  2.3 ],
                [3.1,  3.3,  3.3,  3.3,  3.1 ],
                [3.15, 3.4,  3.4,  3.4,  3.15],
                [4,  4,  4,  4,  4 ],
            ],
            'bN': [
                [1.2, 1.3, 1.3, 1.3, 1.2],
                [1.3, 2.4, 2.4, 2.4, 1.3],
                [1.3, 2.4, 3.5, 2.4, 1.3],
                [1.3, 2.4, 2.4, 2.4, 1.3],
                [1.2, 1.3, 1.3, 1.3, 1.2],
            ],
            'bB': [
                [1.3, 1.4, 1.4, 1.4, 1.3],
                [1.3, 2.6, 2.6, 2.6, 1.3],
                [1.4, 2.6, 2.75, 2.6, 1.4],
                [1.3, 2.6, 2.6, 2.6, 1.3],
                [1.2, 1.3, 1.3, 1.3, 1.2],
            ],
            'bQ': [
                [1.5, 1.5, 1.5, 1.5, 1.5],
                [1.5, 2.6, 2.6, 2.6, 1.5],
                [1.5, 2.6, 3.7, 2.6, 1.5],
                [1.5, 2.6, 2.6, 2.6, 1.5],
                [1.5, 1.5, 1.5, 1.5, 1.5],
            ],
            'bK': [
                [0.2, 0.2, 0.2, 0.2, 0.2],
                [0.2, 1.4, 1.4, 1.4, 0.2],
                [0.2, 1.4, 0.2, 1.4, 0.2],
                [0.2, 1.4, 1.4, 1.4, 0.2],
                [0.2, 0.2, 0.2, 0.2, 0.2],
            ],
            # White tables (row 0 is top, row 4 is bottom)
            'wp': [
                [4,  4,  4,  4,  4 ],
                [3.15, 3.4,  3.4,  3.4,  3.15],
                [3.1,  3.3,  3.3,  3.3,  3.1 ],
                [2.25,  2.3,  2.3,  2.3,  2.3 ],
                [2,  2,  2,  2,  2 ],
            ],
            'wN': [
                [1.2, 1.3, 1.3, 1.3, 1.2],
                [1.3, 2.4, 2.4, 2.4, 1.3],
                [1.3, 2.4, 3.5, 2.4, 1.3],
                [1.3, 2.4, 2.4, 2.4, 1.3],
                [1.2, 1.3, 1.3, 1.3, 1.2],
            ],
            'wB': [
                [1.3, 1.4, 1.4, 1.4, 1.3],
                [1.3, 2.6, 2.6, 2.6, 1.3],
                [1.4, 2.6, 2.75, 2.6, 1.4],
                [1.3, 2.6, 2.6, 2.6, 1.3],
                [1.2, 1.3, 1.3, 1.3, 1.2],
            ],
            'wQ': [
                [1.5, 1.5, 1.5, 1.5, 1.5],
                [1.5, 2.6, 2.6, 2.6, 1.5],
                [1.5, 2.6, 3.7, 2.6, 1.5],
                [1.5, 2.6, 2.6, 2.6, 1.5],
                [1.5, 1.5, 1.5, 1.5, 1.5],
            ],
            'wK': [
                [0.2, 0.2, 0.2, 0.2, 0.2],
                [0.2, 1.4, 1.4, 1.4, 0.2],
                [0.2, 1.4, 0.2, 1.4, 0.2],
                [0.2, 1.4, 1.4, 1.4, 0.2],
                [0.2, 0.2, 0.2, 0.2, 0.2],
            ],
        }

        # Base material score
        base_score = self.evaluate_board_e0(game_state)

        # Temporarily gather all valid moves for each side
        original_turn = game_state["turn"]
        game_state["turn"] = "white"
        white_moves = self.valid_moves(game_state)
        game_state["turn"] = "black"
        black_moves = self.valid_moves(game_state)
        game_state["turn"] = original_turn

        # Bonus for threatening high-value opponent pieces
        aggression_score = 0
        for move in white_moves:
            start_pos, end_pos = move
            piece_captured = game_state["board"][end_pos[0]][end_pos[1]]
            if piece_captured != '.' and piece_captured[0] == 'b':
                if piece_captured[1] in ['Q', 'K']:
                    aggression_score += 2
                else:
                    aggression_score += 1
        for move in black_moves:
            start_pos, end_pos = move
            piece_captured = game_state["board"][end_pos[0]][end_pos[1]]
            if piece_captured != '.' and piece_captured[0] == 'w':
                if piece_captured[1] in ['Q', 'K']:
                    aggression_score -= 2
                else:
                    aggression_score -= 1

        # Piece-square bonuses
        psq_bonus = 0
        for r in range(5):
            for c in range(5):
                piece = game_state["board"][r][c]
                if piece in piece_square_table:
                    psq_bonus += piece_square_table[piece][r][c]

        total_score = base_score + aggression_score + psq_bonus
        return total_score if self.ai_color == "white" else -total_score
    
    # Helper to format large numbers into e.g. 1.2k, 2.2M, etc.
    def format_number(self, num):
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}k"
        else:
            return str(num)


if __name__ == "__main__":
    game = MiniChess()
    game.play()