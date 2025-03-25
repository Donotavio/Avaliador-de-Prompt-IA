import React from 'react';

// Função para formatar o texto de Pontos Fortes e Fracos
const formatStrengthsWeaknesses = (text: string): React.ReactNode => {
  if (!text) return null;
  
  const strongsWeaksRegex = /Pontos fortes:(.+?)(?:Pontos fracos:|$)/si;
  const weaksRegex = /Pontos fracos:(.+)$/si;
  
  const strongsMatch = text.match(strongsWeaksRegex);
  const weaksMatch = text.match(weaksRegex);
  
  const strongs = strongsMatch ? strongsMatch[1].trim() : '';
  const weaks = weaksMatch ? weaksMatch[1].trim() : '';
  
  // Se não encontrou o padrão esperado, retorna o texto original formatado
  if (!strongs && !weaks) {
    return <p className="section-content">{formatAnalysisText(text)}</p>;
  }
  
  return (
    <div className="strengths-weaknesses">
      {strongs && (
        <div className="strength-section">
          <h5 className="sw-title">Pontos fortes:</h5>
          <p className="sw-content">{formatAnalysisText(strongs)}</p>
        </div>
      )}
      
      {weaks && (
        <div className="weakness-section">
          <h5 className="sw-title">Pontos fracos:</h5>
          <p className="sw-content">{formatAnalysisText(weaks)}</p>
        </div>
      )}
    </div>
  );
};

// Função para limpar e formatar o texto da análise detalhada
const formatAnalysisText = (text: string): string => {
  if (!text) return '';
  
  // Remove marcações de markdown simples que podem vir na resposta
  let formatted = text
    .replace(/^\s*[-*]\s+/gm, '') // Remove bullet points no início das linhas
    .replace(/^#+\s+/gm, '')      // Remove títulos markdown
    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove negrito
    .replace(/\*(.*?)\*/g, '$1')  // Remove itálico
    .trim();
  
  // Verifica se o texto é uma lista numerada e preserva a formatação
  if (/^\d+\.\s/.test(formatted)) {
    return formatted;
  }
  
  return formatted;
};

// Função para verificar se o texto contém uma lista numerada
const containsNumberedList = (text: string): boolean => {
  return /\d+\.\s/.test(text);
};

// Função para formatar listas numeradas em HTML
const formatNumberedList = (text: string, sectionType?: string): React.ReactNode => {
  if (!text) return null;
  
  // Para Pontos Fortes e Fracos, usamos formatação especial
  if (sectionType === 'strengths_weaknesses') {
    return formatStrengthsWeaknesses(text);
  }
  
  // Se o texto contém padrões como "1. ... 2. ... 3. ..." em um único parágrafo
  // vamos processá-lo de forma especial para separar os itens corretamente
  if (sectionType === 'practical_suggestions' && /\d+\.\s.+\s\d+\.\s/.test(text)) {
    // Divide o texto nos pontos numerados
    const items = text.split(/(?=\d+\.\s)/g).filter(Boolean);
    
    return (
      <ol className="section-list">
        {items.map((item, i) => {
          // Remove o número e o ponto do início
          const content = item.replace(/^\d+\.\s+/, '');
          return <li key={i}>{formatAnalysisText(content)}</li>;
        })}
      </ol>
    );
  }
  
  // Se não contém uma lista numerada, retorna o texto limpo
  if (!containsNumberedList(text)) {
    return <p className="section-content">{formatAnalysisText(text)}</p>;
  }
  
  // Divide o texto em linhas
  const lines = text.split(/\n/).map(line => line.trim()).filter(line => line);
  
  // Separa as partes introdutórias das listas numeradas
  const intro: string[] = [];
  const listItems: string[] = [];
  let inList = false;
  
  for (const line of lines) {
    if (/^\d+\.\s/.test(line)) {
      inList = true;
      listItems.push(line);
    } else if (inList) {
      // Verifica se é continuação de um item da lista
      if (line.startsWith('    ') || line.startsWith('\t')) {
        const lastIndex = listItems.length - 1;
        listItems[lastIndex] = `${listItems[lastIndex]} ${line.trim()}`;
      } else {
        intro.push(line);
      }
    } else {
      intro.push(line);
    }
  }
  
  return (
    <>
      {intro.length > 0 && 
        <p className="section-content">{formatAnalysisText(intro.join(' '))}</p>
      }
      {listItems.length > 0 && 
        <ol className="section-list">
          {listItems.map((item, i) => {
            // Remove o número e o ponto do início
            const content = item.replace(/^\d+\.\s+/, '');
            return <li key={i}>{formatAnalysisText(content)}</li>;
          })}
        </ol>
      }
    </>
  );
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
    { title: 'Objetivo Central', content: analysisData.central_objective, type: 'central_objective' },
    { title: 'Pontos Fortes e Fracos', content: analysisData.strengths_weaknesses, type: 'strengths_weaknesses' },
    { title: 'Análise de Contexto', content: analysisData.context, type: 'context' },
    { title: 'Sugestões Práticas', content: analysisData.practical_suggestions, type: 'practical_suggestions' },
    { title: 'Práticas Éticas', content: analysisData.ethical_practices, type: 'ethical_practices' }
  ];

  // Filtrar apenas seções que têm conteúdo
  const filteredSections = sections.filter(section => section.content);

  if (filteredSections.length === 0) return null;

  return (
    <div className="detailed-analysis">
      <h3 className="detailed-title">Análise Detalhada</h3>
      
      {filteredSections.map((section, index) => (
        <div 
          key={index} 
          className="analysis-section"
          data-section-type={section.type}
        >
          <h4 className="section-title">{section.title}</h4>
          {formatNumberedList(section.content || '', section.type)}
        </div>
      ))}
    </div>
  );
};

export default DetailedAnalysis; 