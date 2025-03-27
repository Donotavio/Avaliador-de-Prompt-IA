import { isTokenExpired } from './tokenUtils';
import { notifyTokenExpired } from './auth';

// URL base da API
export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? '/api'  // Usando caminho relativo em produção
  : 'http://localhost:8000/api';

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
    // Verifica se o token está expirado antes de incluí-lo
    const token = localStorage.getItem('token');
    if (token && !isTokenExpired(token)) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      // Se o token estiver expirado, notifica o sistema
      setTimeout(() => notifyTokenExpired(), 0);
    }
  }

  // Adicionar token CSRF se disponível
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  return headers;
};

// Wrapper para fetch que verifica tokens antes de fazer requisições
export const apiFetch = async (
  url: string, 
  options: RequestInit = {}
): Promise<Response> => {
  // Verifica se o token está expirado
  const token = localStorage.getItem('token');
  if (token && isTokenExpired(token)) {
    // Tenta fazer refresh do token
    try {
      // Importação dinâmica para evitar dependência circular
      const { refreshToken } = await import('./auth');
      const refreshed = await refreshToken();
      if (!refreshed) {
        notifyTokenExpired();
        throw new Error('Token expirado e não foi possível atualizá-lo');
      }
    } catch (error) {
      notifyTokenExpired();
      throw error;
    }
  }

  // Mescla cabeçalhos padrão com os fornecidos
  const headers = {
    ...getHeaders(),
    ...(options.headers || {})
  };

  // Faz a requisição com os cabeçalhos atualizados
  const response = await fetch(
    url.startsWith('http') ? url : `${API_BASE_URL}${url}`,
    {
      ...options,
      headers,
      credentials: 'include'
    }
  );

  // Se a resposta for 401 (Unauthorized), notifica o sistema
  if (response.status === 401) {
    notifyTokenExpired();
  }

  return response;
};

// Interface para dados de avaliação de prompt
export interface PromptRequest {
  content: string;
  target_llm?: string;
  user_id: string;
  evaluation_criteria?: string[];
  context?: string;
  plan_type?: string;
}

export interface PromptResponse {
  score?: number;
  feedback?: string;
  suggestions?: string[];
  improved_prompt?: string;
  execution_time?: number;
  evaluation_id?: string;
  
  // Campos para o formato alternativo de resposta
  original_prompt?: {
    content: string;
    context?: string;
    plan_type: string;
    user_id: string;
    target_llm: string;
  };
  evaluation?: {
    clarity_score: number;
    context_score: number;
    effectiveness_score: number;
    suggestions: string[];
    optimized_prompt: string;
    detailed_analysis?: any;
  };
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
      // Garantir que plan_type existe
      plan_type: promptData.plan_type || 'free',
      // Remover campos undefined/null
      context: promptData.context || undefined
    };

    console.log('Enviando payload para API:', payload);

    // Usa o apiFetch em vez do fetch direto
    const response = await apiFetch('/prompts/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log('Endpoint /prompts/evaluate não encontrado, tentando /evaluate');
        // Tentar endpoint alternativo
        const fallbackResponse = await apiFetch('/evaluate', {
          method: 'POST',
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