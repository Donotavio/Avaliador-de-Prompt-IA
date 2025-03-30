import React, { useState } from 'react';
import api from '../../services/api';
import { PromptResponse } from '../../types';

interface SidePanelProps {
  isOpen: boolean;
  prompt: string;
  onClose: () => void;
  onApply: (optimizedPrompt: string) => void;
}

const SidePanel: React.FC<SidePanelProps> = ({ isOpen, prompt, onClose, onApply }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PromptResponse | null>(null);
  
  const evaluatePrompt = async () => {
    if (!prompt.trim()) {
      setError('O prompt não pode estar vazio.');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.evaluatePrompt(prompt);
      setResult(response);
    } catch (err) {
      setError('Erro ao avaliar o prompt. Tente novamente mais tarde.');
      console.error('Erro na avaliação:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleApply = () => {
    if (result?.evaluation.optimized_prompt) {
      onApply(result.evaluation.optimized_prompt);
    }
  };
  
  const handleCopy = () => {
    if (result?.evaluation.optimized_prompt) {
      navigator.clipboard.writeText(result.evaluation.optimized_prompt)
        .then(() => {
          // Feedback visual opcional
          console.log('Prompt copiado para a área de transferência');
        })
        .catch(err => {
          console.error('Erro ao copiar:', err);
        });
    }
  };
  
  return (
    <div className={`prompt-evaluator-side-panel ${isOpen ? 'open' : ''}`}>
      <div className="prompt-evaluator-side-panel-header">
        <h3>Avaliador de Prompts</h3>
        <button className="prompt-evaluator-side-panel-close" onClick={onClose}>✕</button>
      </div>
      
      <div className="prompt-evaluator-side-panel-content">
        <h4>Prompt Original</h4>
        <div className="prompt-evaluator-prompt-display">{prompt}</div>
        
        {!result && (
          <button 
            className="prompt-evaluator-button-primary"
            onClick={evaluatePrompt} 
            disabled={isLoading}
          >
            {isLoading ? 'Avaliando...' : 'Avaliar Prompt'}
          </button>
        )}
        
        {isLoading && (
          <div className="prompt-evaluator-loading">
            <div className="prompt-evaluator-spinner"></div>
          </div>
        )}
        
        {error && (
          <div style={{ color: 'red', margin: '10px 0' }}>{error}</div>
        )}
        
        {result && (
          <>
            <h4>Prompt Otimizado</h4>
            <div className="prompt-evaluator-prompt-display optimized">
              {result.evaluation.optimized_prompt}
            </div>
            
            <div className="prompt-evaluator-button-group">
              <button 
                className="prompt-evaluator-button-primary"
                onClick={handleApply}
              >
                Aplicar
              </button>
              <button 
                className="prompt-evaluator-button-secondary"
                onClick={handleCopy}
              >
                Copiar
              </button>
            </div>
            
            {result.evaluation.suggestions.length > 0 && (
              <>
                <h4>Sugestões</h4>
                <ul style={{ padding: '0 0 0 20px' }}>
                  {result.evaluation.suggestions.map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </>
            )}
            
            <div style={{ marginTop: '20px' }}>
              <button 
                className="prompt-evaluator-button-secondary"
                onClick={() => setResult(null)}
              >
                Nova Avaliação
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SidePanel; 