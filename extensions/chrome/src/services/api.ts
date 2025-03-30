import axios from 'axios';
import { PromptRequest, PromptResponse, UserStatus, PlanType } from '../types';

// Configurações de ambiente
const ENV = {
  development: {
    API_BASE_URL: 'http://localhost:8000/api'
  },
  production: {
    API_BASE_URL: 'https://avaliadorprompt.com/api'
  }
};

console.log('INICIALIZANDO API SERVICE');

// Determina o ambiente atual (pode ser configurado via variável armazenada)
const getEnvironment = async (): Promise<'development' | 'production'> => {
  return new Promise((resolve) => {
    chrome.storage.local.get(['environment'], (result) => {
      const env = result.environment || 'production';
      console.log('Ambiente atual:', env);
      resolve(env);
    });
  });
};

// Função para obter a URL base da API de acordo com o ambiente
const getApiBaseUrl = async (): Promise<string> => {
  const environment = await getEnvironment();
  const baseUrl = ENV[environment].API_BASE_URL;
  console.log('URL base da API:', baseUrl);
  return baseUrl;
};

// Cria uma instância Axios com a URL base atual
const createApiInstance = async () => {
  const baseURL = await getApiBaseUrl();
  console.log('Criando instância Axios com URL:', baseURL);
  
  return axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json'
    },
    withCredentials: false,
    timeout: 10000 // Timeout de 10 segundos
  });
};

// Gera um token CSRF localmente
export const getCSRFToken = async (): Promise<string> => {
  try {
    console.log('Gerando token CSRF localmente...');
    
    // Gera um token aleatório de 32 caracteres
    const randomToken = Array.from(crypto.getRandomValues(new Uint8Array(32)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    console.log('Token CSRF gerado localmente');
    return randomToken;
  } catch (error) {
    console.error('Erro ao gerar token CSRF:', error);
    console.error('Detalhes do erro:', JSON.stringify(error));
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
    console.log('Informações do usuário:', userInfo);
    
    // Cria o objeto de requisição
    const promptRequest: PromptRequest = {
      content: promptContent,
      context: context,
      plan_type: userInfo?.plan_type || PlanType.FREE,
      user_id: userInfo?.id,
      target_llm: targetLLM
    };
    
    console.log('Dados da requisição:', promptRequest);
    
    // Cria a instância da API
    const api = await createApiInstance();
    
    // Faz a requisição para avaliação
    console.log('Enviando requisição para avaliação...');
    const response = await api.post<PromptResponse>('/prompts/evaluate', promptRequest);
    
    console.log('Resposta recebida:', response.data);
    return response.data;
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    console.error('Detalhes do erro:', JSON.stringify(error));
    throw error;
  }
};

// Verifica o status do usuário
export const checkUserStatus = async (userId?: string): Promise<UserStatus> => {
  if (!userId) {
    // Retorna status padrão para usuário anônimo
    console.log('Usuário anônimo, retornando status padrão');
    return {
      remaining_evaluations: 3, // Limite padrão para usuários não autenticados
      is_premium: false,
      plan_type: PlanType.FREE
    };
  }
  
  try {
    const api = await createApiInstance();
    console.log('Verificando status do usuário:', userId);
    const response = await api.get(`/free/status/${userId}`);
    console.log('Status recebido:', response.data);
    return response.data;
  } catch (error) {
    console.error('Erro ao verificar status do usuário:', error);
    console.error('Detalhes do erro:', JSON.stringify(error));
    throw error;
  }
};

// Interface para informações do usuário salvas localmente
interface UserInfo {
  id?: string;
  plan_type: PlanType;
  email?: string;
  remaining_evaluations: number;
}

// Obtém informações do usuário do armazenamento local
export const getUserInfo = async (): Promise<UserInfo | null> => {
  return new Promise((resolve) => {
    try {
      // Verifica se chrome.storage está disponível
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(['userInfo'], (result) => {
          console.log('Informações do usuário obtidas do storage:', result.userInfo);
          resolve(result.userInfo || null);
        });
      } else {
        // Se não estiver disponível, retorna valores padrão
        console.log('chrome.storage não disponível, retornando valores padrão');
        resolve({
          plan_type: PlanType.FREE,
          remaining_evaluations: 3
        });
      }
    } catch (error) {
      console.error('Erro ao obter informações do usuário:', error);
      // Em caso de erro, retorna valores padrão
      resolve({
        plan_type: PlanType.FREE,
        remaining_evaluations: 3
      });
    }
  });
};

// Salva informações do usuário no armazenamento local
export const saveUserInfo = async (userInfo: UserInfo): Promise<void> => {
  return new Promise((resolve) => {
    try {
      // Verifica se chrome.storage está disponível
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ userInfo }, () => {
          console.log('Informações do usuário salvas no storage:', userInfo);
          resolve();
        });
      } else {
        console.log('chrome.storage não disponível, informações não foram salvas');
        resolve();
      }
    } catch (error) {
      console.error('Erro ao salvar informações do usuário:', error);
      resolve();
    }
  });
};

// Define o ambiente atual (desenvolvimento ou produção)
export const setEnvironment = async (environment: 'development' | 'production'): Promise<void> => {
  return new Promise((resolve) => {
    try {
      // Verifica se chrome.storage está disponível
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ environment }, () => {
          console.log('Ambiente alterado para:', environment);
          resolve();
        });
      } else {
        console.log('chrome.storage não disponível, ambiente não foi alterado');
        resolve();
      }
    } catch (error) {
      console.error('Erro ao alterar ambiente:', error);
      resolve();
    }
  });
};

export default {
  evaluatePrompt,
  checkUserStatus,
  getCSRFToken,
  getUserInfo,
  saveUserInfo,
  setEnvironment,
  getEnvironment
}; 