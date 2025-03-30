import { PlanType } from '../types';

// Armazena as informações do usuário
interface UserInfo {
  id?: string;
  plan_type: PlanType;
  email?: string;
  remaining_evaluations: number;
}

// Estado inicial do usuário
const defaultUserInfo: UserInfo = {
  plan_type: PlanType.FREE,
  remaining_evaluations: 3
};

// Eventos quando a extensão é instalada ou atualizada
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    console.log('Avaliador de Prompts instalado');
    
    // Inicializa os dados do usuário
    await chrome.storage.local.set({ userInfo: defaultUserInfo });
    
    // Abre a página de boas-vindas
    chrome.tabs.create({
      url: 'https://avaliadorprompt.com.br/welcome'
    });
  } else if (details.reason === 'update') {
    console.log('Avaliador de Prompts atualizado');
    
    // Verifica se já temos dados do usuário
    const { userInfo } = await chrome.storage.local.get(['userInfo']);
    
    // Se não tiver, inicializa com valores padrão
    if (!userInfo) {
      await chrome.storage.local.set({ userInfo: defaultUserInfo });
    }
  }
});

// Escuta mensagens do content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Mensagem para verificar o status do usuário
  if (message.action === 'checkUserStatus') {
    checkUserStatus()
      .then(status => sendResponse(status))
      .catch(error => {
        console.error('Erro ao verificar status:', error);
        sendResponse({ error: 'Erro ao verificar status' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }
  
  // Mensagem para avaliar um prompt
  if (message.action === 'evaluatePrompt') {
    evaluatePrompt(message.prompt, message.targetLLM)
      .then(result => sendResponse(result))
      .catch(error => {
        console.error('Erro ao avaliar prompt:', error);
        sendResponse({ error: 'Erro ao avaliar prompt' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }
});

// Função para verificar o status do usuário
async function checkUserStatus() {
  try {
    // Obtém informações do usuário armazenadas localmente
    const { userInfo } = await chrome.storage.local.get(['userInfo']);
    
    if (!userInfo || !userInfo.id) {
      return defaultUserInfo;
    }
    
    // Faz uma requisição para verificar o status do usuário no backend
    const response = await fetch(`https://api.avaliadorprompt.com.br/api/free/status/${userInfo.id}`);
    
    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }
    
    const status = await response.json();
    
    // Atualiza as informações locais do usuário
    const updatedUserInfo = {
      ...userInfo,
      remaining_evaluations: status.remaining_evaluations,
      is_premium: status.is_premium,
      plan_type: status.plan_type
    };
    
    await chrome.storage.local.set({ userInfo: updatedUserInfo });
    
    return updatedUserInfo;
  } catch (error) {
    console.error('Erro ao verificar status do usuário:', error);
    // Retorna informações locais se não conseguir se comunicar com o backend
    return defaultUserInfo;
  }
}

// Função para avaliar um prompt
async function evaluatePrompt(content: string, targetLLM: string = 'general') {
  try {
    // Verifica o status do usuário
    const userInfo = await checkUserStatus();
    
    // Verifica se o usuário tem avaliações disponíveis
    if (userInfo.remaining_evaluations <= 0 && userInfo.plan_type === PlanType.FREE) {
      return {
        error: 'Limite de avaliações atingido',
        errorType: 'LIMIT_REACHED'
      };
    }
    
    // Obtém o token CSRF
    const csrfResponse = await fetch('https://api.avaliadorprompt.com.br/api/csrf-token');
    const { csrf_token } = await csrfResponse.json();
    
    // Faz a requisição para avaliação
    const response = await fetch('https://api.avaliadorprompt.com.br/api/prompts/evaluate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
      },
      credentials: 'include',
      body: JSON.stringify({
        content,
        plan_type: userInfo.plan_type,
        user_id: userInfo.id,
        target_llm: targetLLM
      })
    });
    
    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    // Atualiza o contador de avaliações restantes
    if (userInfo.plan_type === PlanType.FREE) {
      const updatedUserInfo = {
        ...userInfo,
        remaining_evaluations: userInfo.remaining_evaluations - 1
      };
      
      await chrome.storage.local.set({ userInfo: updatedUserInfo });
    }
    
    return result;
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    throw error;
  }
} 