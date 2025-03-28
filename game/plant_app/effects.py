import pygame
import math
import random
from typing import Tuple, List, Dict

class LeafEffect:
    """Realistic leaf rendering with simple physics"""
    def __init__(self, position, size=15, color=None, angle=None):
        self.position = position
        self.size = size
        self.color = color or (50, 205, 50)
        self.angle = angle or random.uniform(0, 2 * math.pi)
        self.sway_offset = random.uniform(0, 2 * math.pi)
        self.sway_speed = random.uniform(0.01, 0.05)
        self.scale_factor = random.uniform(0.9, 1.1)
        
    def update(self, time):
        # Gentle swaying motion
        self.angle += math.sin(time * self.sway_speed + self.sway_offset) * 0.01
        
    def draw(self, surface):
        # Create a leaf shape
        leaf_poly = self.create_leaf_shape()
        
        # Rotate the leaf
        rotated_poly = self.rotate_polygon(leaf_poly, self.angle)
        
        # Translate to position
        positioned_poly = [(x + self.position[0], y + self.position[1]) for x, y in rotated_poly]
        
        # Draw leaf
        pygame.draw.polygon(surface, self.color, positioned_poly)
        
        # Draw vein
        vein_points = self.create_vein(positioned_poly)
        if len(vein_points) >= 2:
            pygame.draw.lines(surface, (30, 100, 30), False, vein_points, 1)
    
    def create_leaf_shape(self):
        # Create a more realistic leaf shape
        size = self.size * self.scale_factor
        points = []
        
        # Create a leaf outline with more points for better shape
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            
            # Make the leaf oval-shaped
            r = size * (0.8 + 0.4 * math.sin(angle)**2)
            
            # Add some randomness for natural look
            r *= random.uniform(0.9, 1.1)
            
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            
            points.append((x, y))
            
        return points
    
    def rotate_polygon(self, polygon, angle):
        """Rotate a polygon around the origin"""
        rotated = []
        for x, y in polygon:
            rot_x = x * math.cos(angle) - y * math.sin(angle)
            rot_y = x * math.sin(angle) + y * math.cos(angle)
            rotated.append((rot_x, rot_y))
        return rotated
    
    def create_vein(self, leaf_points):
        """Create a main vein and some side veins"""
        if not leaf_points:
            return []
            
        # Find the top and bottom points of the leaf
        top = min(leaf_points, key=lambda p: p[1])
        bottom = max(leaf_points, key=lambda p: p[1])
        
        # Main vein
        main_vein = [top, bottom]
        
        # Add some side veins
        veins = [main_vein[0]]
        
        center_x = (top[0] + bottom[0]) / 2
        center_y = (top[1] + bottom[1]) / 2
        
        num_side_veins = 3
        for i in range(num_side_veins):
            # Find a point on the leaf edge
            side_point = leaf_points[i * len(leaf_points) // num_side_veins]
            
            # Connect to the main vein
            mid_point = ((center_x + side_point[0]) / 2, (center_y + side_point[1]) / 2)
            veins.append(mid_point)
            veins.append(side_point)
            veins.append(mid_point)
            
        veins.append(main_vein[1])
        return veins


class FlowerEffect:
    """Simple flower rendering"""
    def __init__(self, position, size=10, color=None):
        self.position = position
        self.size = size
        # Choose a flower color if none provided
        self.color = color or random.choice([
            (255, 182, 193),  # Light pink
            (238, 130, 238),  # Violet
            (255, 255, 0),    # Yellow
            (255, 165, 0),    # Orange
            (255, 255, 255),  # White
        ])
        self.center_color = (255, 215, 0)  # Gold center
        self.rotation = random.uniform(0, math.pi/4)
        self.bloom_state = random.uniform(0.5, 1.0)  # How open the flower is
        self.sway_offset = random.uniform(0, 2 * math.pi)
        self.sway_speed = random.uniform(0.005, 0.02)
        
    def update(self, time):
        # Gentle swaying and blooming
        self.rotation += math.sin(time * self.sway_speed + self.sway_offset) * 0.005
        
        # Gradually bloom more
        if self.bloom_state < 1.0:
            self.bloom_state = min(1.0, self.bloom_state + 0.005)
    
    def draw(self, surface):
        x, y = self.position
        # Draw petals
        num_petals = 5
        for i in range(num_petals):
            angle = self.rotation + (i / num_petals) * 2 * math.pi
            
            # Petal position
            petal_distance = self.size * self.bloom_state
            px = x + math.cos(angle) * petal_distance
            py = y + math.sin(angle) * petal_distance
            
            # Draw petal
            petal_size = self.size * 0.8
            pygame.draw.circle(surface, self.color, (int(px), int(py)), int(petal_size))
        
        # Draw flower center
        pygame.draw.circle(surface, self.center_color, (int(x), int(y)), int(self.size * 0.5))


class WaterRippleEffect:
    """Water ripple visual effect"""
    def __init__(self, position, radius=30):
        self.position = position
        self.radius = radius
        self.max_radius = radius
        self.ripples = []
        self.next_ripple_time = 0
    
    def update(self, time):
        # Maybe start a new ripple
        if time > self.next_ripple_time:
            self.ripples.append(0)  # New ripple with 0 radius
            self.next_ripple_time = time + random.uniform(20, 60)  # Next ripple in 20-60 frames
        
        # Update existing ripples
        new_ripples = []
        for radius in self.ripples:
            radius += 0.5  # Expand ripple
            if radius <= self.max_radius * 2:  # Keep until it gets too big
                new_ripples.append(radius)
                
        self.ripples = new_ripples
    
    def draw(self, surface):
        for radius in self.ripples:
            alpha = int(255 * (1 - radius / (self.max_radius * 2)))
            ripple_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                ripple_surface, 
                (100, 180, 255, alpha), 
                (int(radius), int(radius)), 
                max(1, int(radius * 0.1))
            )
            surface.blit(
                ripple_surface, 
                (int(self.position[0] - radius), int(self.position[1] - radius))
            )


