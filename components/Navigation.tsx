import React from 'react';

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="flex justify-center bg-gray-100 p-2">
      <button 
        onClick={() => setActiveTab('visualization')}
        className={`px-4 py-2 mx-1 border-none rounded ${
          activeTab === 'visualization' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'
        } cursor-pointer`}
      >
        Interactive Visualization
      </button>
      <button 
        onClick={() => setActiveTab('theory')}
        className={`px-4 py-2 mx-1 border-none rounded ${
          activeTab === 'theory' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'
        } cursor-pointer`}
      >
        Theory Explanation
      </button>
    </nav>
  );
};