import React from 'react';
import ReactDOM from 'react-dom/client';
import { detectTextAreas } from '../utils/llmSites';
import Button from '../components/Button/Button';
import SidePanel from '../components/SidePanel/SidePanel';

// Interface para controlar o estado da aplicação
interface AppState {
  isOpen: boolean;
  prompt: string;
  activeTextArea: HTMLElement | null;
}

// Classe para gerenciar a extensão no content script
class PromptEvaluatorApp {
  private state: AppState = {
    isOpen: false,
    prompt: '',
    activeTextArea: null
  };
  
  private root: ReactDOM.Root | null = null;
  private container: HTMLDivElement | null = null;
  private observer: MutationObserver | null = null;
  
  constructor() {
    this.initialize();
  }
  
  /**
   * Inicializa a aplicação
   */
  private initialize(): void {
    console.log('Inicializando Avaliador de Prompts');
    
    // Criar o container
    this.createContainer();
    
    // Configurar o observador para detectar mudanças no DOM
    this.setupObserver();
    
    // Iniciar o processo de detecção
    this.detectAndAddButtons();
    
    // Detectar novos elementos a cada 3 segundos (como fallback)
    setInterval(() => this.detectAndAddButtons(), 3000);
  }
  
  /**
   * Cria o container para a aplicação React
   */
  private createContainer(): void {
    this.container = document.createElement('div');
    this.container.id = 'prompt-evaluator-container';
    document.body.appendChild(this.container);
    
    // Inicializa o root do React
    this.root = ReactDOM.createRoot(this.container);
    this.renderApp();
  }
  
  /**
   * Configura o observador de mutação para detectar alterações no DOM
   */
  private setupObserver(): void {
    this.observer = new MutationObserver((mutations) => {
      let shouldDetect = false;
      
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          shouldDetect = true;
          break;
        }
      }
      
      if (shouldDetect) {
        this.detectAndAddButtons();
      }
    });
    
    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
  
  /**
   * Detecta áreas de texto e adiciona botões a elas
   */
  private detectAndAddButtons(): void {
    const textAreas = detectTextAreas();
    
    textAreas.forEach(textArea => {
      if (!textArea.dataset.promptEvaluatorButton) {
        // Marca o elemento para evitar duplicação
        textArea.dataset.promptEvaluatorButton = 'true';
        
        // Adiciona o botão adjacente ao textarea
        this.addButtonToTextArea(textArea);
      }
    });
  }
  
  /**
   * Adiciona um botão flutuante a uma área de texto
   */
  private addButtonToTextArea(textArea: HTMLElement): void {
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('prompt-evaluator-button-container');
    buttonContainer.style.position = 'relative';
    
    // Adiciona o container como um irmão adjacente
    if (textArea.parentNode) {
      // Calcula posição
      const rect = textArea.getBoundingClientRect();
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
      
      const buttonRoot = ReactDOM.createRoot(buttonContainer);
      buttonRoot.render(
        <Button 
          position={{
            bottom: 10,
            right: 10
          }}
          onClick={() => this.handleButtonClick(textArea)}
        />
      );
      
      // Se o textarea já estiver em um container com position relative
      // adiciona o botão como filho
      if (getComputedStyle(textArea.parentNode as Element).position === 'relative') {
        textArea.parentNode.appendChild(buttonContainer);
      } else {
        // Caso contrário, cria um wrapper
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        textArea.parentNode.insertBefore(wrapper, textArea);
        wrapper.appendChild(textArea);
        wrapper.appendChild(buttonContainer);
      }
    }
  }
  
  /**
   * Manipula o clique no botão de avaliação
   */
  private handleButtonClick(textArea: HTMLElement): void {
    // Obtém o conteúdo do textarea
    let promptContent = '';
    
    if (textArea instanceof HTMLTextAreaElement) {
      promptContent = textArea.value;
    } else if (textArea.getAttribute('contenteditable') === 'true') {
      promptContent = textArea.textContent || '';
    } else if (textArea.textContent) {
      promptContent = textArea.textContent;
    }
    
    if (promptContent.trim()) {
      this.setState({
        isOpen: true,
        prompt: promptContent,
        activeTextArea: textArea
      });
    } else {
      console.warn('Área de texto vazia');
      // Opcional: mostrar um alerta ao usuário
    }
  }
  
  /**
   * Fecha o painel lateral
   */
  private handleClose = (): void => {
    this.setState({ isOpen: false });
  };
  
  /**
   * Aplica o prompt otimizado à área de texto ativa
   */
  private handleApply = (optimizedPrompt: string): void => {
    if (this.state.activeTextArea) {
      const textArea = this.state.activeTextArea;
      
      if (textArea instanceof HTMLTextAreaElement) {
        textArea.value = optimizedPrompt;
        
        // Dispara um evento de input para acionar handlers
        const event = new Event('input', { bubbles: true });
        textArea.dispatchEvent(event);
      } else if (textArea.getAttribute('contenteditable') === 'true') {
        textArea.textContent = optimizedPrompt;
        
        // Dispara um evento de input para acionar handlers
        const event = new InputEvent('input', { bubbles: true });
        textArea.dispatchEvent(event);
      }
    }
    
    // Fecha o painel após aplicar
    this.setState({ isOpen: false });
  };
  
  /**
   * Atualiza o estado da aplicação e renderiza novamente
   */
  private setState(newState: Partial<AppState>): void {
    this.state = { ...this.state, ...newState };
    this.renderApp();
  }
  
  /**
   * Renderiza o componente React
   */
  private renderApp(): void {
    if (this.root) {
      this.root.render(
        <SidePanel
          isOpen={this.state.isOpen}
          prompt={this.state.prompt}
          onClose={this.handleClose}
          onApply={this.handleApply}
        />
      );
    }
  }
}

// Inicializa a aplicação quando o DOM estiver totalmente carregado
window.addEventListener('load', () => {
  new PromptEvaluatorApp();
}); 