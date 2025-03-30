// Tipo para os seletores específicos de cada site LLM
export interface LLMSiteSelectors {
  textAreaSelector: string;
  submitButtonSelector: string;
}

// Tipo para o mapeamento de sites LLM
export interface LLMSitesMap {
  [hostname: string]: LLMSiteSelectors;
}

// Tipo para o plano do usuário
export enum PlanType {
  FREE = "free",
  PREMIUM = "premium"
}

// Interface da análise detalhada
export interface DetailedAnalysis {
  central_objective: string;
  strengths_weaknesses: string;
  context: string;
  practical_suggestions: string;
  ethical_practices: string;
}

// Interface para o objeto de requisição de prompt
export interface PromptRequest {
  content: string;
  context?: string;
  plan_type: PlanType;
  user_id?: string;
  target_llm: string;
}

// Interface para a avaliação de prompt
export interface PromptEvaluation {
  clarity_score: number;
  context_score: number;
  effectiveness_score: number;
  suggestions: string[];
  optimized_prompt: string;
  detailed_analysis?: DetailedAnalysis;
}

// Interface para a resposta da API
export interface PromptResponse {
  original_prompt: {
    content: string;
    context?: string;
    plan_type: PlanType;
    user_id?: string;
    target_llm: string;
  };
  evaluation: PromptEvaluation;
}

// Interface para o status do usuário
export interface UserStatus {
  remaining_evaluations: number;
  is_premium: boolean;
  plan_type: PlanType;
} 