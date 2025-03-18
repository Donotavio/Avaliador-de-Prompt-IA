import React, { useEffect, useState } from 'react';
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
    // Adicionando campos diretos para compatibilidade com o schema do backend
    clarity_score?: number;
    context_score?: number;
    effectiveness_score?: number;
  };
}

const EvaluationResult: React.FC<EvaluationResultProps> = ({ result }) => {
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    if (result) {
      console.log('Dados recebidos pelo EvaluationResult:', result);
    }
  }, [result]);

  // Reseta a mensagem de cópia após 2 segundos
  useEffect(() => {
    if (copySuccess) {
      const timer = setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [copySuccess]);

  if (!result) {
    return null;
  }

  // Extrair valores diretos se estiverem no nível raiz do objeto (compatibilidade com backend)
  const directClarity = typeof result.clarity_score === 'number' ? result.clarity_score : undefined;
  const directContext = typeof result.context_score === 'number' ? result.context_score : undefined;
  const directEffectiveness = typeof result.effectiveness_score === 'number' ? result.effectiveness_score : undefined;

  // Extrair de scores (compatibilidade com estrutura anterior)
  const { scores = {}, suggestions = [], optimized_prompt = '', improved_versions = [], premium_status } = result;
  
  // Usar valores diretos se disponíveis, caso contrário usar os de scores
  const clarity = directClarity !== undefined ? directClarity : scores.clarity ?? 0;
  const context = directContext !== undefined ? directContext : scores.context ?? 0;
  const effectiveness = directEffectiveness !== undefined ? directEffectiveness : scores.effectiveness ?? 0;
  const average = scores.average ?? ((clarity + context + effectiveness) / 3);

  // Funções de formatação
  const getColorForScore = (score: number): string => {
    if (score === 0) return '#dc3545'; // Vermelho para zero
    if (score < 4) return '#dc3545';   // Vermelho para baixo
    if (score < 7) return '#ffc107';   // Amarelo para médio
    return '#28a745';                  // Verde para alto
  };

  const formatScore = (score: number): string => {
    // Garantir que o score seja um número
    if (isNaN(score) || score === null || score === undefined) return '0/10';
    return `${score}/10`;
  };

  // Filtrar sugestões vazias e remover duplicatas
  const filteredSuggestions = suggestions
    .filter(suggestion => suggestion && suggestion.trim() !== '' && suggestion !== 'Nenhuma sugestão disponível')
    .filter((suggestion, index, self) => self.indexOf(suggestion) === index);

  // Função para copiar o prompt otimizado
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(optimized_prompt);
      setCopySuccess(true);
    } catch (err) {
      console.error('Erro ao copiar o texto: ', err);
    }
  };

  // Ícone de cópia
  const CopyIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  );

  // Ícone de verificação
  const CheckIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  );

  return (
    <div className="evaluation-result">
      <h2>Resultado da Avaliação</h2>
      
      <div className="scores-section">
        <h3>Pontuações</h3>
        <div className="scores-grid">
          <div className="score-item">
            <label>CLAREZA:</label>
            <div className="score-value" style={{ color: getColorForScore(clarity) }}>
              {formatScore(clarity)}
            </div>
          </div>
          <div className="score-item">
            <label>CONTEXTO:</label>
            <div className="score-value" style={{ color: getColorForScore(context) }}>
              {formatScore(context)}
            </div>
          </div>
          <div className="score-item">
            <label>EFICÁCIA:</label>
            <div className="score-value" style={{ color: getColorForScore(effectiveness) }}>
              {formatScore(effectiveness)}
            </div>
          </div>
          <div className="score-item">
            <label>MÉDIA:</label>
            <div className="score-value" style={{ color: getColorForScore(average) }}>
              {formatScore(typeof average === 'number' ? parseFloat(average.toFixed(1)) : 0)}
            </div>
          </div>
        </div>
      </div>

      <div className="suggestions-section">
        <h3>Sugestões de Melhoria</h3>
        {filteredSuggestions.length > 0 ? (
          <ul>
            {filteredSuggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        ) : (
          <p className="no-data-message">Nenhuma sugestão disponível</p>
        )}
      </div>

      {optimized_prompt && optimized_prompt !== 'Não foi possível gerar um prompt otimizado' && (
        <div className="optimized-prompt-section">
          <div className="section-header">
            <h3>Prompt Otimizado</h3>
            <button 
              className={`copy-button ${copySuccess ? 'copied' : ''}`}
              onClick={copyToClipboard} 
              title="Copiar para área de transferência"
            >
              {copySuccess ? <><CheckIcon /> Copiado!</> : <><CopyIcon /> Copiar</>}
            </button>
          </div>
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