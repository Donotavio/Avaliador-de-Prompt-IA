import axios from 'axios';
import { PromptRequest, PromptResponse, UserStatus, PlanType } from '../types';

const API_BASE_URL = 'https://api.avaliadorprompt.com.br/api';

// Criação de uma instância axios com configurações comuns
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // Para enviar cookies em requisições cross-origin
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  response => response,
  error => {
    // Centraliza o tratamento de erros de rede ou da API
    console.error('Erro na API:', error);
    return Promise.reject(error);
  }
);

// Busca o token CSRF para requisições seguras
export const getCSRFToken = async (): Promise<string> => {
  try {
    const response = await api.get('/csrf-token');
    return response.data.csrf_token;
  } catch (error) {
    console.error('Erro ao obter CSRF token:', error);
    throw error;
  }
};

// Avalia um prompt
export const evaluatePrompt = async (
  promptContent: string,
  targetLLM: string = 'general',
  context: string = ''
): Promise<PromptResponse> => {
  try {
    // Recupera informações do usuário do armazenamento
    const userInfo = await getUserInfo();
    
    // Obtém um token CSRF para segurança
    const csrfToken = await getCSRFToken();
    
    // Cria o objeto de requisição
    const promptRequest: PromptRequest = {
      content: promptContent,
      context: context,
      plan_type: userInfo?.plan_type || PlanType.FREE,
      user_id: userInfo?.id,
      target_llm: targetLLM
    };
    
    // Faz a requisição para avaliação
    const response = await api.post<PromptResponse>('/prompts/evaluate', promptRequest, {
      headers: {
        'X-CSRF-Token': csrfToken
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    throw error;
  }
};

// Verifica o status do usuário
export const checkUserStatus = async (userId?: string): Promise<UserStatus> => {
  if (!userId) {
    // Retorna status padrão para usuário anônimo
    return {
      remaining_evaluations: 3, // Limite padrão para usuários não autenticados
      is_premium: false,
      plan_type: PlanType.FREE
    };
  }
  
  try {
    const response = await api.get(`/free/status/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao verificar status do usuário:', error);
    throw error;
  }
};

// Interface para informações do usuário salvas localmente
interface UserInfo {
  id?: string;
  plan_type: PlanType;
  email?: string;
}

// Obtém informações do usuário do armazenamento local
export const getUserInfo = async (): Promise<UserInfo | null> => {
  return new Promise((resolve) => {
    chrome.storage.local.get(['userInfo'], (result) => {
      resolve(result.userInfo || null);
    });
  });
};

// Salva informações do usuário no armazenamento local
export const saveUserInfo = async (userInfo: UserInfo): Promise<void> => {
  return new Promise((resolve) => {
    chrome.storage.local.set({ userInfo }, () => {
      resolve();
    });
  });
};

export default {
  evaluatePrompt,
  checkUserStatus,
  getCSRFToken,
  getUserInfo,
  saveUserInfo
}; 