import math
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

DEFAULT_PARAMS = {
    'alpha': 0.2,              # CMAT tuning parameter
    'beta': 0.3,               # CMAT tuning parameter
    'epsilon': 1e-9,           # Singularity prevention
    'd_critical': 15.0,        # CMAT singularity threshold (up from 2.0)
    'growth_rate': 5.0,
    'max_energy_distance': 200.0,
    'complexity_gradient_scale': 0.01,
    'max_nodes': 500,          # Increased for more complexity
    'growth_prob': 0.3,
    'branch_prob': 0.1,
    'lambda': 0.5,             # Attention decay from CMAT
}

@dataclass
class Vector2D:
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar):
        # Handle scalar * Vector2D by delegating to __mul__
        return self.__mul__(scalar)
    
    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        return Vector2D(self.x / mag, self.y / mag) if mag > 0 else Vector2D(0, -1)

@dataclass
class ResourcePoint:
    position: Vector2D
    intensity: float
    type: str

@dataclass
class PlantNode:
    id: int
    position: Vector2D
    energy: float
    coherence: float
    distortion: float
    temporal_complexity: float
    spatial_complexity: float
    parent: Optional[int]
    age: int
    C_t: Vector2D = field(default_factory=lambda: Vector2D(0, 0))  # ETC accumulator
    depth: float = 0.0  # Cycle-depth

