import random
import heapq
from collections import deque

# --- Simulation Constants ---
EMPTY = '.'
TRASH = 'T'
OBSTACLE = '#'
AGENT = 'A'

# --- Algorithmic Helpers ---

def is_map_connected(grid, width, height):
    """Checks if all non-obstacle tiles on the map are connected using BFS."""
    non_obstacle_tiles = []
    start_node = None
    for r in range(height):
        for c in range(width):
            if grid[r][c] != OBSTACLE:
                non_obstacle_tiles.append((r, c))
                if start_node is None:
                    start_node = (r, c)
    if not non_obstacle_tiles: return True
    queue = deque([start_node])
    visited = {start_node}
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width and \
               grid[nr][nc] != OBSTACLE and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return len(visited) == len(non_obstacle_tiles)

def generate_random_map(width, height, num_trash, num_obstacles):
    """Generates a random 2D map."""
    grid = [[EMPTY for _ in range(width)] for _ in range(height)]
    obstacles_placed = 0
    max_retries = width * height * 5
    for _ in range(max_retries):
        if obstacles_placed == num_obstacles: break
        r, c = random.randint(0, height - 1), random.randint(0, width - 1)
        if grid[r][c] == EMPTY:
            grid[r][c] = OBSTACLE
            if not is_map_connected(grid, width, height):
                grid[r][c] = EMPTY
            else:
                obstacles_placed += 1
    
    empty_tiles = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == EMPTY]
    random.shuffle(empty_tiles)
    for i in range(min(num_trash, len(empty_tiles))):
        r, c = empty_tiles[i]
        grid[r][c] = TRASH
    return grid

def a_star_search(grid, start, goal, constraints, start_time=0):
    """Finds the shortest path using A*."""
    height, width = len(grid), len(grid[0])
    def heuristic(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])

    pq = [(heuristic(start, goal), start_time, start)]
    path_info = {(start, start_time): (start_time, None, -1)}
    constraint_set = set(constraints)

    while pq:
        _, time, pos = heapq.heappop(pq)
        if pos == goal:
            path = []
            curr_pos, curr_time = pos, time
            while curr_pos is not None:
                path.append(curr_pos)
                _, prev_pos, prev_time = path_info.get((curr_pos, curr_time), (0, None, -1))
                curr_pos, curr_time = prev_pos, prev_time
            return path[::-1]

        for dr, dc in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_pos = (pos[0] + dr, pos[1] + dc)
            next_time = time + 1

            if not (0 <= neighbor_pos[0] < height and 0 <= neighbor_pos[1] < width and
                    grid[neighbor_pos[0]][neighbor_pos[1]] != OBSTACLE):
                continue
            if (neighbor_pos, next_time) in constraint_set: continue

            if path_info.get((neighbor_pos, next_time), (float('inf'),0,0))[0] > next_time:
                 path_info[(neighbor_pos, next_time)] = (next_time, pos, time)
                 new_f_score = next_time + heuristic(neighbor_pos, goal)
                 heapq.heappush(pq, (new_f_score, next_time, neighbor_pos))
    return None

def find_first_conflict(solution):
    """Finds the first vertex conflict in a set of paths."""
    if not solution: return None
    max_len = max((len(p) for p in solution.values()), default=0)
    for t in range(max_len):
        positions_at_time_t = {}
        for agent_id, path in solution.items():
            pos = path[t] if t < len(path) else path[-1]
            if pos in positions_at_time_t:
                return {'agent1': positions_at_time_t[pos], 'agent2': agent_id, 'pos': pos, 'time': t}
            positions_at_time_t[pos] = agent_id
    return None

def plan_full_path(grid, start_pos, goal_queue, constraints):
    """Plans a complete path for an agent to visit all its goals."""
    if not goal_queue: return [start_pos]
    full_path, current_pos, current_time = [], start_pos, 0
    for goal in goal_queue:
        segment = a_star_search(grid, current_pos, goal, constraints, start_time=current_time)
        if not segment: return None
        full_path.extend(segment if not full_path else segment[1:])
        current_pos, current_time = goal, len(full_path) - 1
    return full_path

def solve_cbs(grid, agents, initial_solution):
    """High-level Conflict-Based Search."""
    open_list = []
    root_constraints = {agent['id']: [] for agent in agents}
    root_cost = sum(len(p) - 1 for p in initial_solution.values())
    heapq.heappush(open_list, (root_cost, root_constraints, initial_solution))
    
    while open_list:
        _cost, constraints, solution = heapq.heappop(open_list)
        conflict = find_first_conflict(solution)
        if not conflict: return solution
        
        for agent_to_constrain_id in [conflict['agent1'], conflict['agent2']]:
            new_constraints = {aid: c[:] for aid, c in constraints.items()}
            new_constraints[agent_to_constrain_id].append((conflict['pos'], conflict['time']))
            
            agent_info = next(a for a in agents if a['id'] == agent_to_constrain_id)
            new_path = plan_full_path(grid, agent_info['pos'], agent_info['goal_queue'], new_constraints[agent_to_constrain_id])
            
            if new_path:
                new_solution = solution.copy()
                new_solution[agent_to_constrain_id] = new_path
                new_cost = sum(len(p) - 1 for p in new_solution.values())
                heapq.heappush(open_list, (new_cost, new_constraints, new_solution))
    return None

