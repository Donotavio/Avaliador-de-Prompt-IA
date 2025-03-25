// Definir URL da API com base no ambiente
export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://avaliadorprompt.com/api'  // URL de produção
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
    // Verificar se estamos em desenvolvimento e retornar um token fictício
    if (process.env.NODE_ENV === 'development') {
      console.log('Ambiente de desenvolvimento: usando token CSRF fictício');
      return 'desenvolvimento-csrf-token';
    }
    
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
    // Em desenvolvimento, retornar um token fictício em caso de erro
    if (process.env.NODE_ENV === 'development') {
      console.log('Usando token CSRF fictício após erro');
      return 'desenvolvimento-csrf-token-fallback';
    }
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
  target_llm: string;
  plan_type: PlanType;
  user_id?: string;
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

    // Garantir que temos os campos necessários
    const payload = {
      ...promptData,
      // Garantir que target_llm existe (o backend espera isso)
      target_llm: promptData.target_llm || 'gpt-4',
      // Garantir que user_id existe (o backend exige isso)
      user_id: promptData.user_id || 'anon',
      // Remover campos undefined/null
      context: promptData.context || undefined
    };

    console.log('Enviando payload para API:', payload);

    const response = await fetch(`${API_BASE_URL}/prompts/evaluate`, {
      method: 'POST',
      credentials: 'include', // Importante para incluir cookies
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log('Endpoint /prompts/evaluate não encontrado, tentando /evaluate');
        // Tentar endpoint alternativo
        const fallbackResponse = await fetch(`${API_BASE_URL}/evaluate`, {
          method: 'POST',
          credentials: 'include',
          headers: getHeaders(),
          body: JSON.stringify(payload),
        });
        
        if (!fallbackResponse.ok) {
          throw new Error(`Erro na API: ${fallbackResponse.statusText}`);
        }
        
        return await fallbackResponse.json();
      }
      throw new Error(`Erro na API: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    throw error;
  }
}; 