// hooks/usePlantCSpace.ts
import { useState, useEffect } from 'react';
import { PlantNode, ResourcePoint, Vector2D } from '../types/plant-types';

// Constants
const ALPHA = 0.05; // Coherence damping coefficient
const BETA = 0.1; // Temporal scaling factor
const EPSILON = 1e-9; // Small constant to avoid division by zero
const D_CRITICAL = 2.5; // Critical distortion threshold for branching
const GROWTH_RATE = 5; // Base growth rate per step
const MAX_ENERGY_DISTANCE = 200; // Maximum distance to sense energy
const COMPLEXITY_GRADIENT_SCALE = 0.01; // Scale for spatial complexity gradient

export const usePlantCSpace = (width: number, height: number) => {
  const [nodes, setNodes] = useState<PlantNode[]>([]);
  const [resources, setResources] = useState<ResourcePoint[]>([]);
  const [paths, setPaths] = useState<{ id: number; d: string }[]>([]);
  const [time, setTime] = useState(0);
  const [paused, setPaused] = useState(false);

  // Initialize the simulation
  useEffect(() => {
    // Create initial seed node at the bottom center
    const seed: PlantNode = {
      id: 0,
      position: { x: width / 2, y: height - 50 },
      energy: 0.5,
      coherence: 1.0,
      distortion: 0.0,
      temporalComplexity: 0.0,
      spatialComplexity: 0.5,
      parent: null,
      age: 0,
    };
    
    setNodes([seed]);
    
    // Create resource environment
    const newResources: ResourcePoint[] = [
      // Light source (energy maximum)
      { position: { x: width * 0.875, y: height * 0.2 }, intensity: 1.0, type: 'light' },
      
      // Support structures (trellis)
      { position: { x: width * 0.5, y: height * 0.5 }, intensity: 0.7, type: 'support' },
      { position: { x: width * 0.625, y: height * 0.5 }, intensity: 0.7, type: 'support' },
      { position: { x: width * 0.75, y: height * 0.5 }, intensity: 0.7, type: 'support' },
      { position: { x: width * 0.5, y: height * 0.333 }, intensity: 0.7, type: 'support' },
      { position: { x: width * 0.625, y: height * 0.333 }, intensity: 0.7, type: 'support' },
      { position: { x: width * 0.75, y: height * 0.333 }, intensity: 0.7, type: 'support' },
      
      // Obstacles (high complexity regions)
      { position: { x: width * 0.3125, y: height * 0.75 }, intensity: 0.9, type: 'obstacle' },
      { position: { x: width * 0.4375, y: height * 0.6667 }, intensity: 0.8, type: 'obstacle' },
    ];
    
    // Add vertical trellis supports
    for (let y = height * 0.333; y <= height * 0.8333; y += height * 0.0333) {
      [width * 0.5, width * 0.625, width * 0.75].forEach(x => {
        newResources.push({
          position: { x, y },
          intensity: 0.6,
          type: 'support',
        });
      });
    }
    
    setResources(newResources);
  }, [width, height]);

  // Calculate spatial complexity at a given position
  const calculateSpatialComplexity = (pos: Vector2D): number => {
    // Higher near obstacles, lower near supports
    let complexity = 0.5; // Base complexity
    
    resources.forEach(resource => {
      const distance = Math.sqrt(
        Math.pow(pos.x - resource.position.x, 2) + 
        Math.pow(pos.y - resource.position.y, 2)
      );
      
      if (distance < 100) {
        if (resource.type === 'obstacle') {
          // Obstacles increase complexity
          complexity += resource.intensity * (1 - distance / 100);
        } else if (resource.type === 'support') {
          // Supports decrease complexity
          complexity -= resource.intensity * (1 - distance / 100) * 0.5;
        }
      }
    });
    
    // Constrain between 0.1 and 1.0
    return Math.max(0.1, Math.min(1.0, complexity));
  };

  // Calculate energy at a given position
  const calculateEnergy = (pos: Vector2D): number => {
    // Higher near light sources
    let energy = 0.2; // Ambient energy
    
    resources.forEach(resource => {
      if (resource.type === 'light') {
        const distance = Math.sqrt(
          Math.pow(pos.x - resource.position.x, 2) + 
          Math.pow(pos.y - resource.position.y, 2)
        );
        
        if (distance < MAX_ENERGY_DISTANCE) {
          // Light intensity drops with square of distance
          energy += resource.intensity * Math.pow(1 - distance / MAX_ENERGY_DISTANCE, 2);
        }
      }
    });
    
    // Constrain between 0.1 and 1.0
    return Math.max(0.1, Math.min(1.0, energy));
  };

  // Calculate the spatial complexity gradient at a position
  const calculateSpatialGradient = (pos: Vector2D): Vector2D => {
    const delta = 5;
    const s = calculateSpatialComplexity(pos);
    const sx = calculateSpatialComplexity({ x: pos.x + delta, y: pos.y });
    const sy = calculateSpatialComplexity({ x: pos.x, y: pos.y + delta });
    
    return {
      x: (sx - s) / delta,
      y: (sy - s) / delta,
    };
  };

  // Update the simulation state
  useEffect(() => {
    if (paused) return;
    
    const timer = setTimeout(() => {
      setTime(t => t + 1);
      
      // Update existing nodes
      setNodes(prevNodes => {
        // First, let's create a copy of the previous nodes
        const newNodes = [...prevNodes];
        // Array to collect new nodes to be added
        const nodesToAdd: PlantNode[] = [];
        
        // Process each node
        prevNodes.forEach((node, index) => {
          // Skip processing for older nodes that have already produced branches
          if (node.age > 20) return;
          
          // Calculate local environment properties
          const pos = node.position;
          const S = calculateSpatialComplexity(pos);
          const E = calculateEnergy(pos);
          const gradient = calculateSpatialGradient(pos);
          
          // Update coherence (H)
          const dD_dH = node.distortion / (node.coherence + EPSILON);
          const gradS = Math.sqrt(gradient.x * gradient.x + gradient.y * gradient.y);
          const dH = -ALPHA * (dD_dH + gradS * COMPLEXITY_GRADIENT_SCALE);
          
          // Update distortion (D)
          const dD = BETA * Math.log1p(Math.abs(dH) * E);
          
          // Update temporal complexity (T)
          const dT = BETA * Math.tanh(Math.abs(dH) * E) * Math.sign(node.coherence);
          
          // Update node properties
          newNodes[index] = {
            ...node,
            coherence: Math.max(0, node.coherence + dH),
            distortion: node.distortion + dD,
            temporalComplexity: node.temporalComplexity + dT,
            spatialComplexity: S,
            energy: E,
            age: node.age + 1,
          };
          
          // FIX: Limited branching to avoid exponential growth
          // Only branch if not already branched too much from this area
          const nearbyNodes = prevNodes.filter(n => 
            Math.sqrt(Math.pow(n.position.x - pos.x, 2) + Math.pow(n.position.y - pos.y, 2)) < 20
          );
          
          // Check for branching (singularity handling)
          if (node.distortion > D_CRITICAL && E > 0.3 && node.age > 5 && nearbyNodes.length < 3) {
            // Create a new branch - enter hierarchical infinity
            const branchDirection = Math.random() * 2 * Math.PI;
            const branchDistance = GROWTH_RATE * (0.5 + 0.5 * E);
            
            const newNode: PlantNode = {
              id: prevNodes.length + nodesToAdd.length,
              position: {
                x: pos.x + Math.cos(branchDirection) * branchDistance,
                y: pos.y + Math.sin(branchDirection) * branchDistance,
              },
              energy: E,
              coherence: 1.0, // Reset coherence
              distortion: 0.0, // Reset distortion
              temporalComplexity: node.temporalComplexity, // Preserve T
              spatialComplexity: S,
              parent: node.id,
              age: 0,
            };
            
            nodesToAdd.push(newNode);
            
            // Reset distortion for the original node
            newNodes[index] = {
              ...newNodes[index],
              distortion: 0.5,
            };
          }
          
          // FIX: Limit total growth nodes
          // Only grow if we have less than a certain number of active nodes
          const activeNodeCount = prevNodes.filter(n => n.age < 15).length;
          
          // Grow toward light/support (geodesic path) if not too distorted
          if (node.coherence > 0.2 && node.age < 15 && activeNodeCount < 50 && Math.random() > 0.5) {
            // Calculate growth direction (weighted by energy gradient and spatial complexity)
            const moveX = -gradient.x * 10 - 0.2; // Slight upward bias
            const moveY = -gradient.y * 10 - 0.6; // Stronger upward bias
            
            // Bias toward light sources
            let lightBiasX = 0;
            let lightBiasY = 0;
            
            resources.forEach(resource => {
              if (resource.type === 'light') {
                const dx = resource.position.x - pos.x;
                const dy = resource.position.y - pos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < MAX_ENERGY_DISTANCE) {
                  const weight = resource.intensity * (1 - distance / MAX_ENERGY_DISTANCE);
                  lightBiasX += dx / distance * weight;
                  lightBiasY += dy / distance * weight;
                }
              }
            });
            
            // Calculate pure time state factor (when S → 0, more direct movement)
            const pureTimeFactor = Math.max(0, 1 - S * 2);
            
            // Combine all factors
            const dirX = moveX + lightBiasX * 2 * pureTimeFactor;
            const dirY = moveY + lightBiasY * 2 * pureTimeFactor;
            
            // Normalize and scale by growth rate and energy
            const magnitude = Math.sqrt(dirX * dirX + dirY * dirY);
            const normDirX = magnitude > 0 ? dirX / magnitude : 0;
            const normDirY = magnitude > 0 ? dirY / magnitude : -1; // Default upward
            
            const growth = GROWTH_RATE * (0.5 + 0.5 * E);
            
            // Create new growth node
            const newNode: PlantNode = {
              id: prevNodes.length + nodesToAdd.length,
              position: {
                x: pos.x + normDirX * growth,
                y: pos.y + normDirY * growth,
              },
              energy: E,
              coherence: node.coherence,
              distortion: node.distortion,
              temporalComplexity: node.temporalComplexity + dT,
              spatialComplexity: S,
              parent: node.id,
              age: 0,
            };
            
            nodesToAdd.push(newNode);
          }
        });
        
        // Return the updated nodes array
        return [...newNodes, ...nodesToAdd];
      });
    }, 200); // Update every 200ms
    
    return () => clearTimeout(timer);
  }, [time, paused, resources]);

  // Update the paths for visualization
  useEffect(() => {
    // Generate paths from node connections
    const nodePaths: { id: number; d: string }[] = [];
    
    nodes.forEach(node => {
      if (node.parent !== null) {
        const parent = nodes.find(n => n.id === node.parent);
        if (parent) {
          // Find existing path or create new one
          let pathIndex = nodePaths.findIndex(p => p.id === parent.id);
          
          if (pathIndex === -1) {
            nodePaths.push({
              id: parent.id,
              d: `M${parent.position.x},${parent.position.y} L${node.position.x},${node.position.y}`,
            });
          } else {
            // FIX: Directly modify path to ensure it's always updated
            nodePaths[pathIndex] = {
              ...nodePaths[pathIndex],
              d: `${nodePaths[pathIndex].d} L${node.position.x},${node.position.y}`,
            };
          }
        }
      }
    });
    
    setPaths(nodePaths);
  }, [nodes]);

  return {
    nodes,
    resources,
    paths,
    time,
    paused,
    setPaused,
    calculateSpatialComplexity,
    calculateEnergy,
  };
};