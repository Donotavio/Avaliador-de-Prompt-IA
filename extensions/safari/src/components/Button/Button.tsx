import React from 'react';

interface ButtonProps {
  onClick: () => void;
  position: {
    top?: number;
    right?: number;
    bottom?: number;
    left?: number;
  };
}

const Button: React.FC<ButtonProps> = ({ onClick, position }) => {
  return (
    <div 
      className="prompt-evaluator-button"
      onClick={onClick}
      style={{
        top: position.top !== undefined ? `${position.top}px` : 'auto',
        right: position.right !== undefined ? `${position.right}px` : 'auto',
        bottom: position.bottom !== undefined ? `${position.bottom}px` : 'auto',
        left: position.left !== undefined ? `${position.left}px` : 'auto',
      }}
      title="Avaliar e otimizar prompt"
    >
      <svg 
        width="16" 
        height="16" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2"
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
      </svg>
    </div>
  );
};

export default Button; 