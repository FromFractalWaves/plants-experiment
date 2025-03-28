from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import math
import random
import numpy as np
from cspace_engine import Vector2D, ResourcePoint

@dataclass
class PlantNodeEnhanced:
    id: int
    position: 'Vector2D'
    energy: float
    coherence: float
    distortion: float
    temporal_complexity: float
    spatial_complexity: float
    parent: Optional[int]
    age: int
    C_t: 'Vector2D' = field(default_factory=lambda: Vector2D(0, 0))  # ETC accumulator
    depth: float = 0.0  # Cycle-depth
    
    # Plant-specific properties
    growth_direction: 'Vector2D' = field(default_factory=lambda: Vector2D(0, -1))  # Default up
    stem_thickness: float = 1.0
    growth_stage: str = "seedling"  # seedling, growing, mature, flowering
    branch_type: str = "main"       # main, lateral, terminal
    water_level: float = 0.5        # Water content affects growth
    leaf_count: int = 0             # Number of leaves on this node
    has_flowered: bool = False      # Whether this node has produced a flower
    
    def update_growth_stage(self):
        """Update the growth stage based on age and other factors"""
        if self.age < 5:
            self.growth_stage = "seedling"
        elif self.age < 15:
            self.growth_stage = "growing"
        elif self.age < 30:
            self.growth_stage = "mature"
        else:
            self.growth_stage = "flowering"
            
    def calculate_stem_thickness(self) -> float:
        """Calculate proper stem thickness based on node properties"""
        base_thickness = 1.0
        age_factor = min(3.0, self.age / 10)
        energy_factor = self.energy * 2
        return base_thickness * (age_factor + energy_factor) / 3


