import { LLMSitesMap } from '../types';

export const LLM_SITES: LLMSitesMap = {
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
  
  // Verificar domínios exatos
  if (LLM_SITES[hostname]) {
    return hostname;
  }
  
  // Verificar domínios parciais
  for (const site of Object.keys(LLM_SITES)) {
    if (hostname.includes(site)) {
      return site;
    }
  }
  
  return null;
}

export function detectTextAreas(): HTMLElement[] {
  const currentSite = getCurrentLLMSite();
  const elements: HTMLElement[] = [];
  
  if (currentSite && LLM_SITES[currentSite]) {
    const selector = LLM_SITES[currentSite].textAreaSelector;
    const found = document.querySelectorAll(selector);
    
    found.forEach((element) => {
      if (element instanceof HTMLElement) {
        elements.push(element);
      }
    });
  }
  
  // Lógica de fallback se não encontrarmos elementos específicos
  if (elements.length === 0) {
    const genericSelectors = [
      'textarea:not([readonly])',
      '[contenteditable="true"]',
      '[role="textbox"]'
    ];
    
    genericSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(element => {
        if (element instanceof HTMLElement && 
            element.offsetWidth > 200 && 
            element.offsetHeight > 30) {
          elements.push(element);
        }
      });
    });
  }
  
  return elements;
} 