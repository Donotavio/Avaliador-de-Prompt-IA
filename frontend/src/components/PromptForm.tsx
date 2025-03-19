import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import PremiumModal from './PremiumModal';
import EvaluationResult from './EvaluationResult';
import ThinkingAnimation from './ThinkingAnimation';

// Ícones SVG inline
const SparkleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3l1.7 4.3h4.3l-3.5 3 1.5 4.3-4-3-4 3 1.5-4.3-3.5-3h4.3z"></path>
  </svg>
);

const ResetIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 4v6h-6"></path>
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
  </svg>
);

const SendIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);

const AlertIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

interface PromptFormProps {
  userId: string;
  isAdmin?: boolean;
  isPremium?: boolean;
  openPremiumModal?: () => void;
}

interface PromptEvaluation {
  clarity_score: number;
  context_score: number;
  effectiveness_score: number;
  suggestions: string[];
  optimized_prompt: string;
  scores?: {
    clarity?: number;
    context?: number;
    effectiveness?: number;
    average?: number;
  };
  detailed_analysis?: {
    central_objective?: string;
    strengths_weaknesses?: string;
    context?: string;
    practical_suggestions?: string;
    ethical_practices?: string;
  };
}

const PromptForm: React.FC<PromptFormProps> = ({ userId, isAdmin, isPremium, openPremiumModal }) => {
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState('');
  const [model, setModel] = useState<string>('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PromptEvaluation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [evaluationCount, setEvaluationCount] = useState<number | null>(null);
  const [maxFreeEvaluations] = useState<number>(10);

  useEffect(() => {
    const checkStatus = async () => {
      await checkPremiumStatus();
      await checkFreeStatus();
    };
    checkStatus();
  }, [userId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const checkUserRole = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          return;
        }
        
        const response = await fetch('/api/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          await response.json();
        }
      } catch (error) {
        console.error('Erro ao verificar permissões:', error);
      }
    };
    
    checkUserRole();
  }, []);

  const showMessage = (message: string, type: 'success' | 'error' | 'warning') => {
    if (type === 'error') {
      setError(message);
    } else {
      setError(null);
    }
    setTimeout(() => setError(null), 5000);
  };

  const checkPremiumStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const actualUserId = userId || 'anon';
      
      const response = await fetch(`/premium/status/${actualUserId}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });
      
      if (!response.ok) {
        // Se o erro for 401 ou 403, definimos valores padrão para usuários não autenticados
        if (response.status === 401 || response.status === 403) {
          setEvaluationCount(null);
          return;
        }
        throw new Error('Falha ao verificar status premium');
      }
      
      const data = await response.json();
      setEvaluationCount(data.evaluation_count);
      
      // Não definir mensagem de status para usuários premium
      // Só definir erro se explicitamente não puder usar premium
      if (data.status === false) {
        setError(data.message);
      } else {
        // Limpar mensagens de erro anteriores se o status for ok
        setError(null);
      }
    } catch (error) {
      console.error('Erro ao verificar status premium:', error);
      // Por padrão, define que não pode usar premium
      setEvaluationCount(null);
      setError('Não foi possível verificar o status premium');
    }
  };

  const checkFreeStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const actualUserId = userId || 'anon';
      
      const response = await fetch(`/free/status/${actualUserId}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });
      
      if (!response.ok) {
        // Se o erro for 401 ou 403, definimos valores padrão para usuários não autenticados
        if (response.status === 401 || response.status === 403) {
          setEvaluationCount(maxFreeEvaluations);
          return;
        }
        throw new Error('Falha ao verificar status gratuito');
      }
      
      const data = await response.json();
      setEvaluationCount(data.evaluation_count);
      
      // Só definir erro se o status for falso (não pode usar)
      if (data.status === false) {
        setError(data.message);
      } else {
        // Limpar mensagens de erro anteriores se o status for ok
        setError(null);
      }
    } catch (error) {
      console.error('Erro ao verificar status gratuito:', error);
      // Em caso de erro, definimos valores padrão permissivos
      setEvaluationCount(maxFreeEvaluations);
    }
  };

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    
    if (prompt.trim().length < 10) {
      showMessage('O prompt deve ter pelo menos 10 caracteres', 'error');
      return;
    }

    if (!model) {
      showMessage('Por favor, selecione o modelo LLM', 'error');
      return;
    }

    setIsEvaluating(true);
    setError(null);
    setResult(null);

    try {
      // Use 'anon' como ID para usuários não logados
      const actualUserId = userId || 'anon';
      
      // Verificar se há token de autenticação
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Adicionar token de autenticação se disponível
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('/evaluate', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          content: prompt,
          context: context || undefined,
          plan_type: isPremium ? "premium" : "free",  // Use plano premium se usuário tiver acesso
          user_id: actualUserId,
          target_llm: model,
        }),
      });

      const data = await response.json();
      
      console.log('Resposta API completa:', data);

      if (!response.ok) {
        if (data.detail && data.detail.includes("temporariamente indisponível")) {
          throw new Error("O serviço gratuito está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium.");
        }
        throw new Error(data.detail || 'Erro ao avaliar o prompt');
      }

      if (data && data.evaluation) {
        console.log('Scores recebidos:', data.evaluation.clarity_score, data.evaluation.context_score, data.evaluation.effectiveness_score);
        console.log('Análise detalhada recebida:', data.evaluation.detailed_analysis);

        // Se a análise detalhada for uma string, tentamos convertê-la para objeto
        if (typeof data.evaluation.detailed_analysis === 'string') {
          try {
            data.evaluation.detailed_analysis = JSON.parse(data.evaluation.detailed_analysis);
          } catch (e) {
            console.error('Erro ao parsear detailed_analysis:', e);
            // Se falhar, criamos um objeto com a string na propriedade central_objective
            data.evaluation.detailed_analysis = {
              central_objective: data.evaluation.detailed_analysis
            };
          }
        }
        
        setResult(data.evaluation);
        
        // Atualizar o contador de avaliações após avaliação bem-sucedida
        if (!isPremium) {
          await checkFreeStatus();
        }
      } else {
        throw new Error('Estrutura de resposta inválida');
      }
    } catch (error) {
      console.error('Erro:', error);
      showMessage(error instanceof Error ? error.message : 'Erro ao avaliar o prompt', 'error');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleReset = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`/reset/${userId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Falha ao resetar uso');
      }
      const data = await response.json();
      logger.info('Uso resetado');
      showMessage(data.message, 'success');
      await checkPremiumStatus();
      await checkFreeStatus();
    } catch (error) {
      logger.error('Erro ao resetar uso');
      showMessage('Não foi possível resetar o uso', 'error');
    }
  };

  // Função para abrir o modal premium
  const handleOpenPremiumModal = () => {
    setIsModalOpen(true);
  };

  return (
    <div className="prompt-form-container">
      <div className="prompt-form">
        <h2>Avalie seu prompt</h2>
        
        {evaluationCount !== null && !isPremium && (
          <div className="evaluation-count">
            <span>{maxFreeEvaluations - (evaluationCount || 0)}/{maxFreeEvaluations} avaliações restantes</span>
            {evaluationCount >= maxFreeEvaluations / 2 && (
              <button 
                className="btn btn-secondary" 
                onClick={openPremiumModal || handleOpenPremiumModal}
              >
                <SparkleIcon /> Comprar Premium
              </button>
            )}
          </div>
        )}
        
        {isPremium && (
          <div className="evaluation-count premium-count">
            <span>Uso ilimitado (Plano Premium)</span>
          </div>
        )}
        
        {evaluationCount !== null && evaluationCount >= maxFreeEvaluations && !isPremium && (
          <p className="prompt-status error">
            <AlertIcon />
            Limite diário de {maxFreeEvaluations} avaliações gratuitas atingido
          </p>
        )}
        
        <form onSubmit={(e) => e.preventDefault()}>
          <div className="form-group">
            <label htmlFor="prompt">Prompt*</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Digite seu prompt aqui..."
              className="form-control"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="model">Modelo LLM*</label>
            <select
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="form-control"
            >
              <option value="">Selecione o modelo LLM</option>
              <option value="gpt-3.5-turbo">GPT-3.5</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              <option value="claude-3-haiku">Claude 3 Haiku</option>
              <option value="gemini-pro">Gemini Pro</option>
              <option value="gemini-ultra">Gemini Ultra</option>
              <option value="llama-3-70b">Llama 3 70B</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="context">Contexto (opcional)</label>
            <textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Adicione contexto adicional para melhor avaliação..."
              className="form-control"
            />
          </div>
          
          {error && error.trim() !== "" && (
            <div className="message error">
              <AlertIcon /> {error}
            </div>
          )}
          
          <div className="form-actions">
            <button 
              type="button"
              onClick={handleSubmit} 
              disabled={isEvaluating || !prompt.trim() || !model} 
              className="btn btn-primary"
            >
              {isEvaluating ? 'Avaliando...' : 'Avaliar Prompt'}
              {!isEvaluating && <SendIcon />}
            </button>
            
            <button 
              type="button"
              onClick={handleReset} 
              disabled={isEvaluating || (!prompt.trim() && !context.trim())} 
              className="btn btn-secondary"
            >
              <ResetIcon /> Limpar
            </button>
            
            {!isPremium && (
              <button
                type="button"
                onClick={openPremiumModal || handleOpenPremiumModal}
                className="btn premium-button"
              >
                <SparkleIcon /> Premium
              </button>
            )}
          </div>
        </form>
      </div>
      
      {isModalOpen && <PremiumModal onClose={() => setIsModalOpen(false)} refreshPage={true} />}
      
      {isEvaluating && (
        <ThinkingAnimation message="Analisando seu prompt com inteligência artificial..." />
      )}
      
      {result && <EvaluationResult result={result} />}
    </div>
  );
};

export default PromptForm; 