class PlantCSpaceEngine:
    """Extended CSpaceEngine with more plant-like behaviors"""
    def __init__(self, width: int, height: int, params: dict = None):
        self.width = width
        self.height = height
        self.DEFAULT_PARAMS = {
            'alpha': 0.2,              # CMAT tuning parameter
            'beta': 0.3,               # CMAT tuning parameter
            'epsilon': 1e-9,           # Singularity prevention
            'd_critical': 15.0,        # CMAT singularity threshold
            'growth_rate': 5.0,
            'max_energy_distance': 200.0,
            'complexity_gradient_scale': 0.01,
            'max_nodes': 500,
            'growth_prob': 0.3,
            'branch_prob': 0.1,
            'lambda': 0.5,             # Attention decay from CMAT
            
            # Plant-specific parameters
            'tropism_strength': 0.3,    # How strongly plant responds to stimuli
            'phototropism_factor': 1.2, # Light-seeking behavior
            'gravitropism_factor': 0.8, # Gravity response (stems grow up, roots down)
            'water_consumption': 0.01,  # Water consumed per update
            'water_threshold': 0.2,     # Minimum water to grow
            'leaf_energy_contribution': 0.05,  # Energy gained per leaf
            'flower_energy_threshold': 0.8,    # Energy needed to flower
            'branch_angle_variance': 0.4,      # Variation in branching angles
            'leaf_generation_probability': 0.1  # Chance to generate leaf
        }
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self.nodes: List[PlantNodeEnhanced] = []
        self.resources: List[ResourcePoint] = []
        self.paths: Dict[int, List[PlantNodeEnhanced]] = {}
        self.time = 0
        self.children: List['PlantCSpaceEngine'] = []
        
        # Plant-specific tracking
        self.leaf_positions = []
        self.flower_positions = []
        self.total_energy_collected = 0.0
        self.water_sources = []
    
    def add_resource(self, pos: Tuple[float, float], intensity: float, resource_type: str):
        """Add a resource to the environment."""
        self.resources.append(ResourcePoint(Vector2D(pos[0], pos[1]), intensity, resource_type))
    
    def initialize_plant(self, start_pos: Tuple[float, float], initial_energy: float = 0.5):
        """Initialize with a more plant-like structure"""
        seed = PlantNodeEnhanced(
            id=0,
            position=Vector2D(start_pos[0], start_pos[1]),
            energy=initial_energy,
            coherence=1.0,
            distortion=0.0,
            temporal_complexity=0.0,
            spatial_complexity=0.5,
            parent=None,
            age=0,
            branch_type="main",
            water_level=0.8,  # Seeds start with high water content
        )
        self.nodes = [seed]
        self.paths = {}
        self.leaf_positions = []
        self.flower_positions = []
        
        # Add some water sources
        self.water_sources = [
            Vector2D(start_pos[0] - 100, start_pos[1]),
            Vector2D(start_pos[0] + 100, start_pos[1])
        ]
    
    def phototropism_vector(self, pos: 'Vector2D') -> 'Vector2D':
        """Calculate the light-seeking direction vector (phototropism)"""
        direction = Vector2D(0, -1)  # Default up
        weight_sum = 0.0
        
        for resource in self.resources:
            if resource.type == 'light':
                distance = pos.distance(resource.position)
                if distance < self.params['max_energy_distance']:
                    weight = resource.intensity * (1 - distance / self.params['max_energy_distance'])
                    weight_sum += weight
                    to_light = (resource.position - pos).normalize()
                    direction = direction + (to_light * weight)
        
        if weight_sum > 0:
            direction = direction * (1 / (1 + weight_sum))
        
        return direction.normalize()
    
    def gravitropism_vector(self, node: PlantNodeEnhanced) -> 'Vector2D':
        """Calculate the gravity response vector (gravitropism)"""
        # Main stems grow upward, against gravity
        if node.branch_type == "main":
            return Vector2D(0, -self.params['gravitropism_factor'])
        # Lateral branches grow more horizontally
        elif node.branch_type == "lateral":
            return Vector2D(random.choice([-1, 1]) * 0.5, -0.5)
        # Default behavior
        return Vector2D(0, -0.5)
    
    def hydrotropism_vector(self, pos: 'Vector2D') -> 'Vector2D':
        """Calculate water-seeking direction (hydrotropism)"""
        if not self.water_sources:
            return Vector2D(0, 0)
            
        closest_source = min(self.water_sources, key=lambda src: pos.distance(src))
        distance = pos.distance(closest_source)
        
        if distance < 150:
            direction = (closest_source - pos).normalize()
            strength = max(0, 1 - distance / 150)
            return direction * strength
        
        return Vector2D(0, 0)
    
    def calculate_growth_direction(self, node: PlantNodeEnhanced) -> 'Vector2D':
        """Calculate growth direction based on various tropisms"""
        pos = node.position
        
        # Calculate all tropism vectors
        photo_vec = self.phototropism_vector(pos) * self.params['phototropism_factor']
        gravi_vec = self.gravitropism_vector(node)
        hydro_vec = self.hydrotropism_vector(pos)
        
        # Weighted combination based on node needs
        water_need = 1.0 - node.water_level
        energy_need = 1.0 - node.energy
        
        # Combine vectors with weights
        direction = (
            photo_vec * energy_need * 1.5 +
            gravi_vec * 1.0 +
            hydro_vec * water_need * 0.5
        )
        
        # Add randomness for natural variation
        randomness = Vector2D(
            random.uniform(-0.1, 0.1),
            random.uniform(-0.05, 0.05)
        )
        direction = direction + randomness
        
        return direction.normalize()
    
    def calculate_spatial_complexity(self, pos: Vector2D) -> float:
        """Calculate spatial complexity at a given position"""
        complexity = 0.5
        for resource in self.resources:
            distance = pos.distance(resource.position)
            if distance < 100:
                if resource.type == 'obstacle':
                    complexity += resource.intensity * (1 - distance / 100)
                elif resource.type == 'support':
                    complexity -= resource.intensity * (1 - distance / 100) * 0.5
        return max(0.1, min(1.0, complexity))
    
    def calculate_energy(self, pos: Vector2D) -> float:
        """Calculate energy/light level at a given position"""
        energy = 0.3
        for resource in self.resources:
            if resource.type == 'light':
                distance = pos.distance(resource.position)
                if distance < self.params['max_energy_distance']:
                    energy += resource.intensity * (1 - distance / self.params['max_energy_distance']) * 2
        return max(0.1, min(1.5, energy))
    
    def calculate_spatial_gradient(self, pos: Vector2D) -> Vector2D:
        """Calculate gradient of spatial complexity for directional growth"""
        delta = 5.0
        s = self.calculate_spatial_complexity(pos)
        sx = self.calculate_spatial_complexity(Vector2D(pos.x + delta, pos.y))
        sy = self.calculate_spatial_complexity(Vector2D(pos.x, pos.y + delta))
        return Vector2D((sx - s) / delta, (sy - s) / delta)
    
    def update_node_dynamics(self, node):
        """Compatibility with the original CSpaceEngine"""
        pos = node.position
        S = self.calculate_spatial_complexity(pos)
        E = self.calculate_energy(pos)
        
        dD_dH = node.distortion / (node.coherence + self.params['epsilon'])
        gradS = self.calculate_spatial_gradient(pos).magnitude()
        dH = -self.params['alpha'] * (dD_dH + gradS)
        dD = self.params['beta'] * math.log1p(abs(dH) * E)
        dT = self.params['beta'] * math.tanh(abs(dH) * E) * (1 if node.coherence > 0 else -1)
        
        return dH, dD, dT

    def grow_node(self, node: PlantNodeEnhanced) -> Optional[PlantNodeEnhanced]:
        """Enhanced plant-like growth behavior"""
        # Check if the node can grow
        if node.coherence <= 0.1 or node.water_level < self.params['water_threshold']:
            return None
        
        # Update growth stage
        node.update_growth_stage()
        
        # Calculate growth properties
        pos = node.position
        S = self.calculate_spatial_complexity(pos)
        E = self.calculate_energy(pos)
        
        # Calculate growth direction with tropisms
        direction = self.calculate_growth_direction(node)
        
        # Calculate growth length based on energy and age
        growth_factor = E * (1.0 - (min(node.age, 30) / 40))
        growth_length = self.params['growth_rate'] * growth_factor
        
        # Calculate new position
        new_pos = pos + (direction * growth_length)
        
        # Keep within bounds
        new_pos.x = max(0, min(self.width - 1, new_pos.x))
        new_pos.y = max(0, min(self.height - 1, new_pos.y))
        
        # Consume water for growth
        node.water_level -= self.params['water_consumption']
        
        # Create new node
        new_node = PlantNodeEnhanced(
            id=len(self.nodes),
            position=new_pos,
            energy=E,
            coherence=max(0.5, node.coherence * 0.95),
            distortion=node.distortion * 0.7,
            temporal_complexity=node.temporal_complexity + 0.1,
            spatial_complexity=S,
            parent=node.id,
            age=0,
            growth_direction=direction,
            stem_thickness=node.stem_thickness * 0.9,
            branch_type=node.branch_type,
            water_level=node.water_level * 0.9,
        )
        
        # Maybe generate a leaf
        if random.random() < self.params['leaf_generation_probability'] and node.energy > 0.3:
            new_node.leaf_count += 1
            self.leaf_positions.append((new_pos.x, new_pos.y))
            # Leaves contribute to energy
            new_node.energy += self.params['leaf_energy_contribution']
        
        # Check for flowering
        if (node.growth_stage == "mature" and 
            node.energy > self.params['flower_energy_threshold'] and 
            not node.has_flowered and random.random() < 0.05):
            node.has_flowered = True
            self.flower_positions.append((pos.x, pos.y))
            
        return new_node
    
    def branch_node(self, node: PlantNodeEnhanced) -> Optional[PlantNodeEnhanced]:
        """Create a branching pattern more like real plants"""
        if node.distortion <= self.params['d_critical'] * 0.7 or node.energy <= 0.3:
            return None
        
        # Calculate a branching angle
        main_direction = node.growth_direction
        
        # Branches tend to go outward and upward
        branch_angle_base = math.pi / 4  # 45 degrees
        branch_variance = self.params['branch_angle_variance']
        
        # Choose left or right randomly
        side = random.choice([-1, 1])
        branch_angle = branch_angle_base + random.uniform(-branch_variance, branch_variance)
        
        # Calculate the branch direction
        x = main_direction.x * math.cos(branch_angle) - main_direction.y * math.sin(branch_angle * side)
        y = main_direction.x * math.sin(branch_angle * side) + main_direction.y * math.cos(branch_angle)
        branch_direction = Vector2D(x, y).normalize()
        
        # Branch length is smaller than main stem growth
        branch_length = self.params['growth_rate'] * 0.7 * node.energy
        new_pos = node.position + (branch_direction * branch_length)
        
        # Keep within bounds
        new_pos.x = max(0, min(self.width - 1, new_pos.x))
        new_pos.y = max(0, min(self.height - 1, new_pos.y))
        
        # Create branch node
        new_node = PlantNodeEnhanced(
            id=len(self.nodes),
            position=new_pos,
            energy=node.energy * 0.7,
            coherence=1.0,
            distortion=0.0,
            temporal_complexity=node.temporal_complexity + 0.05,
            spatial_complexity=self.calculate_spatial_complexity(new_pos),
            parent=node.id,
            age=0,
            growth_direction=branch_direction,
            stem_thickness=node.stem_thickness * 0.6,
            branch_type="lateral" if node.branch_type == "main" else "terminal",
            water_level=node.water_level * 0.8,
        )
        
        # Branching reduces parent's distortion
        node.distortion *= 0.6
        
        return new_node
    
    def update(self) -> bool:
        """Update with more plant-like behaviors"""
        self.time += 1
        new_nodes = []
        
        # Sort by energy (prioritize energetic nodes)
        active_nodes = sorted(self.nodes, key=lambda n: n.energy, reverse=True)
        max_new_nodes = min(3, self.params['max_nodes'] - len(self.nodes))
        
        # Update each existing node
        for node in active_nodes:
            # Update core CMAT dynamics
            dH, dD, dT = self.update_node_dynamics(node)
            node.coherence = max(0, node.coherence + dH)
            node.distortion = max(0, node.distortion + dD)
            node.temporal_complexity += dT
            node.spatial_complexity = self.calculate_spatial_complexity(node.position)
            node.energy = self.calculate_energy(node.position)
            node.age += 1
            
            # Plant-specific updates
            node.update_growth_stage()
            node.stem_thickness = node.calculate_stem_thickness()
            
            # Water level decreases over time, faster in high energy (sunlight) areas
            node.water_level = max(0.1, node.water_level - self.params['water_consumption'] * (1 + node.energy * 0.5))
            
            # Receive water from water sources if nearby
            for water_source in self.water_sources:
                distance = node.position.distance(water_source)
                if distance < 100:
                    water_gain = 0.05 * (1 - distance / 100)
                    node.water_level = min(1.0, node.water_level + water_gain)
            
            # Energy contribution from leaves
            node.energy += node.leaf_count * self.params['leaf_energy_contribution']
            
            # Add node to new list
            new_nodes.append(node)
        
        # Growth and branching phase
        new_count = 0
        random.shuffle(active_nodes)  # Randomize to avoid bias
        
        for node in active_nodes:
            if new_count >= max_new_nodes:
                break
                
            # Growth is more likely in young nodes with good water and energy
            growth_probability = self.params['growth_prob'] * node.water_level * node.energy
            if node.age > 30:
                growth_probability *= 0.5  # Older nodes grow less
                
            if random.random() < growth_probability:
                new_growth = self.grow_node(node)
                if new_growth and len(new_nodes) < self.params['max_nodes']:
                    new_nodes.append(new_growth)
                    if node.id not in self.paths:
                        self.paths[node.id] = []
                    self.paths[node.id].append(new_growth)
                    new_count += 1
            
            # Branching is more likely in mature nodes
            branch_probability = self.params['branch_prob']
            if 10 <= node.age <= 25:
                branch_probability *= 1.5  # Middle-aged nodes branch more
                
            if random.random() < branch_probability and node.energy > 0.4:
                new_branch = self.branch_node(node)
                if new_branch and len(new_nodes) < self.params['max_nodes']:
                    new_nodes.append(new_branch)
                    if node.id not in self.paths:
                        self.paths[node.id] = []
                    self.paths[node.id].append(new_branch)
                    new_count += 1
        
        self.nodes = new_nodes[:self.params['max_nodes']]
        return len(self.nodes) < self.params['max_nodes']
    
    def get_state(self):
        state = {
            'nodes': self.nodes,
            'resources': self.resources,
            'paths': self.paths,
            'time': self.time,
            'children': [child.get_state() for child in self.children],
            'leaf_positions': self.leaf_positions,
            'flower_positions': self.flower_positions,
            'water_sources': self.water_sources
        }
        return state