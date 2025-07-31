# Heuristic-Based Adversarial Search Engine for MiniChess

A **MiniChess AI engine** implementing classic adversarial search techniques such as **Minimax** and **Alpha-Beta Pruning**, enhanced with:

- **Iterative Deepening Search**
- **Time-limited search control**
- **Transposition Tables** for optimization
- Multiple **Heuristic Evaluators** (`e0` to `e4`)
- Support for **Human vs AI**, **AI vs AI**, and **Human vs Human** modes
- Full game trace logging with move evaluation, time stats, and strategic analysis

---

## Heuristics Included

| Heuristic | Description |
|----------|-------------|
| `e0` | Material value only |
| `e1` | Material + central control + king edge penalty |
| `e2` | Material + mobility (number of legal moves) |
| `e3` | Material + king safety based on threatened squares |
| `e4` | Material + piece-square table + aggression bonus |

---

## Features

- 5×5 **MiniChess** board with simplified rules
- Turn-based engine with built-in **move legality checks**
- **Pawn promotion**, **game termination**, and **draw detection**
- **Iterative deepening** up to 25 plies (or until timeout)
- Move logs saved to `.txt` with rich debug info: evaluations, board snapshots, AI metrics
- **Flexible CLI interface** for selecting:
  - Game mode (PvP, PvAI, AIvAI)
  - Search algorithm (Minimax / Alpha-Beta)
  - Time limits and turn caps
  - Heuristic functions per AI

---

## Project Structure
- Run the file "MiniChessSkeletonCode.py" to see the game-play.
