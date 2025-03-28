import pygame
import random
from typing import Tuple, List
from plant_engine import PlantCSpaceEngine
from cspace_engine import Vector2D

class SimulationControls:
    """Enhanced controls system that works with plant engine and effects"""
    def __init__(self, engine: PlantCSpaceEngine, width: int, height: int):
        self.engine = engine
        self.width = width
        self.height = height
        self.paused = False
        self.show_complexity = True
        self.update_interval = 1  # Steps per frame
        self.update_counter = 0   # Counter for update frequency
        self.debug_mode = False   # Toggle detailed stats

    def reset_plant(self):
        """Reset the plant to its initial state with default resources."""
        # Initialize seed at bottom center
        self.engine.initialize_plant((self.width // 2, self.height - 50))
        
        # Clear resources
        self.engine.resources = []
        
        # Add light sources
        self.engine.add_resource((450, 100), 1.0, 'light')
        self.engine.add_resource((200, 200), 0.8, 'light')
        
        # Add support structures
        for x in [400, 500, 600]:
            for y in range(200, 501, 50):
                self.engine.add_resource((x, y), 0.6, 'support')
        
        # Add obstacles
        self.engine.add_resource((250, 450), 0.9, 'obstacle')
        self.engine.add_resource((350, 400), 0.8, 'obstacle')
        
        # Add water sources
        self.engine.add_resource((150, 500), 1.0, 'water')
        self.engine.add_resource((650, 500), 1.0, 'water')
        
        print("Plant reset with enhanced environment")

    def handle_events(self, events: List[pygame.event.Event]) -> bool:
        """Handle Pygame events and return whether the simulation should continue running."""
        running = True
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                # Handle UI button clicks
                if 20 <= pos[0] <= 100 and self.height - 40 <= pos[1] <= self.height - 10:
                    self.paused = not self.paused
                    print(f"Simulation {'paused' if self.paused else 'resumed'}")
                elif 120 <= pos[0] <= 240 and self.height - 40 <= pos[1] <= self.height - 10:
                    self.show_complexity = not self.show_complexity
                    print(f"Complexity heatmap {'hidden' if not self.show_complexity else 'shown'}")
                elif 260 <= pos[0] <= 340 and self.height - 40 <= pos[1] <= self.height - 10:
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
                # Handle resource creation
                elif event.button == 1 and pos[1] < self.height - 50 and not self.paused:  # Left click: Add light
                    self.engine.add_resource((pos[0], pos[1]), 1.0, 'light')
                    print(f"Added light at ({pos[0]}, {pos[1]})")
                elif event.button == 2 and pos[1] < self.height - 50 and not self.paused:  # Middle click: Add water
                    self.engine.add_resource((pos[0], pos[1]), 1.0, 'water')
                    print(f"Added water at ({pos[0]}, {pos[1]})")
                elif event.button == 3 and pos[1] < self.height - 50 and not self.paused:  # Right click: Add obstacle
                    self.engine.add_resource((pos[0], pos[1]), 0.9, 'obstacle')
                    print(f"Added obstacle at ({pos[0]}, {pos[1]})")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print(f"Simulation {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_r:
                    self.reset_plant()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):  # + or =
                    self.update_interval = min(10, self.update_interval + 1)
                    print(f"Speed increased to {self.update_interval}x")
                elif event.key == pygame.K_MINUS:
                    self.update_interval = max(1, self.update_interval - 1)
                    print(f"Speed decreased to {self.update_interval}x")
                elif event.key == pygame.K_g and not self.paused:
                    self.force_growth()
                elif event.key == pygame.K_b and not self.paused:
                    self.force_branch()
                elif event.key == pygame.K_s:
                    self.toggle_support_at_mouse()
                elif event.key == pygame.K_d:
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
                elif event.key == pygame.K_c:
                    self.show_complexity = not self.show_complexity
                    print(f"Complexity heatmap {'hidden' if not self.show_complexity else 'shown'}")
        return running

    def force_growth(self):
        """Force growth on the most energetic node if possible."""
        if self.engine.nodes and len(self.engine.nodes) < self.engine.params['max_nodes']:
            # Sort by energy to find the most energetic node
            node = max(self.engine.nodes, key=lambda n: n.energy)
            new_growth = self.engine.grow_node(node)
            if new_growth:
                self.engine.nodes.append(new_growth)
                if node.id not in self.engine.paths:
                    self.engine.paths[node.id] = []
                self.engine.paths[node.id].append(new_growth)
                print(f"Forced growth at ({new_growth.position.x:.1f}, {new_growth.position.y:.1f})")

    def force_branch(self):
        """Force branching on a random eligible node if possible."""
        if self.engine.nodes and len(self.engine.nodes) < self.engine.params['max_nodes']:
            # Find nodes eligible for branching
            eligible = [n for n in self.engine.nodes if n.distortion > self.engine.params['d_critical']*0.7 and 
                       n.energy > 0.3 and n.age > 3]
            if eligible:
                node = random.choice(eligible)
                new_branch = self.engine.branch_node(node)
                if new_branch:
                    self.engine.nodes.append(new_branch)
                    if node.id not in self.engine.paths:
                        self.engine.paths[node.id] = []
                    self.engine.paths[node.id].append(new_branch)
                    node.distortion *= 0.5  # Reduce distortion after branching
                    print(f"Forced branch at ({new_branch.position.x:.1f}, {new_branch.position.y:.1f})")

    def toggle_support_at_mouse(self):
        """Add a support structure at the mouse position."""
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[1] < self.height - 50:  # Avoid UI area
            self.engine.add_resource((mouse_pos[0], mouse_pos[1]), 0.8, 'support')
            print(f"Added support structure at ({mouse_pos[0]}, {mouse_pos[1]})")

    def update_simulation(self) -> bool:
        """Update the simulation if not paused, return False if max nodes reached."""
        if not self.paused:
            self.update_counter += 1
            if self.update_counter >= self.update_interval:
                can_continue = self.engine.update()
                self.update_counter = 0
                
                if not can_continue:
                    print(f"Max nodes ({self.engine.params['max_nodes']}) reached at time {self.engine.time}")
                    self.paused = True
                
                # Print periodic status updates
                if self.engine.time % 10 == 0:
                    state = self.engine.get_state()
                    if state['nodes']:
                        seed_node = state['nodes'][0]  # First node is the seed
                        print(f"Time: {state['time']}, Nodes: {len(state['nodes'])}, "
                              f"Seed Coherence: {seed_node.coherence:.2f}, "
                              f"Energy: {seed_node.energy:.2f}")
                
                return can_continue
        return True

    def is_done(self) -> bool:
        """Check if the simulation has reached its end condition."""
        return len(self.engine.nodes) >= self.engine.params['max_nodes']

    def get_ui_state(self) -> dict:
        """Return state for UI rendering."""
        state = self.engine.get_state()
        return {
            'paused': self.paused,
            'show_complexity': self.show_complexity,
            'debug_mode': self.debug_mode,
            'time': state['time'],
            'node_count': len(state['nodes']),
            'speed': self.update_interval
        }