import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import PremiumModal from './PremiumModal';

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

  useEffect(() => {
    const checkStatus = async () => {
      await checkPremiumStatus();
      await checkFreeStatus();
    };
    checkStatus();
  }, [userId]); // eslint-disable-line react-hooks/exhaustive-deps

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
      const response = await fetch(`/premium/status/${userId}`);
      if (!response.ok) {
        throw new Error('Erro ao verificar status premium');
      }
      const data = await response.json();
      setCanUsePremium(data.can_use);
      setPremiumMessage(data.message);
      setHasPremiumExpired(data.has_expired);
    } catch (error) {
      console.error('Erro ao verificar status premium:', error);
      setPremiumMessage('Não foi possível verificar o status premium');
      setCanUsePremium(false);
      showMessage('Erro ao verificar status premium', 'error');
    }
  };

  const checkFreeStatus = async () => {
    try {
      const response = await fetch(`/free/status/${userId}`);
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

      if (!response.ok) {
        if (data.detail && data.detail.includes("temporariamente indisponível")) {
          throw new Error("O serviço gratuito está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium.");
        }
        throw new Error(data.detail || 'Erro ao avaliar o prompt');
      }

      setEvaluation(data.evaluation);
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
      <form className="prompt-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <div className={`status-badge ${canUsePremium ? 'premium' : 'free'}`}>
            {canUsePremium ? 'Premium' : 'Gratuito'}
          </div>
          <p className="status-message">
            {canUsePremium ? premiumMessage : canUseFree ? freeMessage : 'Limite de uso gratuito atingido'}
          </p>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

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
              {isLoading ? 'Avaliando...' : 'Avaliar Prompt'}
            </button>
            
            {!canUsePremium && !hasPremiumExpired && (
              <button
                type="button"
                className="premium-button"
                onClick={activatePremium}
                disabled={isLoading}
              >
                Ativar Premium
              </button>
            )}

            {hasPremiumExpired && (
              <button
                type="button"
                className="premium-button"
                onClick={() => setIsModalOpen(true)}
                disabled={isLoading}
              >
                Assinar Premium
              </button>
            )}
            
            <button
              type="button"
              className="reset-button"
              onClick={resetUsage}
              disabled={isLoading}
            >
              Resetar Uso
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Avaliando seu prompt...</p>
          </div>
        )}

        {evaluation && (
          <div className="feedback-section">
            <h2>Resultado da Avaliação</h2>
            
            <div className="scores">
              <div className="score-item">
                <h3>Clareza</h3>
                <div className="score-value">{evaluation.clarity_score}/10</div>
              </div>
              
              <div className="score-item">
                <h3>Contexto</h3>
                <div className="score-value">{evaluation.context_score}/10</div>
              </div>
              
              <div className="score-item">
                <h3>Eficácia</h3>
                <div className="score-value">{evaluation.effectiveness_score}/10</div>
              </div>
            </div>
            
            <div className="suggestions">
              <h3>Sugestões</h3>
              <ul>
                {evaluation.suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
            
            <div className="optimized-prompt">
              <h3>Prompt Otimizado</h3>
              <pre>{evaluation.optimized_prompt}</pre>
            </div>
          </div>
        )}
      </form>

      <PremiumModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

export default PromptForm; 