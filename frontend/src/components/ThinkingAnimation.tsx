import React, { useState, useEffect } from 'react';

interface ThinkingAnimationProps {
  message?: string;
}

const BrainIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
    <path d="M15.75 5h-5c-1.2 0-2.4.5-3.2 1.3L4.4 9.5a.2.2 0 00.3.3l2.6-2.1a.2.2 0 01.2 0l2.5 2.1c.1.1.3.1.4 0l2.5-2.1c.1-.1.3-.1.4 0l2.5 2.1c.1.1.3.1.4 0l2.6-2.1c.2-.2.4 0 .3.3l-3.1 3.2c-.8.8-2 1.3-3.2 1.3h-5c-1.2 0-2.4-.5-3.2-1.3L1.1 8a1 1 0 01-.3-.7c0-1.1.9-2 2-2h2.6L8 2.7c.8-.8 2-1.2 3.2-1.2h1.6c1.2 0 2.4.4 3.2 1.2l2.6 2.6h2.6c1.1 0 2 .9 2 2 0 .3-.1.5-.3.7L19.8 11c-.8.8-2 1.3-3.2 1.3 1.4 0 2.6-.6 3.5-1.5l1.2-1.2c.3-.3.5-.7.5-1.1 0-1.7-1.5-3.1-3.3-3.1h-2a2 2 0 01-1.4-.6l-2.6-2.6c-.6-.6-1.5-1-2.4-1h-1.6c-1 0-1.8.4-2.4 1L3.9 5.5c-.4.4-.9.6-1.4.6H2.7c-.6 0-1.2.2-1.6.6-.8.7-1 1.9-.7 2.8 0 .1 0 .1.1.2 0 0 .2.2.3.3l3.2 3.2c.8.9 2 1.5 3.4 1.5-1.4 0-2.6-.6-3.5-1.5l-1.2-1.2c-.3-.3-.5-.7-.5-1.1 0-1.7 1.5-3.1 3.3-3.1h2a2 2 0 011.4-.6h9.6c.5 0 1 .2 1.4.6l2.6 2.6c.6.6 1.5 1 2.4 1h1.6c.9 0 1.8-.4 2.4-1l2.6-2.6c.4-.4.9-.6 1.4-.6h.9c1.7 0 3.1 1.4 3.1 3.1 0 .4-.2.8-.5 1.1l-1.2 1.2c-.9.9-2.1 1.5-3.5 1.5 1.2 0 2.3-.5 3.2-1.3l3.1-3.1c.2-.2.3-.5.3-.7 0-1.1-.9-2-2-2h-2.6L19.4 2.7c-.8-.8-2-1.2-3.2-1.2h-1.6c-1.2 0-2.4.4-3.2 1.2L8.8 5.3 6.2 2.7c-.8-.8-2-1.2-3.2-1.2H2.8c-1.1 0-2 .9-2 2 0 .3.1.5.3.7l3.1 3.1c.8.8 2 1.3 3.2 1.3h5c1.2 0 2.4-.5 3.2-1.3l3.1-3.1c.2-.2.4 0 .3.3l-3.1 3.2c-.8.8-2 1.3-3.2 1.3H8.3"/>
  </svg>
);

const MagnifyingGlassIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"></circle>
    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);

const ChecklistIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="10" y1="6" x2="21" y2="6"></line>
    <line x1="10" y1="12" x2="21" y2="12"></line>
    <line x1="10" y1="18" x2="21" y2="18"></line>
    <circle cx="4" cy="6" r="2"></circle>
    <circle cx="4" cy="12" r="2"></circle>
    <circle cx="4" cy="18" r="2"></circle>
  </svg>
);

const StarIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

const ThinkingAnimation: React.FC<ThinkingAnimationProps> = ({ 
  message = "Avaliando seu prompt..." 
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const evaluationSteps = [
    { icon: <BrainIcon />, text: "Analisando a estrutura do prompt..." },
    { icon: <MagnifyingGlassIcon />, text: "Verificando contexto e clareza..." },
    { icon: <ChecklistIcon />, text: "Avaliando efetividade e precisão..." },
    { icon: <StarIcon />, text: "Calculando pontuação final..." }
  ];

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % evaluationSteps.length);
    }, 3000);

    return () => clearInterval(stepInterval);
  }, []);

  return (
    <div className="thinking-animation">
      <div className="thinking-container">
        <div className="thinking-brain">
          {evaluationSteps[currentStep].icon}
          <div className="thinking-neurons">
            <div className="neuron"></div>
            <div className="neuron"></div>
            <div className="neuron"></div>
            <div className="neuron"></div>
            <div className="neuron"></div>
          </div>
        </div>
        
        <div className="thinking-message">
          {evaluationSteps[currentStep].text}
          <span className="thinking-dots">
            <span className="thinking-dot"></span>
            <span className="thinking-dot"></span>
            <span className="thinking-dot"></span>
          </span>
        </div>
        
        <div className="thinking-steps">
          {evaluationSteps.map((step, index) => (
            <div 
              key={index} 
              className={`thinking-step ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
            >
              <div className="step-number">{index + 1}</div>
            </div>
          ))}
        </div>
        
        <div className="thinking-progress">
          <div className="thinking-progress-bar"></div>
          <div className="thinking-progress-glow"></div>
        </div>
        
        <div className="thinking-criteria">
          <div className={`criteria-item ${currentStep >= 1 ? 'active' : ''}`}>
            <span className="criteria-label">Clareza</span>
            <div className="criteria-dots">
              <span className={`criteria-dot ${currentStep >= 1 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 2 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 3 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 4 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 5 ? 'filling' : ''}`}></span>
            </div>
          </div>
          <div className={`criteria-item ${currentStep >= 2 ? 'active' : ''}`}>
            <span className="criteria-label">Contexto</span>
            <div className="criteria-dots">
              <span className={`criteria-dot ${currentStep >= 2 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 3 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 4 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 5 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 6 ? 'filling' : ''}`}></span>
            </div>
          </div>
          <div className={`criteria-item ${currentStep >= 3 ? 'active' : ''}`}>
            <span className="criteria-label">Eficácia</span>
            <div className="criteria-dots">
              <span className={`criteria-dot ${currentStep >= 3 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 4 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 5 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 6 ? 'filling' : ''}`}></span>
              <span className={`criteria-dot ${currentStep >= 7 ? 'filling' : ''}`}></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThinkingAnimation; 