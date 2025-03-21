// Definir URL da API com base no ambiente
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://avaliadorprompt.com.br/api'  // URL de produção
  : 'http://localhost:8000/api';          // URL de desenvolvimento

// Armazenamento do token CSRF
let csrfToken: string | null = null;

// Função para atualizar o token CSRF
export const setCsrfToken = (token: string) => {
  csrfToken = token;
};

// Função para obter token CSRF do servidor
export const fetchCsrfToken = async (): Promise<string> => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/csrf-token`, {
      method: 'GET',
      credentials: 'include', // Importante para incluir cookies
      headers: {
        'Content-Type': 'application/json',
        // Incluir token de autenticação se disponível
        ...(localStorage.getItem('token') && {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        })
      }
    });

    if (!response.ok) {
      throw new Error(`Erro ao obter token CSRF: ${response.statusText}`);
    }

    const data = await response.json();
    csrfToken = data.csrf_token;
    return data.csrf_token; // Retornar o valor diretamente
  } catch (error) {
    console.error('Erro ao obter token CSRF:', error);
    throw error;
  }
};

// Função auxiliar para incluir cabeçalhos comuns, incluindo CSRF
const getHeaders = (includeAuth: boolean = true): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Adicionar token de autenticação se disponível e solicitado
  if (includeAuth && localStorage.getItem('token')) {
    headers['Authorization'] = `Bearer ${localStorage.getItem('token')}`;
  }

  // Adicionar token CSRF se disponível
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  return headers;
};

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
    // Obter token CSRF se não estiver disponível
    if (!csrfToken) {
      try {
        await fetchCsrfToken();
      } catch (e) {
        console.warn('Não foi possível obter token CSRF. Tentando continuar sem ele.');
      }
    }

    const response = await fetch(`${API_BASE_URL}/prompts/evaluate`, {
      method: 'POST',
      credentials: 'include', // Importante para incluir cookies
      headers: getHeaders(),
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