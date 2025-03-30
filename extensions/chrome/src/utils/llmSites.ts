import { LLMSitesMap } from '../types';

export const LLM_SITES: LLMSitesMap = {
  'chatgpt.com': {
    textAreaSelector: 'textarea[data-id="root"]',
    submitButtonSelector: 'button[data-testid="send-button"]'
  },
  'chat.openai.com': {
    textAreaSelector: 'textarea[data-id="root"]',
    submitButtonSelector: 'button[data-testid="send-button"]'
  },
  'claude.ai': {
    textAreaSelector: '.ProseMirror',
    submitButtonSelector: 'button[aria-label="Send message"]'
  },
  'gemini.google.com': {
    textAreaSelector: 'textarea[aria-label="Enviar uma mensagem"], textarea[aria-label="Send a message"]',
    submitButtonSelector: 'button[aria-label="Enviar"], button[aria-label="Send"]'
  },
  'perplexity.ai': {
    textAreaSelector: 'div[contenteditable="true"]',
    submitButtonSelector: 'button[aria-label="Send"]'
  },
  'bing.com': {
    textAreaSelector: '#searchbox',
    submitButtonSelector: '#search_icon'
  },
  'copilot.microsoft.com': {
    textAreaSelector: 'div[contenteditable="true"]',
    submitButtonSelector: 'button[aria-label="Enviar mensagem"], button[aria-label="Send message"]'
  },
  'huggingface.co': {
    textAreaSelector: 'div[contenteditable="true"]',
    submitButtonSelector: 'button[aria-label="Send message"]'
  },
  'poe.com': {
    textAreaSelector: 'div[contenteditable="true"]',
    submitButtonSelector: 'button[aria-label="Submit"]'
  },
  'character.ai': {
    textAreaSelector: 'textarea.chat-input',
    submitButtonSelector: 'button.send-button'
  },
  'grok.com': {
    textAreaSelector: 'div[contenteditable="true"]',
    submitButtonSelector: 'button[aria-label="Send message"]'
  },
  'chat.deepseek.com': {
    textAreaSelector: 'textarea',
    submitButtonSelector: 'button[type="submit"]'
  }
};

export function getCurrentLLMSite(): string | null {
  const hostname = window.location.hostname;
  console.log('Avaliador de Prompts - Detectando site:', hostname);
  
  // Tratar especificamente para chatgpt.com
  if (hostname === 'chatgpt.com' || hostname.endsWith('.chatgpt.com')) {
    console.log('Avaliador de Prompts - Site detectado: chatgpt.com');
    return 'chatgpt.com';
  }
  
  // Verificar domínios exatos
  if (LLM_SITES[hostname]) {
    console.log('Avaliador de Prompts - Site detectado (exato):', hostname);
    return hostname;
  }
  
  // Verificar domínios parciais
  for (const site of Object.keys(LLM_SITES)) {
    if (hostname.includes(site)) {
      console.log('Avaliador de Prompts - Site detectado (parcial):', site);
      return site;
    }
  }
  
  console.log('Avaliador de Prompts - Nenhum site LLM detectado');
  return null;
}

export function detectTextAreas(): HTMLElement[] {
  const currentSite = getCurrentLLMSite();
  const elements: HTMLElement[] = [];
  
  console.log('Avaliador de Prompts - Detectando áreas de texto para site:', currentSite);
  
  if (currentSite && LLM_SITES[currentSite]) {
    const selector = LLM_SITES[currentSite].textAreaSelector;
    console.log('Avaliador de Prompts - Usando seletor:', selector);
    
    const found = document.querySelectorAll(selector);
    console.log('Avaliador de Prompts - Elementos encontrados:', found.length);
    
    found.forEach((element) => {
      if (element instanceof HTMLElement) {
        elements.push(element);
      }
    });
  }
  
  // Seletores específicos para chatgpt.com que podem não estar na configuração padrão
  if (currentSite === 'chatgpt.com' && elements.length === 0) {
    console.log('Avaliador de Prompts - Usando seletores alternativos para chatgpt.com');
    
    const chatgptSelectors = [
      'textarea[data-id="root"]', 
      'textarea[placeholder="Send a message"]',
      'textarea.text-input',
      'div[contenteditable="true"]'
    ];
    
    chatgptSelectors.forEach(selector => {
      const found = document.querySelectorAll(selector);
      console.log(`Avaliador de Prompts - Seletor alternativo ${selector}:`, found.length);
      
      found.forEach(element => {
        if (element instanceof HTMLElement) {
          elements.push(element);
        }
      });
    });
  }
  
  // Lógica de fallback se não encontrarmos elementos específicos
  if (elements.length === 0) {
    console.log('Avaliador de Prompts - Usando seletores genéricos');
    
    const genericSelectors = [
      'textarea:not([readonly])',
      '[contenteditable="true"]',
      '[role="textbox"]'
    ];
    
    genericSelectors.forEach(selector => {
      const found = document.querySelectorAll(selector);
      console.log(`Avaliador de Prompts - Seletor genérico ${selector}:`, found.length);
      
      found.forEach(element => {
        if (element instanceof HTMLElement && 
            element.offsetWidth > 200 && 
            element.offsetHeight > 30) {
          elements.push(element);
        }
      });
    });
  }
  
  console.log('Avaliador de Prompts - Total de áreas de texto encontradas:', elements.length);
  return elements;
} 