import { PlanType } from '../types';
import api from '../services/api';

console.log('Inicializando background service');

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
    console.log('Dados do usuário inicializados:', defaultUserInfo);
    
    // Define o ambiente como produção por padrão
    await api.setEnvironment('production');
    console.log('Ambiente inicial definido como produção');
    
    // Abre a página de boas-vindas
    chrome.tabs.create({
      url: 'https://avaliadorprompt.com/welcome'
    });
  } else if (details.reason === 'update') {
    console.log('Avaliador de Prompts atualizado');
    
    // Verifica se já temos dados do usuário
    const { userInfo } = await chrome.storage.local.get(['userInfo']);
    
    // Se não tiver, inicializa com valores padrão
    if (!userInfo) {
      await chrome.storage.local.set({ userInfo: defaultUserInfo });
      console.log('Dados do usuário inicializados após atualização:', defaultUserInfo);
    } else {
      console.log('Dados do usuário existentes mantidos:', userInfo);
    }
  }
});

// Escuta mensagens do content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Mensagem recebida:', message, 'de:', sender?.tab?.url || 'popup');
  
  // Mensagem para verificar o status do usuário
  if (message.action === 'checkUserStatus') {
    console.log('Verificando status do usuário...');
    checkUserStatus()
      .then(status => {
        console.log('Status do usuário obtido:', status);
        sendResponse(status);
      })
      .catch(error => {
        console.error('Erro ao verificar status:', error);
        sendResponse({ error: 'Erro ao verificar status' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }
  
  // Mensagem para avaliar um prompt
  if (message.action === 'evaluatePrompt') {
    console.log('Avaliando prompt:', message.prompt.substring(0, 50) + '...');
    evaluatePrompt(message.prompt, message.targetLLM)
      .then(result => {
        console.log('Avaliação concluída com sucesso');
        sendResponse(result);
      })
      .catch(error => {
        console.error('Erro ao avaliar prompt:', error);
        sendResponse({ error: 'Erro ao avaliar prompt' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }

  // Alternar entre ambientes (desenvolvimento/produção)
  if (message.action === 'setEnvironment') {
    console.log('Alterando ambiente para:', message.environment);
    api.setEnvironment(message.environment)
      .then(() => {
        console.log(`Ambiente alterado para: ${message.environment}`);
        sendResponse({ success: true, environment: message.environment });
      })
      .catch(error => {
        console.error('Erro ao alterar ambiente:', error);
        sendResponse({ error: 'Erro ao alterar ambiente' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }

  // Obter ambiente atual
  if (message.action === 'getEnvironment') {
    console.log('Obtendo ambiente atual...');
    api.getEnvironment()
      .then(environment => {
        console.log('Ambiente atual:', environment);
        sendResponse({ environment });
      })
      .catch(error => {
        console.error('Erro ao obter ambiente:', error);
        sendResponse({ error: 'Erro ao obter ambiente' });
      });
    
    return true; // Indica que a resposta será assíncrona
  }
});

// Função para verificar o status do usuário
async function checkUserStatus() {
  try {
    // Obtém informações do usuário armazenadas localmente
    const userInfo = await api.getUserInfo();
    console.log('Informações do usuário obtidas:', userInfo);
    
    if (!userInfo || !userInfo.id) {
      console.log('Usuário não identificado, retornando status padrão');
      return defaultUserInfo;
    }
    
    try {
      // Usa o serviço de API para verificar o status
      console.log('Verificando status no servidor para usuário:', userInfo.id);
      const status = await api.checkUserStatus(userInfo.id);
      console.log('Status recebido do servidor:', status);
      
      // Atualiza as informações locais do usuário
      const updatedUserInfo = {
        ...userInfo,
        remaining_evaluations: status.remaining_evaluations,
        is_premium: status.is_premium,
        plan_type: status.plan_type
      };
      
      await api.saveUserInfo(updatedUserInfo);
      console.log('Informações do usuário atualizadas:', updatedUserInfo);
      
      return updatedUserInfo;
    } catch (error) {
      console.error('Erro ao verificar status do usuário:', error);
      // Retorna informações locais se não conseguir se comunicar com o backend
      return userInfo;
    }
  } catch (error) {
    console.error('Erro ao obter informações do usuário:', error);
    return defaultUserInfo;
  }
}

// Função para avaliar um prompt
async function evaluatePrompt(content: string, targetLLM: string = 'general') {
  try {
    // Verifica o status do usuário
    console.log('Verificando status do usuário antes da avaliação');
    const userInfo = await checkUserStatus();
    
    // Verifica se o usuário tem avaliações disponíveis
    if (userInfo.remaining_evaluations <= 0 && userInfo.plan_type === PlanType.FREE) {
      console.log('Limite de avaliações atingido para usuário gratuito');
      return {
        error: 'Limite de avaliações atingido',
        errorType: 'LIMIT_REACHED'
      };
    }
    
    // Usa o serviço de API para avaliar o prompt
    console.log('Enviando prompt para avaliação');
    const result = await api.evaluatePrompt(content, targetLLM);
    console.log('Avaliação concluída com sucesso');
    
    // Atualiza o contador de avaliações restantes
    if (userInfo.plan_type === PlanType.FREE) {
      console.log('Atualizando contador de avaliações para usuário gratuito');
      const updatedUserInfo = {
        ...userInfo,
        remaining_evaluations: userInfo.remaining_evaluations - 1
      };
      
      await api.saveUserInfo(updatedUserInfo);
      console.log('Contador atualizado:', updatedUserInfo.remaining_evaluations);
    }
    
    return result;
  } catch (error) {
    console.error('Erro ao avaliar prompt:', error);
    throw error;
  }
}

export default {
  checkUserStatus,
  evaluatePrompt
}; 