def assign_all_tasks(agents, trash_locations, grid):
    """Assigns all trash locations to agents to balance workload."""
    goal_queues = {agent['id']: [] for agent in agents}
    agent_last_pos = {agent['id']: agent['pos'] for agent in agents}
    agent_total_workload = {agent['id']: 0 for agent in agents}
    unassigned_trash = set(trash_locations)

    while unassigned_trash:
        potential_assignments = []
        for agent_id, last_pos in agent_last_pos.items():
            for trash_pos in unassigned_trash:
                path = a_star_search(grid, last_pos, trash_pos, [])
                if path:
                    trip_cost = len(path) - 1
                    adjusted_cost = agent_total_workload[agent_id] + trip_cost
                    potential_assignments.append((adjusted_cost, trip_cost, agent_id, trash_pos))
        
        if not potential_assignments: break
        potential_assignments.sort()
        _adj_cost, trip_cost, agent_id, trash_pos = potential_assignments[0]

        goal_queues[agent_id].append(trash_pos)
        agent_last_pos[agent_id] = trash_pos
        agent_total_workload[agent_id] += trip_cost
        unassigned_trash.remove(trash_pos)
    return goal_queues

# --- Main Simulation Logic Class ---

class SimulationModel:
    def __init__(self):
        self.grid = []
        self.agents = []
        self.final_paths = {}
        self.goal_queues = {}
        self.stats = {}
    
    def generate_grid(self, w, h, trash_count, obstacle_count):
        self.grid = generate_random_map(w, h, trash_count, obstacle_count)
        self.agents = []
        self.final_paths = {}
        self.stats = {}
    
    def update_cell(self, r, c, tool_type):
        """Updates a single cell based on user tool interaction."""
        if not self.grid: return
        if 0 <= r < len(self.grid) and 0 <= c < len(self.grid[0]):
            if self.grid[r][c] == tool_type:
                self.grid[r][c] = EMPTY
            else:
                self.grid[r][c] = tool_type

    def detect_agents_from_grid(self):
        """Scans the grid to populate the agents list."""
        self.agents = []
        agent_id_counter = 0
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == AGENT:
                    self.agents.append({'id': agent_id_counter, 'pos': (r, c)})
                    agent_id_counter += 1
        return self.agents

    def count_items(self):
        """Returns counts of trash, obstacles, and agents."""
        if not self.grid: return 0, 0, 0
        trash = sum(row.count(TRASH) for row in self.grid)
        obstacles = sum(row.count(OBSTACLE) for row in self.grid)
        agents = sum(row.count(AGENT) for row in self.grid)
        return trash, obstacles, agents

    def solve(self):
        """Runs the task assignment and CBS solver."""
        self.detect_agents_from_grid()
        if not self.agents:
            return False, "Error: No agents on the map!"
        
        trash_locations = set((r, c) for r, row in enumerate(self.grid) for c, val in enumerate(row) if val == TRASH)
        if not trash_locations:
            return False, "No trash to collect!"

        self.goal_queues = assign_all_tasks(self.agents, trash_locations, self.grid)
        for agent in self.agents:
            agent['goal_queue'] = self.goal_queues.get(agent['id'], [])

        initial_solution = {}
        for agent in self.agents:
            path = plan_full_path(self.grid, agent['pos'], agent['goal_queue'], [])
            if not path:
                return False, f"Error: No initial path for Agent {agent['id']}."
            initial_solution[agent['id']] = path

        self.final_paths = solve_cbs(self.grid, self.agents, initial_solution)

        if not self.final_paths:
            return False, "CBS failed to find a solution."
        
        # Calculate stats
        sum_of_costs = sum(len(p) - 1 for p in self.final_paths.values())
        makespan = max((len(p) - 1 for p in self.final_paths.values() if p), default=0)
        self.stats = {
            "sum_of_costs": sum_of_costs,
            "makespan": makespan,
            "agent_costs": {aid: len(p) - 1 for aid, p in self.final_paths.items()}
        }
        return True, "Planning complete."

    def get_grid_at_time(self, time_step):
        """Returns the state of the grid (trash status) at a specific time step."""
        temp_grid = [row[:] for row in self.grid]
        for agent in self.agents:
            path = self.final_paths.get(agent['id'])
            if path:
                # Agent clears trash along its path up to time_step
                for t in range(int(time_step) + 1):
                    if t < len(path):
                        pos = path[t]
                        if temp_grid[pos[0]][pos[1]] == TRASH:
                            temp_grid[pos[0]][pos[1]] = EMPTY
        return temp_grid