class EnhancedPlantRenderer:
    """Enhanced renderer with realistic plant effects"""
    def __init__(self, screen):
        self.screen = screen
        
        # Base colors
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
        
        # Visual effects
        self.leaves = {}      # node_id -> LeafEffect
        self.flowers = {}     # node_id -> FlowerEffect
        self.water_ripples = []  # List of WaterRippleEffect
        
        # Growth animation
        self.node_sizes = {}  # node_id -> current_size
        self.branch_thickness = {}  # (parent_id, child_id) -> thickness
        
        # Time tracking for animations
        self.time = 0
    
    def update(self):
        """Update all animations"""
        self.time += 1
        
        # Update leaves
        for leaf_effect in self.leaves.values():
            leaf_effect.update(self.time)
            
        # Update flowers
        for flower_effect in self.flowers.values():
            flower_effect.update(self.time)
            
        # Update water ripples
        for ripple in self.water_ripples:
            ripple.update(self.time)
    
    def add_leaf(self, node_id, position):
        """Add a leaf to a node"""
        if node_id not in self.leaves:
            leaf_color = random.choice(self.leaf_colors)
            self.leaves[node_id] = LeafEffect(position, color=leaf_color)
    
    def add_flower(self, node_id, position):
        """Add a flower to a node"""
        if node_id not in self.flowers:
            self.flowers[node_id] = FlowerEffect(position)
    
    def add_water_ripple(self, position):
        """Add a water ripple effect"""
        self.water_ripples.append(WaterRippleEffect(position))
    
    def get_stem_thickness(self, node, is_root=False):
        """Calculate stem thickness based on node properties"""
        if is_root:
            return 5
        
        # Thicker stems for older, more established nodes with higher coherence
        base_thickness = 3
        age_factor = min(1.0, node.age / 20)
        coherence_factor = min(1.0, node.coherence)
        
        return max(1, int(base_thickness * (0.5 + 0.5 * (age_factor + coherence_factor) / 2)))
    
    def get_stem_color(self, node):
        """Get stem color based on node properties"""
        # Younger stems are lighter
        if node.age < 5:
            return self.stem_colors[1]
        # Older stems are darker
        elif node.age > 15:
            return self.stem_colors[2]
        # Middle-aged stems
        else:
            return self.stem_colors[0]
    
    def animate_branch_growth(self, parent_id, child_id, target_thickness):
        """Animate branch thickness growth"""
        key = (parent_id, child_id)
        if key not in self.branch_thickness:
            self.branch_thickness[key] = max(1, target_thickness * 0.5)
        elif self.branch_thickness[key] < target_thickness:
            self.branch_thickness[key] = min(target_thickness, self.branch_thickness[key] + 0.2)
        return self.branch_thickness[key]
    
    def animate_node_growth(self, node_id, target_size):
        """Animate node size growth"""
        if node_id not in self.node_sizes:
            self.node_sizes[node_id] = max(1, target_size * 0.5)
        elif self.node_sizes[node_id] < target_size:
            self.node_sizes[node_id] = min(target_size, self.node_sizes[node_id] + 0.2)
        return self.node_sizes[node_id]
    
    def draw_bezier_branch(self, start, end, thickness, color):
        """Draw a bezier curve for a more natural-looking branch"""
        # Calculate control points
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Control point offset (perpendicular to line)
        offset = min(dist * 0.3, 20)
        # Random offset direction
        if not hasattr(self, 'bezier_directions'):
            self.bezier_directions = {}
        
        key = (start, end)
        if key not in self.bezier_directions:
            self.bezier_directions[key] = random.choice([-1, 1])
        
        direction = self.bezier_directions[key]
        
        # Control point
        ctrl_x = start[0] + dx * 0.5 + direction * offset * dy / dist
        ctrl_y = start[1] + dy * 0.5 - direction * offset * dx / dist
        
        # Draw the curve using multiple line segments
        steps = max(int(dist / 5), 10)
        points = []
        
        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier formula
            bx = (1-t)**2 * start[0] + 2*(1-t)*t * ctrl_x + t**2 * end[0]
            by = (1-t)**2 * start[1] + 2*(1-t)*t * ctrl_y + t**2 * end[1]
            points.append((bx, by))
        
        # Draw the curve
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, int(thickness))
    
    def draw_branch(self, start_pos, end_pos, parent_id, child_id, thickness, color):
        """Draw a branch with curved shape and thickness"""
        # Animate thickness
        actual_thickness = self.animate_branch_growth(parent_id, child_id, thickness)
        
        # Draw as a bezier curve
        self.draw_bezier_branch(start_pos, end_pos, actual_thickness, color)
        
        # Add a small circle at the joint for a smoother connection
        pygame.draw.circle(self.screen, color, end_pos, int(actual_thickness / 2))
    
    def draw_node(self, node, is_pure_time, is_singularity):
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
        size = self.animate_node_growth(node.id, target_size)
        
        # Draw node
        pygame.draw.circle(self.screen, color, pos, int(size))
        
        # Maybe add leaf or flower based on node state
        if hasattr(node, 'growth_stage') and node.growth_stage == "mature" and node.energy > 0.7:
            # Add flower to mature high-energy nodes
            if node.id not in self.flowers and random.random() < 0.02:
                self.add_flower(node.id, pos)
        
        if node.coherence > 0.5 and node.age > 5 and node.id not in self.leaves and random.random() < 0.1:
            # Add leaf to stable nodes
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            leaf_pos = (pos[0] + offset_x, pos[1] + offset_y)
            self.add_leaf(node.id, leaf_pos)
    
    def draw_plant(self, nodes, paths, params):
        """Draw the entire plant with enhanced visuals"""
        # Update animations
        self.update()
        
        # First pass: Draw all water ripples
        for ripple in self.water_ripples:
            ripple.draw(self.screen)
        
        # Second pass: Draw all stems from parent to child
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
                    self.draw_branch(start_pos, end_pos, parent.id, child.id, thickness, color)
        
        # Third pass: Draw all leaves 
        for node_id, leaf in self.leaves.items():
            leaf.draw(self.screen)
            
        # Fourth pass: Draw all flowers
        for node_id, flower in self.flowers.items():
            flower.draw(self.screen)
            
        # Fifth pass: Draw all nodes on top
        for node in nodes:
            is_pure_time = node.spatial_complexity < 0.2 and node.energy > 0.7
            is_singularity = node.distortion > params['d_critical']
            self.draw_node(node, is_pure_time, is_singularity)
            
    def draw_environment(self, resources):
        """Draw environmental elements"""
        for resource in resources:
            pos = (int(resource.position.x), int(resource.position.y))
            
            if resource.type == 'light':
                # Draw sun/light with a glow effect
                # Base circle
                pygame.draw.circle(self.screen, (255, 255, 0), pos, 15)
                
                # Glow effect
                glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                for radius in range(25, 5, -5):
                    alpha = 100 - radius * 3
                    pygame.draw.circle(
                        glow_surf, 
                        (255, 255, 0, max(0, alpha)), 
                        (30, 30), 
                        radius
                    )
                self.screen.blit(glow_surf, (pos[0] - 30, pos[1] - 30))
                
            elif resource.type == 'water':
                # Draw water with ripple
                pygame.draw.circle(self.screen, (0, 191, 255), pos, 10)
                
                # Maybe add a new ripple
                if random.random() < 0.005:
                    self.add_water_ripple(pos)
                    
            elif resource.type == 'support':
                # Draw support (like a trellis)
                pygame.draw.rect(
                    self.screen, 
                    (139, 69, 19), 
                    (pos[0] - 2, pos[1] - 10, 4, 20)
                )
                
            elif resource.type == 'obstacle':
                # Semi-transparent obstacle
                surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 99, 71, 75), (30, 30), 30)
                self.screen.blit(surf, (pos[0] - 30, pos[1] - 30))