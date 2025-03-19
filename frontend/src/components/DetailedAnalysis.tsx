import React from 'react';
import './DetailedAnalysis.css';

// Função para limpar o texto da análise detalhada
const cleanAnalysisText = (text: string): string => {
  if (!text) return '';
  
  // Remove números sozinhos no início da linha
  let cleanedText = text.replace(/^\s*\d+\s*$/m, '').trim();
  
  // Remove scores de avaliação (como "EFICÁCIA: 8")
  cleanedText = cleanedText.replace(/\b(CLAREZA|CONTEXTO|EFICÁCIA):\s*\d+(\s*\/\s*\d+)?\s*/gi, '').trim();
  
  return cleanedText;
};

const formatText = (text: string): JSX.Element => {
  // Limpa o texto antes de formatá-lo
  const cleanedText = cleanAnalysisText(text);
  
  if (!cleanedText) return <p>Informação não disponível</p>;
  
  // Converter links para elementos clicáveis
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const textWithLinks = cleanedText.split(urlRegex).map((part, i) => {
    return part.match(urlRegex) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer">
        {part}
      </a>
    ) : (
      part
    );
  });

  // Quebrar parágrafos
  const withParagraphs = textWithLinks.map((part) => {
    if (typeof part === 'string') {
      return part.split('\n\n').map((paragraph, idx) => (
        <p key={idx}>{paragraph.split('\n').map((line, i) => (
          <React.Fragment key={i}>
            {line}
            {i < paragraph.split('\n').length - 1 && <br />}
          </React.Fragment>
        ))}</p>
      ));
    }
    return part;
  });

  return <>{withParagraphs}</>;
};

interface DetailedAnalysisProps {
  analysis: {
    central_objective?: string;
    strengths_weaknesses?: string;
    context?: string;
    practical_suggestions?: string;
    ethical_practices?: string;
  } | null;
}

const DetailedAnalysis: React.FC<DetailedAnalysisProps> = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="detailed-analysis">
        <p>Análise detalhada não disponível.</p>
      </div>
    );
  }

  return (
    <div className="detailed-analysis">
      <h2>Análise Detalhada</h2>
      
      <div className="analysis-section">
        <h3>Objetivo Central</h3>
        <div className="analysis-content">
          {formatText(analysis.central_objective || '')}
        </div>
      </div>
      
      <div className="analysis-section">
        <h3>Pontos Fortes e Fracos</h3>
        <div className="analysis-content">
          {formatText(analysis.strengths_weaknesses || '')}
        </div>
      </div>
      
      <div className="analysis-section">
        <h3>Contexto</h3>
        <div className="analysis-content">
          {formatText(analysis.context || '')}
        </div>
      </div>
      
      <div className="analysis-section">
        <h3>Sugestões Práticas</h3>
        <div className="analysis-content">
          {formatText(analysis.practical_suggestions || '')}
        </div>
      </div>
      
      <div className="analysis-section">
        <h3>Práticas Éticas</h3>
        <div className="analysis-content">
          {formatText(analysis.ethical_practices || '')}
        </div>
      </div>
    </div>
  );
};

export default DetailedAnalysis; 