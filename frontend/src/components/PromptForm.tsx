import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import PremiumModal from './PremiumModal';
import EvaluationResult from './EvaluationResult';

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
}

interface PromptEvaluation {
  clarity_score: number;
  context_score: number;
  effectiveness_score: number;
  suggestions: string[];
  optimized_prompt: string;
}

const PromptForm: React.FC<PromptFormProps> = ({ userId }) => {
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState('');
  const [targetLLM, setTargetLLM] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<PromptEvaluation | null>(null);
  const [canUsePremium, setCanUsePremium] = useState(false);
  const [premiumMessage, setPremiumMessage] = useState('');
  const [canUseFree, setCanUseFree] = useState(true);
  const [freeMessage, setFreeMessage] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [hasPremiumExpired, setHasPremiumExpired] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

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
          const userData = await response.json();
          setIsAdmin(userData.is_admin === true);
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
      if (!token) {
        setCanUsePremium(false);
        setPremiumMessage('Login necessário para acesso premium');
        return;
      }
      
      const response = await fetch(`/premium/status/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Erro ao verificar status premium');
      }
      
      const data = await response.json();
      setCanUsePremium(data.can_use);
      setPremiumMessage(data.message);
      setHasPremiumExpired(data.has_expired);
      
      if (data.has_expired && data.message.includes('Limite de ativações premium atingido')) {
        setIsModalOpen(true);
      }
    } catch (error) {
      console.error('Erro ao verificar status premium:', error);
      setPremiumMessage('Não foi possível verificar o status premium');
      setCanUsePremium(false);
      showMessage('Erro ao verificar status premium', 'error');
    }
  };

  const checkFreeStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setCanUseFree(false);
        setFreeMessage('Login necessário para usar o sistema');
        return;
      }
      
      const response = await fetch(`/free/status/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Falha ao verificar status gratuito');
      }
      
      const data = await response.json();
      setCanUseFree(data.can_use_free);
      setFreeMessage(data.message);
    } catch (error) {
      logger.error('Erro ao verificar status gratuito');
      showMessage('Não foi possível verificar o status gratuito', 'error');
    }
  };

  const activatePremium = async () => {
    if (hasPremiumExpired) {
      setIsModalOpen(true);
      return;
    }

    try {
      const response = await fetch(`/premium/activate/${userId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        const data = await response.json();
        if (data.detail === 'premium_expired') {
          setHasPremiumExpired(true);
          setIsModalOpen(true);
          return;
        }
        throw new Error('Falha ao ativar plano premium');
      }
      const data = await response.json();
      logger.info('Plano premium ativado');
      showMessage(data.message, 'success');
      await checkPremiumStatus();
    } catch (error) {
      logger.error('Erro ao ativar plano premium');
      showMessage('Não foi possível ativar o plano premium', 'error');
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (prompt.trim().length < 10) {
      showMessage('O prompt deve ter pelo menos 10 caracteres', 'error');
      return;
    }

    if (!targetLLM) {
      showMessage('Por favor, selecione o modelo LLM', 'error');
      return;
    }

    setIsLoading(true);
    setError(null);
    setEvaluation(null);

    try {
      const response = await fetch('/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: prompt,
          context: context || undefined,
          plan_type: canUsePremium ? "premium" : "free",
          user_id: userId,
          target_llm: targetLLM,
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
        setEvaluation(data.evaluation);
      } else {
        throw new Error('Estrutura de resposta inválida');
      }
    } catch (error) {
      console.error('Erro:', error);
      showMessage(error instanceof Error ? error.message : 'Erro ao avaliar o prompt', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const resetUsage = async () => {
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

  return (
    <>
      <div className="form-section">
        <div className="form-section-header">
          <div className={`status-badge ${canUsePremium ? 'premium' : 'free'}`}>
            {canUsePremium ? 'Premium' : 'Gratuito'}
          </div>
          <p className="status-message">
            {canUsePremium ? premiumMessage : canUseFree ? freeMessage : 'Limite de uso gratuito atingido'}
          </p>
        </div>

        {error && (
          <div className="error-message error">
            <AlertIcon />
            {error}
          </div>
        )}

        <form className="prompt-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="prompt">Prompt*</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Digite seu prompt aqui..."
              required
              disabled={!canUsePremium && !canUseFree}
            />
          </div>

          <div className="form-group">
            <label htmlFor="targetLLM">Modelo LLM*</label>
            <select
              id="targetLLM"
              value={targetLLM}
              onChange={(e) => setTargetLLM(e.target.value)}
              required
              disabled={!canUsePremium && !canUseFree}
            >
              <option value="">Selecione o modelo LLM</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              <option value="claude-3-haiku">Claude 3 Haiku</option>
              <option value="gemini-pro">Gemini Pro</option>
              <option value="gemini-ultra">Gemini Ultra</option>
              <option value="llama3">Llama 3</option>
              <option value="mistral-large">Mistral Large</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="context">Contexto (opcional)</label>
            <textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Adicione contexto adicional para melhor avaliação..."
              disabled={!canUsePremium && !canUseFree}
            />
          </div>

          <div className="button-group">
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading || (!canUsePremium && !canUseFree)}
            >
              {isLoading ? <><div className="spinner"></div>Avaliando...</> : <><SendIcon />Avaliar Prompt</>}
            </button>
            
            {hasPremiumExpired && (
              <button
                type="button"
                className="premium-button"
                onClick={() => setIsModalOpen(true)}
                disabled={isLoading}
              >
                <SparkleIcon />
                Assinar Premium
              </button>
            )}
            
            {isAdmin && (
              <button
                type="button"
                className="reset-button"
                onClick={resetUsage}
                disabled={isLoading}
              >
                <ResetIcon />
                Resetar Uso (Admin)
              </button>
            )}
          </div>
        </form>
      </div>

      {evaluation && (
        <div className="feedback-section">
          <EvaluationResult result={evaluation} />
        </div>
      )}

      {isModalOpen && (
        <PremiumModal 
          onClose={() => setIsModalOpen(false)} 
          refreshPage={true}
        />
      )}
    </>
  );
};

export default PromptForm; 