class CSpaceEngine:
    def __init__(self, width: int, height: int, params: dict = None):
        self.width = width
        self.height = height
        self.params = {**DEFAULT_PARAMS, **(params or {})}
        self.nodes: List[PlantNode] = []
        self.resources: List[ResourcePoint] = []
        self.paths: dict = {}
        self.time = 0
        self.children: List['CSpaceEngine'] = []  # Hierarchical infinity layers

    def initialize_plant(self, start_pos: Tuple[float, float], initial_energy: float = 0.5):
        seed = PlantNode(
            id=0,
            position=Vector2D(start_pos[0], start_pos[1]),
            energy=initial_energy,
            coherence=1.0,
            distortion=0.0,
            temporal_complexity=0.0,
            spatial_complexity=0.5,
            parent=None,
            age=0
        )
        self.nodes = [seed]
        self.paths = {}

    def add_resource(self, pos: Tuple[float, float], intensity: float, resource_type: str):
        self.resources.append(ResourcePoint(Vector2D(pos[0], pos[1]), intensity, resource_type))

    def metric_tensor(self, node: PlantNode) -> np.ndarray:
        """CMAT metric tensor g = [[1/E^2, 0], [0, 1/(D + ε)]]."""
        return np.diag([1 / (node.energy**2), 1 / (node.distortion + self.params['epsilon'])])

    def calculate_spatial_complexity(self, pos: Vector2D) -> float:
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
        energy = 0.3
        for resource in self.resources:
            if resource.type == 'light':
                distance = pos.distance(resource.position)
                if distance < self.params['max_energy_distance']:
                    energy += resource.intensity * (1 - distance / self.params['max_energy_distance']) * 2
        return max(0.1, min(1.5, energy))

    def calculate_spatial_gradient(self, pos: Vector2D) -> Vector2D:
        delta = 5.0
        s = self.calculate_spatial_complexity(pos)
        sx = self.calculate_spatial_complexity(Vector2D(pos.x + delta, pos.y))
        sy = self.calculate_spatial_complexity(Vector2D(pos.x, pos.y + delta))
        return Vector2D((sx - s) / delta, (sy - s) / delta)

    def complex_density(self, node: PlantNode) -> float:
        """CMAT ρ_c = √(S^2 + T^2) * E, or T * E in pure time state."""
        S = node.spatial_complexity
        return node.temporal_complexity * node.energy if S < 0.1 else math.sqrt(S**2 + node.temporal_complexity**2) * node.energy

    def compute_attention(self, node: PlantNode) -> Vector2D:
        """CMAT manifold attention A for growth direction."""
        attentions = []
        for resource in self.resources:
            dist = node.position.distance(resource.position)
            rho_c = self.complex_density(node)
            g11 = 1 / (node.energy**2)
            exp_term = math.exp(-self.params['lambda'] * dist * g11 / (rho_c + self.params['epsilon']))
            weight = exp_term * (node.coherence / max(node.distortion, self.params['epsilon']))
            direction = (resource.position - node.position).normalize()
            attentions.append((weight, direction))
        total_weight = sum(w for w, _ in attentions) or 1e-9  # Avoid division by zero
        # Fix: Use Vector2D(0, 0) as the initial value for sum
        direction = sum(((w / total_weight) * d for w, d in attentions if w > 0), Vector2D(0, 0)) or Vector2D(0, -1)
        return direction

    def update_node_dynamics(self, node: PlantNode) -> Tuple[float, float, float]:
        """CMAT perpendicular dynamics for H, D, and T."""
        pos = node.position
        S = self.calculate_spatial_complexity(pos)
        E = self.calculate_energy(pos)
        gradient = self.calculate_spatial_gradient(pos)
        
        dD_dH = node.distortion / (node.coherence + self.params['epsilon'])
        gradS = gradient.magnitude()
        dH = -self.params['alpha'] * (dD_dH + gradS)  # CMAT dH/dt
        dD = self.params['beta'] * math.log1p(abs(dH) * E)  # CMAT dD/dt
        dT = self.params['beta'] * math.tanh(abs(dH) * E) * (1 if node.coherence > 0 else -1)  # CMAT dT/dt
        
        return dH, dD, dT

    def grow_node(self, node: PlantNode) -> Optional[PlantNode]:
        if node.coherence <= 0.1 or node.age >= 20:
            return None

        pos = node.position
        S = self.calculate_spatial_complexity(pos)
        E = self.calculate_energy(pos)
        
        # Use manifold attention for growth direction
        direction = self.compute_attention(node)
        growth = self.params['growth_rate'] * (0.5 + E)
        new_pos = pos + (direction * growth)
        new_pos.x = max(0, min(self.width - 1, new_pos.x))
        new_pos.y = max(0, min(self.height - 1, new_pos.y))

        # ETC: Accumulate position history
        node.C_t = node.C_t + node.position

        new_node = PlantNode(
            id=len(self.nodes),
            position=new_pos,
            energy=E,
            coherence=max(0.5, node.coherence * 0.9),
            distortion=node.distortion * 0.5,
            temporal_complexity=math.log(node.C_t.magnitude() + self.params['epsilon']),  # ETC T_t
            spatial_complexity=S,
            parent=node.id,
            age=0
        )

        # Cycle-depth: Measure bearing after 2π-like step
        d_vec = np.array([new_node.coherence - node.coherence, new_node.temporal_complexity - node.temporal_complexity])
        g = self.metric_tensor(node)
        node.depth += math.sqrt(d_vec.T @ g @ d_vec)

        return new_node

    def branch_node(self, node: PlantNode) -> Optional[PlantNode]:
        if node.distortion <= self.params['d_critical'] or node.energy <= 0.2 or node.age <= 3:
            return None

        E = self.calculate_energy(node.position)
        S = self.calculate_spatial_complexity(node.position)
        angle = random.uniform(0, 2 * math.pi)
        distance = self.params['growth_rate'] * (0.5 + E)
        new_pos = node.position + Vector2D(math.cos(angle) * distance, math.sin(angle) * distance)
        new_pos.x = max(0, min(self.width - 1, new_pos.x))
        new_pos.y = max(0, min(self.height - 1, new_pos.y))

        # ETC for branching node
        node.C_t = node.C_t + node.position

        new_node = PlantNode(
            id=len(self.nodes),
            position=new_pos,
            energy=E,
            coherence=1.0,
            distortion=0.0,
            temporal_complexity=math.log(node.C_t.magnitude() + self.params['epsilon']),
            spatial_complexity=S,
            parent=node.id,
            age=0
        )

        # Cycle-depth for branching
        d_vec = np.array([new_node.coherence - node.coherence, new_node.temporal_complexity - node.temporal_complexity])
        g = self.metric_tensor(node)
        node.depth += math.sqrt(d_vec.T @ g @ d_vec)

        return new_node

    def update(self) -> bool:
        """Update simulation with CMAT mechanics."""
        self.time += 1
        new_nodes = []
        active_nodes = sorted(self.nodes, key=lambda n: n.energy, reverse=True)
        max_new_nodes = min(3, self.params['max_nodes'] - len(self.nodes))

        for node in active_nodes:
            dH, dD, dT = self.update_node_dynamics(node)
            node.coherence = max(0, node.coherence + dH)
            node.distortion = max(0, node.distortion + dD)
            node.temporal_complexity += dT
            node.spatial_complexity = self.calculate_spatial_complexity(node.position)
            node.energy = self.calculate_energy(node.position)
            node.age += 1

            # Singularity: Spawn hierarchical layer
            if node.distortion > self.params['d_critical']:
                child_engine = CSpaceEngine(self.width, self.height, self.params)
                child_engine.initialize_plant((node.position.x, node.position.y), node.energy)
                self.children.append(child_engine)
                node.coherence, node.distortion = 0, 0  # Collapse to pure time state
                node.temporal_complexity = node.energy * math.log(node.depth + self.params['epsilon'])

            new_nodes.append(node)

        # Controlled growth and branching
        new_count = 0
        random.shuffle(active_nodes)
        for node in active_nodes:
            if new_count >= max_new_nodes:
                break
            if random.random() < self.params['growth_prob']:
                new_growth = self.grow_node(node)
                if new_growth and len(new_nodes) < self.params['max_nodes']:
                    new_nodes.append(new_growth)
                    new_count += 1
            if random.random() < self.params['branch_prob']:
                new_branch = self.branch_node(node)
                if new_branch and len(new_nodes) < self.params['max_nodes']:
                    new_nodes.append(new_branch)
                    node.distortion *= 0.5
                    new_count += 1

        self.nodes = new_nodes[:self.params['max_nodes']]

        # Update paths and recurse into children
        self.paths = {n.parent: [c for c in self.nodes if c.parent == n.parent] for n in self.nodes if n.parent is not None}
        for child in self.children:
            child.update()

        return len(self.nodes) < self.params['max_nodes']

    def get_state(self):
        state = {
            'nodes': self.nodes,
            'resources': self.resources,
            'paths': self.paths,
            'time': self.time,
            'children': [child.get_state() for child in self.children]
        }
        return state