// components/Footer.tsx
import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="text-center p-5 border-t border-gray-200 mt-5 text-sm">
      <p>
        An extension of the Computational Spacetime (C-Space) Framework © {new Date().getFullYear()}
      </p>
    </footer>
  );
};