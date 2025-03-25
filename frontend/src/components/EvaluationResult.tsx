import React, { useEffect, useState, useRef } from 'react';
import DetailedAnalysis from './DetailedAnalysis';

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
    // Adicionando campos da análise detalhada
    detailed_analysis?: {
      central_objective?: string;
      strengths_weaknesses?: string;
      context?: string;
      practical_suggestions?: string;
      ethical_practices?: string;
    };
  };
}

const EvaluationResult: React.FC<EvaluationResultProps> = ({ result }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [fadeIn, setFadeIn] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  // Scroll para o resultado quando ele for exibido
  useEffect(() => {
    if (resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    // Adicionar efeito de fade-in
    setTimeout(() => setFadeIn(true), 100);
  }, []);

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
      })
      .catch(err => {
        console.error('Erro ao copiar: ', err);
      });
  };

  // Extraindo os scores
  const clarityScore = result.clarity_score ?? result.scores?.clarity ?? 0;
  const contextScore = result.context_score ?? result.scores?.context ?? 0;
  const effectivenessScore = result.effectiveness_score ?? result.scores?.effectiveness ?? 0;
  
  // Calculando média se não estiver disponível
  const averageScore = result.scores?.average ?? 
    ((clarityScore + contextScore + effectivenessScore) / 3);

  const formatScore = (score: number): string => {
    return score.toFixed(1);
  };

  // Função para determinar cor com base na pontuação
  const getScoreColor = (score: number): string => {
    if (score >= 8) return 'var(--success)';
    if (score >= 6) return 'var(--warning)';
    return 'var(--error)';
  };

  return (
    <div 
      ref={resultRef} 
      className={`resultado-avaliacao prompt-evaluation ${fadeIn ? 'fade-in' : ''}`}
    >
      <div className="evaluation-header">
        <h2 className="evaluation-title">Resultado da Avaliação</h2>
        <p className="evaluation-desc">Análise detalhada do seu prompt e sugestões de melhoria</p>
      </div>

      <div className="evaluation-criteria">
        <div className="criterion">
          <div className="criterion-header">
            <span className="criterion-label">Clareza</span>
            <div className="criterion-rating">
              <div 
                className="rating-value" 
                style={{ color: getScoreColor(clarityScore) }}
              >
                {formatScore(clarityScore)}
              </div>
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span 
                    key={i} 
                    style={{ 
                      opacity: (clarityScore / 10) * 5 > i ? 1 : 0.3 
                    }}
                  >★</span>
                ))}
              </div>
            </div>
          </div>
          <p className="criterion-desc">Quão claro e explícito é o prompt</p>
        </div>

        <div className="criterion">
          <div className="criterion-header">
            <span className="criterion-label">Contexto</span>
            <div className="criterion-rating">
              <div 
                className="rating-value" 
                style={{ color: getScoreColor(contextScore) }}
              >
                {formatScore(contextScore)}
              </div>
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span 
                    key={i} 
                    style={{ 
                      opacity: (contextScore / 10) * 5 > i ? 1 : 0.3 
                    }}
                  >★</span>
                ))}
              </div>
            </div>
          </div>
          <p className="criterion-desc">Grau de contexto e informações de suporte</p>
        </div>

        <div className="criterion">
          <div className="criterion-header">
            <span className="criterion-label">Eficácia</span>
            <div className="criterion-rating">
              <div 
                className="rating-value" 
                style={{ color: getScoreColor(effectivenessScore) }}
              >
                {formatScore(effectivenessScore)}
              </div>
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span 
                    key={i} 
                    style={{ 
                      opacity: (effectivenessScore / 10) * 5 > i ? 1 : 0.3 
                    }}
                  >★</span>
                ))}
              </div>
            </div>
          </div>
          <p className="criterion-desc">Capacidade de produzir resultados desejados</p>
        </div>

        <div className="criterion">
          <div className="criterion-header">
            <span className="criterion-label">Pontuação Média</span>
            <div className="criterion-rating">
              <div 
                className="rating-value" 
                style={{ color: getScoreColor(averageScore) }}
              >
                {formatScore(averageScore)}
              </div>
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span 
                    key={i} 
                    style={{ 
                      opacity: (averageScore / 10) * 5 > i ? 1 : 0.3 
                    }}
                  >★</span>
                ))}
              </div>
            </div>
          </div>
          <p className="criterion-desc">Qualidade geral do prompt</p>
        </div>
      </div>

      {result.optimized_prompt && (
        <div className="optimized-prompt">
          <h3>Versão Otimizada do Prompt</h3>
          <div className="prompt-text-container">
            <div className="prompt-text">
              {result.optimized_prompt}
            </div>
            <button 
              className="copy-button"
              onClick={() => handleCopy(result.optimized_prompt || '', 0)}
            >
              {copiedIndex === 0 ? 'Copiado!' : 'Copiar'}
            </button>
          </div>
        </div>
      )}

      {result.suggestions && result.suggestions.length > 0 && (
        <div className="suggestions">
          <h3>Sugestões de Melhoria</h3>
          <ul className="suggestions-list">
            {result.suggestions.map((suggestion, index) => (
              <li key={index} className="suggestion-item">{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      {result.detailed_analysis && (
        <DetailedAnalysis 
          analysisData={
            typeof result.detailed_analysis === 'string' 
              ? (() => {
                  try {
                    return JSON.parse(result.detailed_analysis);
                  } catch (e) {
                    console.error('Erro ao analisar detailed_analysis:', e);
                    // Fallback para quando não é um JSON válido
                    return {
                      central_objective: result.detailed_analysis
                    };
                  }
                })()
              : result.detailed_analysis
          } 
        />
      )}
    </div>
  );
};

export default EvaluationResult; 