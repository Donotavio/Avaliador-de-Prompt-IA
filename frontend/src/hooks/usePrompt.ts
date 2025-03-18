import { useState } from 'react';
import { evaluatePrompt, PromptRequest, PromptResponse } from '../services/api';

interface UsePromptReturn {
  isLoading: boolean;
  error: string | null;
  evaluation: PromptResponse | null;
  evaluateUserPrompt: (promptData: PromptRequest) => Promise<void>;
  resetEvaluation: () => void;
}

export const usePrompt = (): UsePromptReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evaluation, setEvaluation] = useState<PromptResponse | null>(null);

  const evaluateUserPrompt = async (promptData: PromptRequest) => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await evaluatePrompt(promptData);
      setEvaluation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao avaliar o prompt');
      setEvaluation(null);
    } finally {
      setIsLoading(false);
    }
  };

  const resetEvaluation = () => {
    setEvaluation(null);
    setError(null);
  };

  return {
    isLoading,
    error,
    evaluation,
    evaluateUserPrompt,
    resetEvaluation,
  };
}; 