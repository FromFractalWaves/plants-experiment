// components/PlantCSpaceVisualizer.tsx
import React, { useRef, useState } from 'react';
import { usePlantCSpace } from '@/hooks/usePlantCSpace';
import { PlantSvgGrid } from './plants/PlantSvgGrid';
import { ComplexityHeatmap } from './plants/ComplexityHeatmap';
import { ResourcePoints } from './plants/ResourcePoints';
import { PlantPaths } from './plants/PlantPaths';
import { PlantNodes } from './plants/PlantNodes';
import { MathematicalAnnotations } from './plants/MathematicalAnnotations';
import { PlantLegend } from './plants/PlantLegend';
import { InfoPanel } from './plants/InfoPanel';

export const PlantCSpaceVisualizer: React.FC = () => {
  const width = 800;
  const height = 600;
  const svgRef = useRef<SVGSVGElement>(null);
  const [showMath, setShowMath] = useState(true);
  const [showComplexity, setShowComplexity] = useState(true);
  
  const {
    nodes,
    resources,
    paths,
    time,
    paused,
    setPaused,
    calculateSpatialComplexity,
    calculateEnergy,
  } = usePlantCSpace(width, height);

  return (
    <div className="plant-cspace-container">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-100 p-4 mb-5 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Plants as Natural C-Space Navigators</h2>
          <p className="text-sm">
            This visualization demonstrates how plants navigate the Computational Spacetime (C-Space) 
            Framework, following geodesic paths determined by coherence (H), distortion (D), 
            and emergent time (T) dynamics. Watch as the plant optimizes its growth toward light while 
            navigating complexity fields and utilizing support structures.
          </p>
        </div>
      </div>
      
      <svg 
        ref={svgRef}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border border-gray-300 bg-gray-50 block mx-auto"
      >
        {/* Grid representing the manifold */}
        <PlantSvgGrid width={width} height={height} />
        
        {/* Complexity heatmap */}
        <ComplexityHeatmap 
          width={width} 
          height={height} 
          showComplexity={showComplexity}
          calculateSpatialComplexity={calculateSpatialComplexity}
          calculateEnergy={calculateEnergy}
        />
        
        {/* Resource points */}
        <ResourcePoints resources={resources} />
        
        {/* Plant paths */}
        <PlantPaths paths={paths} />
        
        {/* Plant nodes */}
        <PlantNodes nodes={nodes} />
        
        {/* Mathematical annotations */}
        <MathematicalAnnotations showMath={showMath} nodes={nodes} />
        
        {/* Legend */}
        <PlantLegend time={time} />
        
        {/* Title */}
        <text x={width/2} y="30" textAnchor="middle" fontSize={18} fontWeight="bold" fill="#333">
          Plant Growth as Navigation Through Computational Spacetime
        </text>
      </svg>
      
      <div className="controls mt-5 flex justify-center gap-2 max-w-4xl mx-auto">
        <button 
          onClick={() => setPaused(!paused)}
          className={`px-4 py-2 text-white border-none rounded cursor-pointer flex-1 ${
            paused ? 'bg-green-500' : 'bg-red-500'
          }`}
        >
          {paused ? 'Resume Growth' : 'Pause Growth'}
        </button>
        <button 
          onClick={() => setShowMath(!showMath)}
          className="px-4 py-2 bg-blue-500 text-white border-none rounded cursor-pointer flex-1"
        >
          {showMath ? 'Hide Equations' : 'Show Equations'}
        </button>
        <button 
          onClick={() => setShowComplexity(!showComplexity)}
          className="px-4 py-2 bg-orange-500 text-white border-none rounded cursor-pointer flex-1"
        >
          {showComplexity ? 'Hide Complexity Field' : 'Show Complexity Field'}
        </button>
      </div>

      <InfoPanel />
    </div>
  );
};