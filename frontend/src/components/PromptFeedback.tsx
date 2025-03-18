import React from 'react';

interface PromptEvaluation {
  clarity_score: number;
  context_score: number;
  effectiveness_score: number;
  suggestions: string[];
  optimized_prompt: string;
}

interface PromptFeedbackProps {
  evaluation: PromptEvaluation;
}

const PromptFeedback: React.FC<PromptFeedbackProps> = ({ evaluation }) => {
  const {
    clarity_score,
    context_score,
    effectiveness_score,
    suggestions,
    optimized_prompt,
  } = evaluation;

  const averageScore =
    (clarity_score + context_score + effectiveness_score) / 3;

  return (
    <div className="prompt-feedback">
      <h2>Resultado da Avaliação</h2>
      
      <div className="scores">
        <div className="score-item">
          <h3>Clareza</h3>
          <div className="score-value">{clarity_score.toFixed(1)}</div>
        </div>
        
        <div className="score-item">
          <h3>Contexto</h3>
          <div className="score-value">{context_score.toFixed(1)}</div>
        </div>
        
        <div className="score-item">
          <h3>Eficácia</h3>
          <div className="score-value">{effectiveness_score.toFixed(1)}</div>
        </div>
        
        <div className="score-item total">
          <h3>Média</h3>
          <div className="score-value">{averageScore.toFixed(1)}</div>
        </div>
      </div>

      <div className="suggestions">
        <h3>Sugestões de Melhoria</h3>
        <ul>
          {suggestions.map((suggestion, index) => (
            <li key={index}>{suggestion}</li>
          ))}
        </ul>
      </div>

      <div className="optimized-prompt">
        <h3>Prompt Otimizado</h3>
        <pre>{optimized_prompt}</pre>
      </div>
    </div>
  );
};

export default PromptFeedback; 