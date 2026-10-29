import unittest

from algorithms import ALGORITHMS, astar_steps, bfs_steps, dijkstra_steps, heuristic
from grid import Grid, Tile, get_neighbors


def solve(generator):
    steps = list(generator)
    assert steps and steps[-1].kind == "finish"
    return steps[-1].result, steps


class PathfindingTests(unittest.TestCase):
    def test_adjacent(self):
        grid = Grid(5, 5, start=(2, 2), goal=(2, 3))
        for algorithm in ALGORITHMS.values():
            result, steps = solve(algorithm(grid))
            self.assertTrue(result.found)
            self.assertEqual(result.path_length, 1)
            self.assertEqual(result.path_cost, 1)
            self.assertTrue(all(step.kind in ("expand", "path", "finish") for step in steps))

    def test_empty_map(self):
        grid = Grid(8, 10, start=(0, 0), goal=(7, 9))
        for algorithm in ALGORITHMS.values():
            result, _ = solve(algorithm(grid))
            self.assertEqual(result.path_length, 16)
            self.assertEqual(result.path_cost, 16)

    def test_multiple_paths(self):
        grid = Grid(6, 8, start=(2, 0), goal=(2, 7))
        for r in (1, 2, 3):
            grid.set_tile((r, 3), Tile.WALL)
        for algorithm in ALGORITHMS.values():
            result, _ = solve(algorithm(grid))
            self.assertTrue(result.found)
            self.assertEqual(result.path_length, 11)

    def test_blocked_goal(self):
        grid = Grid(5, 5, start=(0, 0), goal=(2, 2))
        for node in get_neighbors(grid.goal, grid):
            grid.set_tile(node, Tile.WALL)
        for algorithm in ALGORITHMS.values():
            result, _ = solve(algorithm(grid))
            self.assertFalse(result.found)
            self.assertEqual(result.path, ())

    def test_short_expensive_vs_long_cheap(self):
        grid = Grid(3, 5, start=(1, 0), goal=(1, 4))
        for col in (1, 2, 3):
            grid.set_tile((1, col), Tile.WEIGHTED)
        bfs, _ = solve(bfs_steps(grid))
        dijkstra, _ = solve(dijkstra_steps(grid))
        astar, _ = solve(astar_steps(grid))
        self.assertEqual(bfs.path_length, 4)
        self.assertEqual(bfs.path_cost, 16)
        self.assertEqual(dijkstra.path_length, 6)
        self.assertEqual(dijkstra.path_cost, 6)
        self.assertEqual(astar.path_cost, 6)

    def test_distant_points(self):
        grid = Grid(24, 38, start=(0, 0), goal=(23, 37))
        for algorithm in ALGORITHMS.values():
            result, _ = solve(algorithm(grid))
            self.assertTrue(result.found)
            self.assertEqual(result.path_length, 60)

    def test_walls_and_grid_bounds(self):
        grid = Grid(4, 4, start=(0, 0), goal=(3, 3))
        self.assertFalse(grid.set_tile(grid.start, Tile.WALL))
        self.assertFalse(grid.set_tile(grid.goal, Tile.WALL))
        self.assertFalse(grid.set_goal(grid.start))
        self.assertFalse(grid.set_start(grid.goal))
        grid.set_tile((0, 1), Tile.WALL)
        self.assertEqual(get_neighbors((0, 0), grid), [(1, 0)])
        self.assertFalse(grid.set_tile((-1, 0), Tile.WALL))

    def test_change_start_on_weighted_cell(self):
        grid = Grid(4, 4, start=(0, 0), goal=(3, 3))
        grid.set_tile((0, 1), Tile.WEIGHTED)
        self.assertTrue(grid.set_start((0, 1)))
        self.assertEqual(grid.get((0, 1)), Tile.EMPTY)

    def test_demo_map_solvable(self):
        grid = Grid()
        grid.load_demo()
        for algorithm in ALGORITHMS.values():
            result, _ = solve(algorithm(grid))
            self.assertTrue(result.found)
        self.assertEqual(solve(dijkstra_steps(grid))[0].path_cost,
                         solve(astar_steps(grid))[0].path_cost)

    def test_heuristic(self):
        self.assertEqual(heuristic((2, 3), (5, 7)), 7)

    def test_event_is_live_generator(self):
        grid = Grid(3, 3, start=(0, 0), goal=(2, 2))
        generator = bfs_steps(grid)
        first = next(generator)
        self.assertEqual(first.kind, "expand")
        self.assertEqual(first.node, grid.start)
        self.assertEqual(set(first.opened), {(1, 0), (0, 1)})
        self.assertEqual(next(generator).node, (1, 0))


if __name__ == "__main__":
    unittest.main()
