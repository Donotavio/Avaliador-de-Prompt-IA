const API_BASE_URL = 'http://localhost:8000/api/v1';

export type PlanType = 'free' | 'premium';

export interface PromptRequest {
  content: string;
  context?: string;
  target_model: string;
  plan_type: PlanType;
}

export interface PromptEvaluation {
  clarity_score: number;
  context_score: number;
  effectiveness_score: number;
  suggestions: string[];
  optimized_prompt: string;
}

export interface PromptResponse {
  original_prompt: PromptRequest;
  evaluation: PromptEvaluation;
}

export const evaluatePrompt = async (
  promptData: PromptRequest
): Promise<PromptResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/prompts/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(promptData),
    });

    if (!response.ok) {
      throw new Error(`Erro na API: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    throw error;
  }
}; 