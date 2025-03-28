// components/Header.tsx
import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="app-header bg-gradient-to-r from-blue-900 via-red-700 to-yellow-400 text-white p-5 text-center">
      <h1 className="m-0 text-2xl">Plants as C-Space Navigators</h1>
      <p className="mt-2 text-base">Visualizing the connection between plant growth and Computational Spacetime</p>
    </header>
  );
};