import React from 'react';
import '../styles/EvaluationResult.css';

interface EvaluationResultProps {
  result: {
    scores?: {
      clarity?: number;
      context?: number;
      effectiveness?: number;
      average?: number;
    };
    suggestions?: string[];
    optimized_prompt?: string;
    improved_versions?: string[];
    premium_status?: string;
  };
}

const EvaluationResult: React.FC<EvaluationResultProps> = ({ result }) => {
  if (!result) {
    return null;
  }

  const { scores = {}, suggestions = [], optimized_prompt = '', improved_versions = [], premium_status } = result;
  const { clarity = 0, context = 0, effectiveness = 0, average = 0 } = scores;

  return (
    <div className="evaluation-result">
      <h2>Resultado da Avaliação</h2>
      
      <div className="scores-section">
        <h3>Pontuações</h3>
        <div className="scores-grid">
          <div className="score-item">
            <label>Clareza:</label>
            <div className="score-value" style={{ color: clarity >= 7 ? '#28a745' : '#dc3545' }}>
              {clarity}/10
            </div>
          </div>
          <div className="score-item">
            <label>Contexto:</label>
            <div className="score-value" style={{ color: context >= 7 ? '#28a745' : '#dc3545' }}>
              {context}/10
            </div>
          </div>
          <div className="score-item">
            <label>Eficácia:</label>
            <div className="score-value" style={{ color: effectiveness >= 7 ? '#28a745' : '#dc3545' }}>
              {effectiveness}/10
            </div>
          </div>
          <div className="score-item">
            <label>Média:</label>
            <div className="score-value" style={{ color: average >= 7 ? '#28a745' : '#dc3545' }}>
              {average}/10
            </div>
          </div>
        </div>
      </div>

      {suggestions.length > 0 && (
        <div className="suggestions-section">
          <h3>Sugestões de Melhoria</h3>
          <ul>
            {suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      {optimized_prompt && (
        <div className="optimized-prompt-section">
          <h3>Prompt Otimizado</h3>
          <div className="prompt-box">
            {optimized_prompt}
          </div>
        </div>
      )}

      {improved_versions && improved_versions.length > 0 && (
        <div className="improved-versions-section">
          <h3>Versões Melhoradas do Prompt</h3>
          {improved_versions.map((version, index) => (
            <div key={index} className="improved-version">
              <h4>Versão {index + 1}</h4>
              <div className="prompt-box">
                {version}
              </div>
            </div>
          ))}
        </div>
      )}

      {premium_status && (
        <div className="premium-status-section">
          <p>{premium_status}</p>
        </div>
      )}
    </div>
  );
};

export default EvaluationResult; 