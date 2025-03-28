import pygame
import random
import math
from typing import Tuple, List, Dict


class PlantRenderer:
    """Class for rendering more realistic plant visuals"""
    def __init__(self, screen):
        self.screen = screen
        
        # Plant color palette
        self.stem_colors = [
            (34, 139, 34),    # Forest Green (main stem)
            (60, 179, 113),   # Medium Sea Green (younger stems)
            (46, 139, 87)     # Sea Green (older stems)
        ]
        
        self.leaf_colors = [
            (50, 205, 50),    # Lime Green
            (144, 238, 144),  # Light Green
            (34, 139, 34)     # Forest Green
        ]
        
        # Load textures or create them procedurally
        self.leaf_texture = self._create_leaf_texture()
        self.node_sizes = {}  # Cached node sizes for growth animation
        self.leaves = {}      # Store leaf information

    def _create_leaf_texture(self) -> pygame.Surface:
        """Create a simple leaf texture"""
        size = 15
        leaf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw a simple leaf shape
        points = [
            (size//2, 0),          # Top point
            (size, size//2),       # Right point
            (size//2, size),       # Bottom point
            (0, size//2)           # Left point
        ]
        pygame.draw.polygon(leaf, random.choice(self.leaf_colors), points)
        
        # Add a vein
        pygame.draw.line(leaf, (30, 100, 30), (size//2, 0), (size//2, size), 1)
        
        return leaf

    def get_stem_thickness(self, node: 'PlantNode', is_root: bool = False) -> int:
        """Calculate the stem thickness based on node properties"""
        if is_root:
            return 5
        
        # Thicker stems for older, more established nodes with higher coherence
        base_thickness = 3
        age_factor = min(1.0, node.age / 20)
        coherence_factor = min(1.0, node.coherence)
        
        return max(1, int(base_thickness * (0.5 + 0.5 * (age_factor + coherence_factor) / 2)))

    def get_stem_color(self, node: 'PlantNode') -> Tuple[int, int, int]:
        """Get a stem color based on node properties"""
        # Younger stems are lighter
        if node.age < 5:
            return self.stem_colors[1]
        # Older stems are darker
        elif node.age > 15:
            return self.stem_colors[2]
        # Middle-aged stems
        else:
            return self.stem_colors[0]

    def create_branch_segment(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                             thickness: int, color: Tuple[int, int, int]) -> None:
        """Draw a branch segment with thickness"""
        pygame.draw.line(self.screen, color, start_pos, end_pos, thickness)
        
        # Add a small circle at the joint to create a smoother connection
        pygame.draw.circle(self.screen, color, end_pos, thickness // 2)

    def maybe_add_leaf(self, node: 'PlantNode', node_id: int) -> None:
        """Possibly add a leaf to a node"""
        # Only add leaves to nodes that are at least somewhat stable
        if (node.coherence > 0.5 and node.distortion < 5.0 and 
            node.age > 5 and random.random() < 0.3 and node_id not in self.leaves):
            
            # Determine leaf position and angle
            angle = random.uniform(0, 2 * math.pi)
            distance = random.randint(3, 8)
            leaf_pos = (
                int(node.position.x + math.cos(angle) * distance),
                int(node.position.y + math.sin(angle) * distance)
            )
            
            self.leaves[node_id] = {
                'position': leaf_pos,
                'angle': random.uniform(0, 2 * math.pi),
                'scale': random.uniform(0.8, 1.2),
                'color': random.choice(self.leaf_colors)
            }

    def draw_leaf(self, leaf_data: Dict) -> None:
        """Draw a leaf with the given properties"""
        pos = leaf_data['position']
        angle = leaf_data['angle']
        scale = leaf_data['scale']
        
        # Create a rotated and scaled version of the leaf
        leaf_size = int(15 * scale)
        leaf = pygame.transform.scale(self.leaf_texture, (leaf_size, leaf_size))
        leaf = pygame.transform.rotate(leaf, math.degrees(angle))
        
        # Calculate the position adjustment for rotation
        leaf_rect = leaf.get_rect()
        leaf_rect.center = pos
        
        # Draw the leaf
        self.screen.blit(leaf, leaf_rect)

    def animate_growth(self, node_id: int, size: float) -> None:
        """Store growth animation state for a node"""
        # Start with a small size and grow to the target size
        if node_id not in self.node_sizes:
            self.node_sizes[node_id] = max(1, size * 0.3)
        elif self.node_sizes[node_id] < size:
            self.node_sizes[node_id] = min(size, self.node_sizes[node_id] + 0.3)

    def draw_node(self, node: 'PlantNode', is_pure_time: bool, is_singularity: bool) -> None:
        """Draw a plant node with enhanced visuals"""
        pos = (int(node.position.x), int(node.position.y))
        
        # Determine node appearance based on state
        if is_singularity:
            color = (255, 99, 71)  # Red for singularity
            target_size = 5
        elif is_pure_time:
            color = (65, 105, 225)  # Blue for pure time state
            target_size = 4
        else:
            color = self.get_stem_color(node)
            target_size = 3
            
        # Animate node size
        self.animate_growth(node.id, target_size)
        size = self.node_sizes.get(node.id, target_size)
        
        # Draw node
        pygame.draw.circle(self.screen, color, pos, size)
        
        # Maybe add a leaf
        self.maybe_add_leaf(node, node.id)

    def draw_plant(self, nodes: List['PlantNode'], paths: Dict, params: Dict) -> None:
        """Draw the entire plant with enhanced visuals"""
        # First pass: Draw all stems from parent to child
        for parent_id, children in paths.items():
            parent = next((n for n in nodes if n.id == parent_id), None)
            if parent:
                start_pos = (int(parent.position.x), int(parent.position.y))
                
                # Get parent properties
                is_root = parent.id == 0
                thickness = self.get_stem_thickness(parent, is_root)
                color = self.get_stem_color(parent)
                
                # Draw connections to all children
                for child in children:
                    end_pos = (int(child.position.x), int(child.position.y))
                    self.create_branch_segment(start_pos, end_pos, thickness, color)
        
        # Second pass: Draw all leaves behind nodes
        for node_id, leaf_data in self.leaves.items():
            self.draw_leaf(leaf_data)
            
        # Third pass: Draw all nodes on top
        for node in nodes:
            is_pure_time = node.spatial_complexity < 0.2 and node.energy > 0.7
            is_singularity = node.distortion > params['d_critical']
            self.draw_node(node, is_pure_time, is_singularity)

# Add this method to PlantCSpaceVisualizer class
def initialize_renderer(self):
    self.plant_renderer = PlantRenderer(self.screen)

# Replace the existing draw_plant method with this:
def draw_plant(self):
    state = self.engine.get_state()
    self.plant_renderer.draw_plant(state['nodes'], state['paths'], self.engine.params)