from typing import List


class MazeGame:
    """
    Joc simplu de labirint pentru touchscreen.
    # = perete, E = ieșire, P = jucător.
    """

    def __init__(self):
        self._template = [
            "#########",
            "#P     E#",
            "# ### # #",
            "#   # # #",
            "### #   #",
            "#   ### #",
            "#       #",
            "#########",
        ]
        self.reset()

    def reset(self):
        self.grid: List[List[str]] = [list(row) for row in self._template]
        self.player_pos = self._find_player()

    def _find_player(self):
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == "P":
                    return (r, c)
        raise RuntimeError("Player not found in maze template.")

    def render(self) -> str:
        return "\n".join("".join(row) for row in self.grid)

    def move(self, direction: str) -> str:
        deltas = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1),
        }
        if direction not in deltas:
            return "block"

        dr, dc = deltas[direction]
        r, c = self.player_pos
        nr, nc = r + dr, c + dc

        # boundaries
        if nr < 0 or nr >= len(self.grid) or nc < 0 or nc >= len(self.grid[0]):
            return "block"

        target = self.grid[nr][nc]
        if target == "#":
            return "block"

        # move player
        self.grid[r][c] = " "
        self.grid[nr][nc] = "P"
        self.player_pos = (nr, nc)

        if target == "E":
            return "win"
        return "move"


if __name__ == "__main__":
    game = MazeGame()
    print(game.render())
    print(game.move("right"))

