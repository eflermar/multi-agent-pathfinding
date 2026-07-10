import pygame
import time
from simulation_core import SimulationModel, EMPTY, TRASH, OBSTACLE, AGENT

# --- Pygame and UI Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 720
GRID_AREA_WIDTH = 720
UI_PANEL_WIDTH = SCREEN_WIDTH - GRID_AREA_WIDTH
FONT_SIZE_LARGE = 38
FONT_SIZE_MEDIUM = 26
FONT_SIZE_SMALL = 20
FONT_NAME = "Consolas, dejavusansmono, monospace"

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRID_LINES = (200, 200, 200)
COLOR_EMPTY = (255, 255, 255)
COLOR_OBSTACLE = (80, 80, 80)
COLOR_TRASH = (255, 223, 0)
COLOR_AGENT = [(65, 105, 225), (60, 179, 113), (255, 69, 0), (148, 0, 211)]
COLOR_PATH = [(173, 216, 230, 0), (144, 238, 144, 0), (255, 182, 193, 0), (221, 160, 221, 0)]

# Button Colors
COLOR_BUTTON = (0, 122, 204)
COLOR_BUTTON_HOVER = (50, 152, 224)
COLOR_BUTTON_DISABLED = (150, 150, 150)
COLOR_BUTTON_TEXT = (255, 255, 255)

# --- UI Classes ---

class Button:
    def __init__(self, x, y, width, height, text, font, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.enabled = enabled
        self.hovered = False

    def draw(self, screen):
        color = COLOR_BUTTON_DISABLED
        if self.enabled:
            color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, COLOR_BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if not self.enabled: return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            return True
        return False

class TextInput:
    def __init__(self, x, y, width, height, font, initial_text="", numeric=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = initial_text
        self.numeric = numeric
        self.active = False
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                char = event.unicode
                if not self.numeric or char.isdigit():
                    self.text += char

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)
        text_surface = self.font.render(self.text, True, COLOR_BLACK)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
    def get_value(self, default=0):
        try: return int(self.text)
        except ValueError: return default

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val, self.max_val = min_val, max_val
        self.val = initial_val
        self.handle_rect = pygame.Rect(0, 0, 10, h + 6)
        self.update_handle_pos()
        self.dragging = False

    def update_handle_pos(self):
        percent = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.x + percent * self.rect.w
        self.handle_rect.centery = self.rect.centery
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and (self.rect.collidepoint(event.pos) or self.handle_rect.collidepoint(event.pos)):
            self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            percent = (event.pos[0] - self.rect.x) / self.rect.w
            percent = max(0, min(1, percent))
            self.val = self.min_val + percent * (self.max_val - self.min_val)
            self.update_handle_pos()

    def draw(self, screen):
        pygame.draw.rect(screen, (200, 200, 200), self.rect, border_radius=4)
        pygame.draw.rect(screen, COLOR_BUTTON, self.handle_rect, border_radius=4)

# --- Drawing Helpers ---

def get_tile_size(grid):
    if not grid: return 0
    h, w = len(grid), len(grid[0])
    return min(GRID_AREA_WIDTH // w, SCREEN_HEIGHT // h)

def draw_text(screen, text, font, position, color=COLOR_BLACK):
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, position)

def draw_grid(screen, grid, tile_size):
    """Draws the main simulation grid."""
    if not grid: return
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            rect = pygame.Rect(c * tile_size, r * tile_size, tile_size, tile_size)
            cell_type = grid[r][c]
            color = COLOR_EMPTY
            if cell_type == OBSTACLE: color = COLOR_OBSTACLE
            elif cell_type == TRASH: color = COLOR_TRASH
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLOR_GRID_LINES, rect, 1)

def draw_config_agents(screen, grid, tile_size):
    """Draws agents found in the grid during the config phase."""
    if not grid: return
    agent_id_counter = 0
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == AGENT:
                color = COLOR_AGENT[agent_id_counter % len(COLOR_AGENT)]
                center = (int(c * tile_size + tile_size / 2), int(r * tile_size + tile_size / 2))
                radius = int(tile_size / 2 * 0.8)
                pygame.draw.circle(screen, color, center, radius)
                agent_id_counter += 1

