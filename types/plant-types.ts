// types/plant-types.ts
export interface Vector2D {
    x: number;
    y: number;
  }
  
  export interface PlantNode {
    id: number;
    position: Vector2D;
    energy: number; // E(p)
    coherence: number; // H
    distortion: number; // D
    temporalComplexity: number; // T
    spatialComplexity: number; // S(p)
    parent: number | null;
    age: number;
  }
  
  export interface ResourcePoint {
    position: Vector2D;
    intensity: number; // Energy intensity
    type: 'light' | 'support' | 'obstacle';
  }
