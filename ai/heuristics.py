def evaluate_board_e0(game_state, ai_color):
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
    return board_eval if ai_color == "white" else -board_eval


def evaluate_board_e1(game_state, ai_color):
    center_positions = {(2, 2), (2, 3), (3, 2), (3, 3)}
    score = 0

    piece_values = {'p': 1, 'B': 3, 'N': 3, 'Q': 9, 'K': 999}

    for r in range(5):
        for c in range(5):
            piece = game_state["board"][r][c]
            if piece != '.':
                sign = 1 if piece[0] == 'w' else -1
                p_type = piece[1]

                score += sign * piece_values.get(p_type, 0)
                if (r, c) in center_positions:
                    score += 0.2 * sign
                if p_type == 'K' and (r == 0 or r == 4 or c == 0 or c == 4):
                    score -= 0.3 * sign

    return score if ai_color == "white" else -score


def evaluate_board_e2(game_state, ai_color, engine):
    original_turn = game_state["turn"]

    game_state["turn"] = "white"
    white_moves = engine.valid_moves(game_state)

    game_state["turn"] = "black"
    black_moves = engine.valid_moves(game_state)

    game_state["turn"] = original_turn

    material_score = evaluate_board_e0(game_state, ai_color)
    mobility_score = (len(white_moves) - len(black_moves)) * 0.3

    return (material_score + mobility_score) if ai_color == "white" else -(material_score + mobility_score)


def evaluate_board_e3(game_state, ai_color, engine):
    base_score = evaluate_board_e0(game_state, ai_color)

    original_turn = game_state["turn"]
    opponent_turn = 'white' if original_turn == 'black' else 'black'
    game_state["turn"] = opponent_turn
    opponent_moves = engine.valid_moves(game_state)
    threatened_squares = {move[1] for move in opponent_moves}
    game_state["turn"] = original_turn

    w_king_positions = []
    b_king_positions = []

    for r in range(5):
        for c in range(5):
            piece = game_state["board"][r][c]
            if piece == 'wK':
                w_king_positions.append((r, c))
            elif piece == 'bK':
                b_king_positions.append((r, c))

    king_safety_score = 0
    for (r, c) in w_king_positions:
        if (r, c) in threatened_squares:
            king_safety_score -= 5
    for (r, c) in b_king_positions:
        if (r, c) in threatened_squares:
            king_safety_score += 5

    total_score = base_score + king_safety_score
    return total_score if ai_color == "white" else -total_score


def evaluate_board_e4(game_state, ai_color, engine):
    piece_square_table = {
        'bp': [[2, 2, 2, 2, 2], [2.25, 2.3, 2.3, 2.3, 2.3], [3.1, 3.3, 3.3, 3.3, 3.1],
               [3.15, 3.4, 3.4, 3.4, 3.15], [4, 4, 4, 4, 4]],
        'bN': [[1.2, 1.3, 1.3, 1.3, 1.2], [1.3, 2.4, 2.4, 2.4, 1.3], [1.3, 2.4, 3.5, 2.4, 1.3],
               [1.3, 2.4, 2.4, 2.4, 1.3], [1.2, 1.3, 1.3, 1.3, 1.2]],
        'bB': [[1.3, 1.4, 1.4, 1.4, 1.3], [1.3, 2.6, 2.6, 2.6, 1.3], [1.4, 2.6, 2.75, 2.6, 1.4],
               [1.3, 2.6, 2.6, 2.6, 1.3], [1.2, 1.3, 1.3, 1.3, 1.2]],
        'bQ': [[1.5] * 5] * 5,
        'bK': [[0.2] * 5] * 5,
        'wp': [[4, 4, 4, 4, 4], [3.15, 3.4, 3.4, 3.4, 3.15], [3.1, 3.3, 3.3, 3.3, 3.1],
               [2.25, 2.3, 2.3, 2.3, 2.3], [2, 2, 2, 2, 2]],
        'wN': [[1.2, 1.3, 1.3, 1.3, 1.2], [1.3, 2.4, 2.4, 2.4, 1.3], [1.3, 2.4, 3.5, 2.4, 1.3],
               [1.3, 2.4, 2.4, 2.4, 1.3], [1.2, 1.3, 1.3, 1.3, 1.2]],
        'wB': [[1.3, 1.4, 1.4, 1.4, 1.3], [1.3, 2.6, 2.6, 2.6, 1.3], [1.4, 2.6, 2.75, 2.6, 1.4],
               [1.3, 2.6, 2.6, 2.6, 1.3], [1.2, 1.3, 1.3, 1.3, 1.2]],
        'wQ': [[1.5] * 5] * 5,
        'wK': [[0.2] * 5] * 5
    }

    base_score = evaluate_board_e0(game_state, ai_color)

    original_turn = game_state["turn"]
    game_state["turn"] = "white"
    white_moves = engine.valid_moves(game_state)
    game_state["turn"] = "black"
    black_moves = engine.valid_moves(game_state)
    game_state["turn"] = original_turn

    aggression_score = 0
    for move in white_moves:
        _, end_pos = move
        captured = game_state["board"][end_pos[0]][end_pos[1]]
        if captured != '.' and captured[0] == 'b':
            aggression_score += 2 if captured[1] in ['Q', 'K'] else 1

    for move in black_moves:
        _, end_pos = move
        captured = game_state["board"][end_pos[0]][end_pos[1]]
        if captured != '.' and captured[0] == 'w':
            aggression_score -= 2 if captured[1] in ['Q', 'K'] else 1

    psq_bonus = 0
    for r in range(5):
        for c in range(5):
            piece = game_state["board"][r][c]
            if piece in piece_square_table:
                psq_bonus += piece_square_table[piece][r][c]

    total_score = base_score + aggression_score + psq_bonus
    return total_score if ai_color == "white" else -total_score