def draw_paths(screen, paths, tile_size, faint=False):
    """Draws planned paths."""
    if not paths: return
    path_surf = pygame.Surface((GRID_AREA_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for agent_id, path in paths.items():
        color = list(COLOR_PATH[agent_id % len(COLOR_PATH)])
        color[3] = 60 if faint else 255
        width = 2 if faint else 4
        if len(path) > 1:
            points = [(p[1] * tile_size + tile_size / 2, p[0] * tile_size + tile_size / 2) for p in path]
            pygame.draw.lines(path_surf, color, False, points, width=width)
    screen.blit(path_surf, (0, 0))

def draw_static_agents(screen, agents, tile_size):
    for agent in agents:
        agent_id, pos = agent['id'], agent['pos']
        color = COLOR_AGENT[agent_id % len(COLOR_AGENT)]
        center = (int(pos[1] * tile_size + tile_size / 2), int(pos[0] * tile_size + tile_size / 2))
        radius = int(tile_size / 2 * 0.8)
        pygame.draw.circle(screen, color, center, radius)

def draw_animated_agents(screen, agents, paths, anim_time, tile_size):
    for agent in agents:
        agent_id, color = agent['id'], COLOR_AGENT[agent['id'] % len(COLOR_AGENT)]
        path = paths.get(agent_id)
        if not path: continue
        
        current_step = int(anim_time)
        progress = anim_time - current_step
        pos1 = path[current_step] if current_step < len(path) else path[-1]
        pos2 = path[current_step + 1] if current_step + 1 < len(path) else pos1
        
        x1, y1 = pos1[1] * tile_size, pos1[0] * tile_size
        x2, y2 = pos2[1] * tile_size, pos2[0] * tile_size
        interp_x = x1 * (1 - progress) + x2 * progress
        interp_y = y1 * (1 - progress) + y2 * progress

        center = (int(interp_x + tile_size / 2), int(interp_y + tile_size / 2))
        radius = int(tile_size / 2 * 0.8)
        pygame.draw.circle(screen, color, center, radius)

def draw_hover_details(screen, agent_id, goal_queues, paths, font, tile_size):
    if agent_id is None: return
    
    path = paths.get(agent_id)
    if path and len(path) > 1:
        color = COLOR_AGENT[agent_id % len(COLOR_AGENT)]
        points = [(p[1] * tile_size + tile_size / 2, p[0] * tile_size + tile_size / 2) for p in path]
        pygame.draw.lines(screen, color, False, points, width=5)
        
    goals = goal_queues.get(agent_id, [])
    color = COLOR_AGENT[agent_id % len(COLOR_AGENT)]
    for i, (r, c) in enumerate(goals):
        rect = pygame.Rect(c * tile_size, r * tile_size, tile_size, tile_size)
        highlight_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        highlight_surf.fill((color[0], color[1], color[2], 128))
        screen.blit(highlight_surf, rect.topleft)
        pygame.draw.rect(screen, color, rect, 3)

        order_text = font.render(str(i + 1), True, COLOR_WHITE)
        text_rect = order_text.get_rect(center=rect.center)
        pygame.draw.circle(screen, color, text_rect.center, radius=int(tile_size/3))
        screen.blit(order_text, text_rect)

# --- Main Application Class ---
class SimulationApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Interactive Trash Collection Simulation")
        self.clock = pygame.time.Clock()
        self.font_l = pygame.font.SysFont(FONT_NAME, FONT_SIZE_LARGE, bold=True)
        self.font_m = pygame.font.SysFont(FONT_NAME, FONT_SIZE_MEDIUM)
        self.font_s = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        
        # Initialize Logic Model
        self.model = SimulationModel()
        
        self.setup_config_state()
        self.running = True

    def setup_config_state(self):
        """Initial state for setting up the simulation parameters."""
        # Reset the underlying simulation model so old stats/paths disappear
        self.model = SimulationModel()

        self.game_state = "CONFIG"
        self.animation_time = 0
        self.status_message = "Configure the grid and click 'Generate Grid'."
        self.selected_tool = OBSTACLE
        self.hovered_agent_id = None
        self.is_paused = False
        self.animation_speed = 2.5
        self.anim_grid_state = [] # Local state for visualization only

        # UI Elements
        self.inputs = {
            "width": TextInput(GRID_AREA_WIDTH + 230, 50, 100, 30, self.font_m, "15"),
            "height": TextInput(GRID_AREA_WIDTH + 230, 90, 100, 30, self.font_m, "15"),
            "trash": TextInput(GRID_AREA_WIDTH + 230, 130, 100, 30, self.font_m, "10"),
            "obstacles": TextInput(GRID_AREA_WIDTH + 230, 170, 100, 30, self.font_m, "20"),
            "agents": TextInput(GRID_AREA_WIDTH + 230, 210, 100, 30, self.font_m, "3"),
        }
        self.buttons = {
            "generate": Button(GRID_AREA_WIDTH + 40, 260, 340, 40, "Generate Grid", self.font_m),
            "tool_obstacle": Button(GRID_AREA_WIDTH + 40, 320, 165, 30, "Obstacle", self.font_s),
            "tool_trash": Button(GRID_AREA_WIDTH + 215, 320, 165, 30, "Trash", self.font_s),
            "tool_agent": Button(GRID_AREA_WIDTH + 40, 360, 165, 30, "Agent", self.font_s),
            "tool_empty": Button(GRID_AREA_WIDTH + 215, 360, 165, 30, "Eraser", self.font_s),
            "solve": Button(GRID_AREA_WIDTH + 40, 410, 340, 40, "Plan Paths", self.font_m, enabled=False),
            "execute": Button(GRID_AREA_WIDTH + 40, 460, 340, 40, "Execute Plan", self.font_m, enabled=False),
            "play_pause": Button(GRID_AREA_WIDTH + 40, 510, 165, 30, "Pause", self.font_s),
            "reset": Button(GRID_AREA_WIDTH + 40, 670, 340, 40, "Reset", self.font_m),
        }
        self.speed_slider = Slider(GRID_AREA_WIDTH + 215, 510, 165, 15, 0.5, 50.0, self.animation_speed)

    def handle_events(self):
        """Handles all user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False

            if self.game_state == "CONFIG":
                for key in self.inputs: self.inputs[key].handle_event(event)
            elif self.game_state in ["EXECUTING", "FINISHED"]:
                self.speed_slider.handle_event(event)
                self.animation_speed = self.speed_slider.val

            if self.buttons["generate"].handle_event(event): self.action_generate_grid()
            if self.buttons["tool_obstacle"].handle_event(event): self.selected_tool = OBSTACLE
            if self.buttons["tool_trash"].handle_event(event): self.selected_tool = TRASH
            if self.buttons["tool_agent"].handle_event(event): self.selected_tool = AGENT
            if self.buttons["tool_empty"].handle_event(event): self.selected_tool = EMPTY
            if self.buttons["solve"].handle_event(event): self.action_solve()
            if self.buttons["execute"].handle_event(event): self.action_execute()
            if self.buttons["reset"].handle_event(event): self.setup_config_state()
            if self.game_state in ["EXECUTING", "FINISHED"] and self.buttons["play_pause"].handle_event(event):
                self.toggle_pause()

            # Handle Grid Clicks (Editing)
            if self.game_state == "CONFIG" and event.type == pygame.MOUSEBUTTONDOWN and self.model.grid:
                mx, my = event.pos
                tile_size = get_tile_size(self.model.grid)
                if mx < GRID_AREA_WIDTH and tile_size > 0:
                    c, r = mx // tile_size, my // tile_size
                    self.model.update_cell(r, c, self.selected_tool)
                    self.update_counts_from_grid()
                    self.anim_grid_state = [row[:] for row in self.model.grid]

            # Handle Grid Hover (Tooltips)
            if self.game_state == "PLANNED" and event.type == pygame.MOUSEMOTION and self.model.grid:
                mx, my = event.pos
                tile_size = get_tile_size(self.model.grid)
                self.hovered_agent_id = None
                if mx < GRID_AREA_WIDTH and tile_size > 0:
                    c, r = mx // tile_size, my // tile_size
                    for agent in self.model.agents:
                        if agent['pos'] == (r, c): self.hovered_agent_id = agent['id']

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.buttons["play_pause"].text = "Play" if self.is_paused else "Pause"

    def update_counts_from_grid(self):
        t, o, a = self.model.count_items()
        self.inputs['trash'].text = str(t)
        self.inputs['obstacles'].text = str(o)
        self.inputs['agents'].text = str(a)

    def action_generate_grid(self):
        w = self.inputs["width"].get_value(10)
        h = self.inputs["height"].get_value(10)
        trash = self.inputs["trash"].get_value(5)
        obstacles = self.inputs["obstacles"].get_value(10)
        
        self.model.generate_grid(w, h, trash, obstacles)
        self.anim_grid_state = [row[:] for row in self.model.grid]
        
        self.buttons["solve"].enabled, self.buttons["execute"].enabled = True, False
        self.status_message = "Grid generated. Edit or click 'Plan Paths'."
        self.game_state = "CONFIG"
        self.update_counts_from_grid()

    def action_solve(self):
        if not self.model.grid: return
        self.status_message = "Planning... This might take a moment."
        self.draw()
        pygame.display.flip()

        success, message = self.model.solve()
        self.status_message = message

        if success:
            self.game_state = "PLANNED"
            self.buttons["execute"].enabled, self.buttons["solve"].enabled, self.buttons["generate"].enabled = True, False, False

    def action_execute(self):
        self.game_state = "EXECUTING"
        self.animation_time = 0
        self.buttons["execute"].enabled = False
        self.is_paused = False
        self.buttons['play_pause'].text = "Pause"
        self.status_message = "Execution in progress..."

    def update(self, dt):
        """Update the simulation state for animations."""
        if self.game_state == "EXECUTING" and self.model.final_paths and not self.is_paused:
            self.animation_time += dt * self.animation_speed
            makespan = self.model.stats.get('makespan', 0)

            # Retrieve grid state from the logic model for the current time
            self.anim_grid_state = self.model.get_grid_at_time(self.animation_time)
            
            if self.animation_time >= makespan and makespan > 0:
                self.game_state = "FINISHED"
                self.status_message = f"Execution finished in {makespan} steps."

    def draw_ui_panel(self):
        """Draws the right-hand UI panel."""
        pygame.draw.rect(self.screen, (240, 240, 240), (GRID_AREA_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT))
        draw_text(self.screen, "Controls", self.font_l, (GRID_AREA_WIDTH + 20, 10))
        if self.game_state == "CONFIG":
            labels = ["Grid Width:", "Grid Height:", "Num Trash:", "Num Obstacles:", "Num Agents:"]
            inputs_keys = ["width", "height", "trash", "obstacles", "agents"]
            for i, (label, key) in enumerate(zip(labels, inputs_keys)):
                draw_text(self.screen, label, self.font_m, (GRID_AREA_WIDTH + 40, 55 + i * 40))
                self.inputs[key].draw(self.screen)

        # Base y-position for status messages (kept clear of buttons)
        status_y = 600

        # Draw plan statistics (only in non-config states) higher up,
        # where the config inputs were, so they never collide with buttons.
        if self.model.stats and self.game_state in ["PLANNED", "EXECUTING", "FINISHED"]:
            start_y = 70
            draw_text(self.screen, "Plan Statistics", self.font_m, (GRID_AREA_WIDTH + 20, start_y))
            stats = self.model.stats
            draw_text(self.screen, f"Total Steps: {stats['sum_of_costs']}", self.font_s, (GRID_AREA_WIDTH + 25, start_y + 30))
            draw_text(self.screen, f"Makespan: {stats['makespan']}", self.font_s, (GRID_AREA_WIDTH + 25, start_y + 50))
            for i, (agent_id, cost) in enumerate(stats.get('agent_costs', {}).items()):
                color = COLOR_AGENT[agent_id % len(COLOR_AGENT)]
                draw_text(self.screen, f"Agent {agent_id}: {cost} steps", self.font_s, (GRID_AREA_WIDTH + 30, start_y + 75 + i * 20), color)
        
        for i, line in enumerate(self.status_message.split('\n')):
            draw_text(self.screen, line, self.font_s, (GRID_AREA_WIDTH + 20, status_y + i * 20), (50, 50, 50))

        # Draw buttons and slider on top so text does not overlap them
        for name, btn in self.buttons.items():
            if name == "play_pause" and self.game_state not in ["EXECUTING", "FINISHED"]:
                continue
            btn.draw(self.screen)

        if self.game_state in ["EXECUTING", "FINISHED"]:
            self.speed_slider.draw(self.screen)
            speed_text = f"{self.animation_speed:.1f}x"
            draw_text(self.screen, speed_text, self.font_s, (self.speed_slider.rect.right - 40, self.speed_slider.rect.y + 18))

        if self.game_state == "CONFIG":
            tool_map = {OBSTACLE: "tool_obstacle", TRASH: "tool_trash", AGENT: "tool_agent", EMPTY: "tool_empty"}
            pygame.draw.rect(self.screen, COLOR_BLACK, self.buttons[tool_map[self.selected_tool]].rect, 2, border_radius=8)

    def draw(self):
        """Main drawing function."""
        self.screen.fill(COLOR_WHITE)
        
        tile_size = get_tile_size(self.model.grid)
        
        if self.model.grid:
            draw_grid(self.screen, self.anim_grid_state, tile_size)
            if self.game_state == "CONFIG":
                draw_config_agents(self.screen, self.model.grid, tile_size)
            elif self.game_state == "PLANNED":
                draw_paths(self.screen, self.model.final_paths, tile_size, faint=True)
                draw_static_agents(self.screen, self.model.agents, tile_size)
                draw_hover_details(self.screen, self.hovered_agent_id, self.model.goal_queues, self.model.final_paths, self.font_s, tile_size)
            elif self.game_state in ["EXECUTING", "FINISHED"]:
                draw_animated_agents(self.screen, self.model.agents, self.model.final_paths, self.animation_time, tile_size)
        
        self.draw_ui_panel()
        pygame.display.flip()

    def run(self):
        """The main loop of the application."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == '__main__':
    app = SimulationApp()
    app.run()