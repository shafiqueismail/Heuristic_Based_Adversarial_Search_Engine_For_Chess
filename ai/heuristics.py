    
    
    
    
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
