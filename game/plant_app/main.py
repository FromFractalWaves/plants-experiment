import pygame
import sys
import os
from typing import Tuple, Dict

# Add current directory to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from plant_engine import PlantCSpaceEngine, PlantNodeEnhanced
from cspace_engine import Vector2D
from controls import SimulationControls
from effects import EnhancedPlantRenderer, LeafEffect, FlowerEffect, WaterRippleEffect

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BASE_FPS = 60
BG_COLOR = (248, 249, 250)
GRID_COLOR = (221, 221, 221)
BUTTON_COLOR = (76, 175, 80)
HOVER_COLOR = (100, 200, 100)
TEXT_COLOR = (51, 51, 51)
TITLE_FONT_SIZE = 24
NORMAL_FONT_SIZE = 14

class PlantCSpaceVisualizer:
    """Main application class that integrates plant engine and effects"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("C-Space Plants: Geometric Computational Growth")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = BASE_FPS

        # Initialize fonts
        self.title_font = pygame.font.SysFont('Arial', TITLE_FONT_SIZE, bold=True)
        self.normal_font = pygame.font.SysFont('Arial', NORMAL_FONT_SIZE)
        self.math_font = pygame.font.SysFont('Times New Roman', NORMAL_FONT_SIZE, italic=True)

        # State management
        self.state = "control_panel"  # "control_panel" or "simulation"
        self.engine = PlantCSpaceEngine(WIDTH, HEIGHT)
        self.controls = None
        self.params = self.engine.DEFAULT_PARAMS.copy()
        self.resources_to_add = []
        
        # Initialize renderer but don't set it up until simulation starts
        self.plant_renderer = None

    def density_to_color(self, s: float, e: float) -> Tuple[int, int, int]:
        """Convert spatial complexity and energy to a color for visualization"""
        r = int(s * 255)
        g = int((1 - s) * 255)
        b = int(e * 100)
        return (r, g, b)

    def draw_grid(self):
        """Draw a faint grid to visualize space"""
        for x in range(0, WIDTH, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))

    # Control Panel Methods
    def draw_control_panel(self):
        """Draw the initial control panel for simulation setup"""
        self.screen.fill(BG_COLOR)
        self.draw_grid()

        # Draw title
        title = self.title_font.render("Plants as C-Space Navigators", True, TEXT_COLOR)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        
        # Explanation text
        explanation = [
            "This simulation models plants as C-Space navigators through a computational manifold.",
            "Plants navigate geometric space optimizing for resources while minimizing distortion.",
            "",
            "LEFT CLICK: Add light source | RIGHT CLICK: Add obstacle | MIDDLE CLICK: Add water",
            "Key 'S': Add support | 'G': Force growth | 'B': Force branch | 'R': Reset"
        ]
        
        y_offset = 60
        for line in explanation:
            text = self.normal_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_offset))
            y_offset += 25

        # Parameter sliders
        y_offset = 180
        param_labels = [
            ("Max Nodes", "max_nodes", 50, 500, 50),
            ("Growth Rate", "growth_rate", 1.0, 10.0, 1.0),
            ("Growth Probability", "growth_prob", 0.1, 1.0, 0.1),
            ("Branch Probability", "branch_prob", 0.1, 1.0, 0.1),
            ("Energy Distance", "max_energy_distance", 100.0, 300.0, 25.0),
            ("Distortion Threshold", "d_critical", 5.0, 20.0, 1.0),
        ]

        for label, key, min_val, max_val, step in param_labels:
            value = self.params[key]
            text = self.normal_font.render(f"{label}: {value}", True, TEXT_COLOR)
            self.screen.blit(text, (WIDTH // 2 - 150, y_offset))
            
            # Draw - and + buttons
            pygame.draw.rect(self.screen, BUTTON_COLOR, (WIDTH // 2 + 100, y_offset, 30, 20))
            pygame.draw.rect(self.screen, BUTTON_COLOR, (WIDTH // 2 + 140, y_offset, 30, 20))
            self.screen.blit(self.normal_font.render("-", True, (255, 255, 255)), (WIDTH // 2 + 113, y_offset + 2))
            self.screen.blit(self.normal_font.render("+", True, (255, 255, 255)), (WIDTH // 2 + 153, y_offset + 2))
            y_offset += 30

        # Draw resources that will be added to the simulation
        for pos, intensity, r_type in self.resources_to_add:
            pos = (int(pos[0]), int(pos[1]))
            if r_type == 'light':
                pygame.draw.circle(self.screen, (255, 255, 0), pos, 15)
            elif r_type == 'water':
                pygame.draw.circle(self.screen, (0, 191, 255), pos, 10)
            elif r_type == 'support':
                pygame.draw.rect(self.screen, (139, 69, 19), (pos[0] - 2, pos[1] - 10, 4, 20))
            elif r_type == 'obstacle':
                surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 99, 71, 75), (30, 30), 30)
                self.screen.blit(surf, (pos[0] - 30, pos[1] - 30))

        # Draw start button
        pygame.draw.rect(self.screen, BUTTON_COLOR, (WIDTH // 2 - 50, HEIGHT - 60, 100, 40))
        text = self.normal_font.render("Start Simulation", True, (255, 255, 255))
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT - 50))

    def handle_control_panel_events(self, events):
        """Handle events specific to the control panel interface"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                
                # Check parameter buttons
                y_offset = 180
                param_labels = [
                    ("Max Nodes", "max_nodes", 50, 500, 50),
                    ("Growth Rate", "growth_rate", 1.0, 10.0, 1.0),
                    ("Growth Probability", "growth_prob", 0.1, 1.0, 0.1),
                    ("Branch Probability", "branch_prob", 0.1, 1.0, 0.1),
                    ("Energy Distance", "max_energy_distance", 100.0, 300.0, 25.0),
                    ("Distortion Threshold", "d_critical", 5.0, 20.0, 1.0),
                ]
                
                for _, key, min_val, max_val, step in param_labels:
                    if WIDTH // 2 + 100 <= pos[0] <= WIDTH // 2 + 130 and y_offset <= pos[1] <= y_offset + 20:
                        self.params[key] = max(min_val, self.params[key] - step)
                    elif WIDTH // 2 + 140 <= pos[0] <= WIDTH // 2 + 170 and y_offset <= pos[1] <= y_offset + 20:
                        self.params[key] = min(max_val, self.params[key] + step)
                    y_offset += 30

                # Check for resource placement
                if pos[1] < HEIGHT - 70:  # Avoid UI area
                    if event.button == 1:  # Left click: Add light
                        self.resources_to_add.append((pos, 1.0, 'light'))
                    elif event.button == 2:  # Middle click: Add water
                        self.resources_to_add.append((pos, 1.0, 'water'))
                    elif event.button == 3:  # Right click: Add obstacle
                        self.resources_to_add.append((pos, 0.9, 'obstacle'))

                # Check start button
                if WIDTH // 2 - 50 <= pos[0] <= WIDTH // 2 + 50 and HEIGHT - 60 <= pos[1] <= HEIGHT - 20:
                    self.start_simulation()
                    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    # Add support at mouse position
                    pos = pygame.mouse.get_pos()
                    if pos[1] < HEIGHT - 70:  # Avoid UI area
                        self.resources_to_add.append((pos, 0.8, 'support'))
                elif event.key == pygame.K_r:
                    # Clear all resources
                    self.resources_to_add = []
                elif event.key == pygame.K_RETURN:
                    self.start_simulation()

    def start_simulation(self):
        """Start the simulation with the current parameters and resources"""
        self.engine = PlantCSpaceEngine(WIDTH, HEIGHT, self.params)
        self.controls = SimulationControls(self.engine, WIDTH, HEIGHT)
        self.controls.reset_plant()
        
        # Add all pre-configured resources
        for pos, intensity, r_type in self.resources_to_add:
            self.engine.add_resource(pos, intensity, r_type)
        
        # Initialize the enhanced plant renderer
        self.plant_renderer = EnhancedPlantRenderer(self.screen)
        
        # Switch to simulation state
        self.state = "simulation"
        print("Starting simulation with custom parameters")

    def reset_to_control_panel(self):
        """Clear the simulation and return to the control panel"""
        self.engine = PlantCSpaceEngine(WIDTH, HEIGHT)
        self.controls = None
        self.plant_renderer = None
        self.resources_to_add = []
        self.state = "control_panel"

    # Simulation Methods
    def draw_complexity_heatmap(self):
        """Draw the complexity field for visualization"""
        if not self.controls or not self.controls.show_complexity:
            return
            
        cell_size = 20
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        for x in range(0, WIDTH, cell_size):
            for y in range(0, HEIGHT, cell_size):
                pos = Vector2D(x + cell_size / 2, y + cell_size / 2)
                s = self.engine.calculate_spatial_complexity(pos)
                e = self.engine.calculate_energy(pos)
                color = self.density_to_color(s, e)
                pygame.draw.rect(surf, color + (50,), (x, y, cell_size, cell_size))
                
        self.screen.blit(surf, (0, 0))

    def draw_debug_info(self, debug_mode: bool, state: Dict):
        """Draw detailed debug information if enabled"""
        if not debug_mode or not state['nodes']:
            return
            
        # Display information about the oldest (seed) node
        seed_node = state['nodes'][0]
        
        debug_info = [
            f"Time: {state['time']}",
            f"Nodes: {len(state['nodes'])}",
            f"Seed Coherence (H): {seed_node.coherence:.2f}",
            f"Seed Distortion (D): {seed_node.distortion:.2f}",
            f"Seed Energy (E): {seed_node.energy:.2f}",
            f"Seed Temporal (T): {seed_node.temporal_complexity:.2f}",
            f"Seed Spatial (S): {seed_node.spatial_complexity:.2f}",
            f"Seed Water: {getattr(seed_node, 'water_level', 0.0):.2f}"
        ]
        
        # Draw a semi-transparent background for readability
        info_rect = pygame.Rect(10, 10, 250, 15 * len(debug_info) + 10)
        debug_surf = pygame.Surface((info_rect.width, info_rect.height), pygame.SRCALPHA)
        debug_surf.fill((0, 0, 0, 128))
        self.screen.blit(debug_surf, info_rect)
        
        # Render text
        for i, text in enumerate(debug_info):
            text_surf = self.normal_font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (15, 15 + i * 15))

    def draw_ui(self):
        """Draw the simulation UI controls"""
        ui_state = self.controls.get_ui_state()
        
        # Draw the bottom control panel background
        pygame.draw.rect(self.screen, (240, 240, 240), (0, HEIGHT - 50, WIDTH, 50))

        # Draw pause/resume button
        button_color = (76, 175, 80) if ui_state['paused'] else (244, 67, 54)
        pygame.draw.rect(self.screen, button_color, (20, HEIGHT - 40, 80, 30))
        text = self.normal_font.render("Resume" if ui_state['paused'] else "Pause", True, (255, 255, 255))
        self.screen.blit(text, (60 - text.get_width() // 2, HEIGHT - 35))

        # Draw complexity toggle button
        pygame.draw.rect(self.screen, (255, 152, 0), (120, HEIGHT - 40, 120, 30))
        text = self.normal_font.render("Hide Complexity" if ui_state['show_complexity'] else "Show Complexity", True, (255, 255, 255))
        self.screen.blit(text, (180 - text.get_width() // 2, HEIGHT - 35))

        # Draw debug toggle button
        pygame.draw.rect(self.screen, (33, 150, 243), (260, HEIGHT - 40, 80, 30))
        text = self.normal_font.render("Debug Info", True, (255, 255, 255))
        self.screen.blit(text, (300 - text.get_width() // 2, HEIGHT - 35))

        # Draw reset button
        pygame.draw.rect(self.screen, (150, 150, 150), (360, HEIGHT - 40, 80, 30))
        text = self.normal_font.render("Reset", True, (255, 255, 255))
        self.screen.blit(text, (400 - text.get_width() // 2, HEIGHT - 35))

        # Draw simulation info
        info_text = f"Time: {ui_state['time']} | Nodes: {ui_state['node_count']} | Speed: {ui_state['speed']}x"
        text = self.normal_font.render(info_text, True, TEXT_COLOR)
        self.screen.blit(text, (WIDTH - text.get_width() - 10, HEIGHT - 35))

    def run(self):
        """Main application loop"""
        while self.running:
            events = pygame.event.get()

            # Handle common events
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Handle state-specific behavior
            if self.state == "control_panel":
                self.handle_control_panel_events(events)
                self.draw_control_panel()
            elif self.state == "simulation" and self.controls is not None:
                # Handle simulation events
                self.running = self.controls.handle_events(events)
                can_continue = self.controls.update_simulation()

                # Check if simulation is done and reset
                if not can_continue or self.controls.is_done():
                    print("Simulation completed, returning to control panel")
                    self.reset_to_control_panel()

                # Only render simulation if still in simulation state
                if self.state == "simulation":
                    # Clear screen and draw basic elements
                    self.screen.fill(BG_COLOR)
                    self.draw_grid()
                    
                    # Draw complexity map if enabled
                    self.draw_complexity_heatmap()
                    
                    # Get current state for drawing
                    state = self.engine.get_state()
                    
                    # Draw plant with enhanced effects
                    if self.plant_renderer:
                        self.plant_renderer.draw_environment(state['resources'])
                        self.plant_renderer.draw_plant(state['nodes'], state['paths'], self.engine.params)
                    
                    # Draw debug information if enabled
                    self.draw_debug_info(self.controls.debug_mode, state)
                    
                    # Draw UI controls
                    self.draw_ui()
                    
                    # Handle Reset button click
                    for event in events:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            pos = event.pos
                            if 360 <= pos[0] <= 440 and HEIGHT - 40 <= pos[1] <= HEIGHT - 10:
                                print("Resetting simulation")
                                self.reset_to_control_panel()

            # Update display and maintain framerate
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()

if __name__ == "__main__":
    app = PlantCSpaceVisualizer()
    app.run()