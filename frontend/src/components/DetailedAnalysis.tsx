import React from 'react';

// Função para limpar o texto da análise detalhada
const cleanAnalysisText = (text: string): string => {
  if (!text) return '';
  // Remove marcações de markdown simples que podem vir na resposta
  return text
    .replace(/^\s*[-*]\s+/gm, '') // Remove bullet points no início das linhas
    .replace(/^#+\s+/gm, '')      // Remove títulos markdown
    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove negrito
    .replace(/\*(.*?)\*/g, '$1')  // Remove itálico
    .trim();
};

interface DetailedAnalysisProps {
  analysisData: {
    central_objective?: string;
    strengths_weaknesses?: string;
    context?: string;
    practical_suggestions?: string;
    ethical_practices?: string;
  };
}

const DetailedAnalysis: React.FC<DetailedAnalysisProps> = ({ analysisData }) => {
  if (!analysisData) return null;

  const sections = [
    { title: 'Objetivo Central', content: analysisData.central_objective },
    { title: 'Pontos Fortes e Fracos', content: analysisData.strengths_weaknesses },
    { title: 'Análise de Contexto', content: analysisData.context },
    { title: 'Sugestões Práticas', content: analysisData.practical_suggestions },
    { title: 'Práticas Éticas', content: analysisData.ethical_practices }
  ];

  // Filtrar apenas seções que têm conteúdo
  const filteredSections = sections.filter(section => section.content);

  if (filteredSections.length === 0) return null;

  return (
    <div className="detailed-analysis">
      <h3 className="detailed-title">Análise Detalhada</h3>
      
      {filteredSections.map((section, index) => (
        <div key={index} className="analysis-section">
          <h4 className="section-title">{section.title}</h4>
          <p className="section-content">{cleanAnalysisText(section.content || '')}</p>
        </div>
      ))}
    </div>
  );
};

export default DetailedAnalysis; 