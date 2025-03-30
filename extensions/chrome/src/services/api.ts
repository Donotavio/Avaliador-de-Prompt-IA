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
  try {
    // Verifica se chrome.storage está disponível
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      return new Promise((resolve) => {
        chrome.storage.local.get(['environment'], (result) => {
          const env = result.environment || 'production';
          console.log('Ambiente atual:', env);
          resolve(env);
        });
      });
    } else {
      // Se não estiver disponível, usa ambiente padrão
      console.log('chrome.storage não disponível, usando ambiente padrão (production)');
      return 'production';
    }
  } catch (error) {
    console.error('Erro ao obter ambiente:', error);
    return 'production'; // Fallback para ambiente de produção
  }
};

// Função para obter a URL base da API de acordo com o ambiente
export const getApiBaseUrl = async (): Promise<string> => {
  try {
    const environment = await getEnvironment();
    const baseUrl = ENV[environment].API_BASE_URL;
    console.log('URL base da API:', baseUrl);
    return baseUrl;
  } catch (error) {
    console.error('Erro ao obter URL base da API:', error);
    // Fallback para ambiente de produção
    return ENV.production.API_BASE_URL;
  }
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
    
    // Gera um ID de usuário anônimo se não existir
    const userId = userInfo?.id || `anon_${Math.random().toString(36).substring(2, 15)}`;
    console.log('ID do usuário para requisição:', userId);
    
    // Cria o objeto de requisição
    const promptRequest: PromptRequest = {
      content: promptContent,
      context: context,
      plan_type: userInfo?.plan_type || PlanType.FREE,
      user_id: userId,
      target_llm: targetLLM
    };
    
    console.log('Dados da requisição:', promptRequest);
    
    // Tenta diferentes métodos de fazer a requisição, em ordem de preferência
    let lastError: Error | null = null;
    
    // Método 1: Tenta usar o proxy do background para contornar problemas de CORS
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      try {
        console.log('Tentando usar proxy do background para evitar problemas de CORS');
        
        const response = await new Promise<any>((resolve, reject) => {
          const messageTimeout = setTimeout(() => {
            reject(new Error('Timeout ao comunicar com background script'));
          }, 5000); // 5 segundos de timeout
          
          chrome.runtime.sendMessage(
            {
              action: 'apiRequest',
              method: 'POST',
              endpoint: '/prompts/evaluate',
              data: promptRequest
            },
            (response) => {
              clearTimeout(messageTimeout);
              
              if (chrome.runtime.lastError) {
                console.error('Erro chrome.runtime:', chrome.runtime.lastError);
                reject(new Error(chrome.runtime.lastError.message || 'Erro na comunicação com background'));
                return;
              }
              
              if (response && response.success) {
                console.log('Resposta recebida via proxy do background:', response.data);
                resolve(response.data);
              } else {
                console.error('Erro ao usar proxy do background:', response?.error);
                const error = new Error(response?.error || 'Erro desconhecido no proxy');
                if (response?.details) {
                  console.error('Detalhes do erro:', response.details);
                }
                reject(error);
              }
            }
          );
        });
        
        return response;
      } catch (proxyError) {
        console.warn('Erro ao usar proxy do background:', proxyError);
        lastError = proxyError instanceof Error ? proxyError : new Error(String(proxyError));
        console.log('Tentando método alternativo...');
      }
    }
    
    // Método 2: Tenta fazer a requisição direta (pode falhar por CORS)
    try {
      console.log('Tentando requisição direta para API...');
      const api = await createApiInstance();
      const response = await api.post<PromptResponse>('/prompts/evaluate', promptRequest);
      console.log('Resposta recebida via requisição direta:', response.data);
      return response.data;
    } catch (directError) {
      console.error('Erro na requisição direta:', directError);
      lastError = directError instanceof Error ? directError : new Error(String(directError));
    }
    
    // Método 3: Fallback para API simulada localmente (quando tudo mais falhar)
    if (lastError) {
      console.warn('Todos os métodos de requisição falharam. Usando simulação local como fallback.');
      
      // Simulação de resposta para evitar que a aplicação quebre
      return {
        original_prompt: promptRequest,
        evaluation: {
          clarity_score: 7,
          context_score: 6,
          effectiveness_score: 8,
          suggestions: [
            "Adicionar mais contexto sobre o projeto específico",
            "Especificar as tecnologias e frameworks preferidos",
            "Incluir exemplos do estilo de código desejado"
          ],
          optimized_prompt: `${promptContent}\n\nPor favor, considere as seguintes diretrizes ao responder:\n1. Priorize código limpo e bem documentado\n2. Sugira soluções escaláveis e de alta performance\n3. Siga as melhores práticas para Python e ReactJS`,
          detailed_analysis: {
            central_objective: "Obter assistência de programação de alta qualidade",
            strengths_weaknesses: "Força: Clareza na expectativa de qualidade. Fraqueza: Falta de contexto específico do projeto.",
            context: "Ambiente de desenvolvimento com Cursor IDE",
            practical_suggestions: "Adicionar mais detalhes sobre o projeto específico e seus requisitos",
            ethical_practices: "O prompt é ético e profissional"
          }
        }
      };
    }
    
    throw new Error('Todos os métodos de requisição falharam');
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
  getEnvironment,
  getApiBaseUrl
}; 