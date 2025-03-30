# Plano de Implementação: Extensão do Avaliador de Prompts

## Visão Geral
Implementaremos uma extensão de navegador que identifica áreas de texto em sites de LLMs (ChatGPT, Claude, Bard, etc.) e oferece funcionalidade para avaliar e otimizar prompts usando o backend existente do avaliador.

## Funcionalidades Principais
- Detecção automática de sites de LLMs
- Identificação de áreas de texto para entrada de prompts
- Botão flutuante no canto inferior direito da área de texto
- Interface lateral para exibir resultados da avaliação e prompts otimizados
- Integração com o backend existente para processamento de prompts

## Estrutura Técnica

### Frontend (React)
Confirmaremos o uso do React como framework principal para a extensão pelas seguintes razões:
- Compatibilidade com a base de código existente
- Componentização eficiente para interfaces modulares
- Grande ecossistema de bibliotecas e suporte comunitário
- Facilidade de manutenção a longo prazo

#### Dependências React Necessárias
- `react` e `react-dom`: Base do framework
- `@emotion/styled` ou `styled-components`: Para estilização de componentes
- `axios` ou `fetch`: Para chamadas à API do backend
- `react-icons`: Para ícones da interface
- `react-tooltip`: Para tooltips informativos
- `webext-redux`: Para gerenciamento de estado entre os diferentes contextos da extensão
- `@types/chrome`: Para tipagem das APIs do Chrome (em TypeScript)
- `@types/safari-extension`: Para tipagem das APIs do Safari (em TypeScript)

### Integração com Backend
A extensão se comunicará com o backend existente através de endpoints da API, utilizando o esquema de resposta definido em `ConfigOpenAIAssistantFunctionResponse.json`. A extensão utilizará especificamente o campo `optimized_prompt` da resposta, ignorando outros dados retornados pelo assistente.

#### Endpoints do Backend a Serem Utilizados
De acordo com a análise do código backend, os seguintes endpoints serão relevantes:

- **POST /api/prompts/evaluate**: Endpoint principal para avaliação de prompts
- **GET /api/free/status/{user_id}**: Verificação de status/limites do usuário gratuito
- **GET /api/premium/status/{user_id}**: Verificação de status/limites do usuário premium
- **GET /api/csrf-token**: Obtenção de token CSRF para requisições seguras

#### Modelo de Requisição/Resposta
A extensão enviará uma requisição seguindo o modelo `PromptRequest` e receberá respostas no formato `PromptResponse`, focando especificamente no campo `optimized_prompt` para exibir ao usuário.

### Estrutura de Diretórios
```
extensions/
├── chrome/
│   ├── public/
│   │   ├── manifest.json
│   │   ├── icons/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Button/
│   │   │   ├── SidePanel/
│   │   │   ├── PromptEditor/
│   │   ├── contexts/
│   │   │   ├── AuthContext.js
│   │   │   ├── PromptContext.js
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── storage.js
│   │   │   ├── domUtils.js
│   │   ├── utils/
│   │   │   ├── tokenizers.js
│   │   │   ├── security.js
│   │   ├── content-scripts/
│   │   │   ├── index.js
│   │   │   ├── detector.js
│   │   │   ├── injector.js
│   │   ├── background/
│   │   │   ├── index.js
│   │   │   ├── auth.js
│   │   ├── popup/
│   │   │   ├── Popup.js
│   │   │   ├── Settings.js
└── safari/
    ├── (estrutura similar)
```

## Implementação Técnica

### 1. Detecção de Sites LLM

Implementaremos uma lista de padrões de URL e estruturas DOM para identificar sites de LLMs com interfaces interativas onde os usuários podem inserir prompts:

1. **ChatGPT**
   - URL padrão: `*.openai.com/*` (especialmente `chat.openai.com`)
   - URL específica da conversa: `https://chat.openai.com/`
   - Plataforma de conversação da OpenAI com interface direta para GPT-4, GPT-3.5, etc.

2. **Claude**
   - URL padrão: `*.anthropic.com/*` (especialmente `claude.ai`)
   - URL específica da conversa: `https://claude.ai/new`
   - Interface conversacional da Anthropic

3. **Gemini (antigo Bard)**
   - URL padrão: `*.google.com/*` (especialmente `gemini.google.com`)
   - URL específica da conversa: `https://gemini.google.com/app`
   - Interface da Google para acesso ao Gemini

4. **Perplexity AI**
   - URL padrão: `*.perplexity.ai/*`
   - URL específica da conversa: `https://www.perplexity.ai/`
   - Ferramenta de busca e resposta baseada em LLM

5. **Bing Chat / Copilot**
   - URL padrão: `*.bing.com/*`, `copilot.microsoft.com/*`
   - URL específica da conversa: `https://copilot.microsoft.com/`
   - Assistente integrado ao Bing e Microsoft Edge

6. **HuggingChat**
   - URL padrão: `*.huggingface.co/chat/*`
   - URL específica da conversa: `https://huggingface.co/chat/`
   - Interface web para acessar e testar modelos do Hugging Face

7. **Poe**
   - URL padrão: `*.poe.com/*`
   - URL específica da conversa: `https://poe.com`
   - Plataforma que oferece acesso a vários modelos de LLM

8. **Character.AI**
   - URL padrão: `*.character.ai/*`
   - URL específica da conversa: `https://character.ai/`
   - Plataforma para interagir com personagens baseados em IA

9. **Grok**
   - URL padrão: `*.grok.com/*` (especialmente `grok.com`)
   - URL específica da conversa: `https://grok.com`
   - Plataforma de conversação do X.com (antigo twitter) com interface direta para Grok 2, Grok 3, etc.

1. **Deepseek**
   - URL padrão: `*.deepseek.com/*` (especialmente `deepseek.com`)
   - URL específica da conversa: `https://chat.deepseek.com`
   - Plataforma de conversação da Deepseek com interface direta para DeepSeek Coder, DeepSeek-R1, DeepSeek-V3, etc.



Para cada site, manteremos um conjunto específico de seletores DOM para identificar com precisão as áreas de texto:

```javascript
const LLM_SITES = {
  'chat.openai.com': {
    textAreaSelector: 'textarea[data-id="root"]',
    submitButtonSelector: 'button[data-testid="send-button"]'
  },
  'claude.ai': {
    textAreaSelector: '.ProseMirror',
    submitButtonSelector: 'button[aria-label="Send message"]'
  },
  'gemini.google.com': {
    textAreaSelector: 'textarea[aria-label="Enviar uma mensagem"]',
    submitButtonSelector: 'button[aria-label="Enviar"]'
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
    submitButtonSelector: 'button[aria-label="Enviar mensagem"]'
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
  }
};
```

### 2. Identificação de Áreas de Texto
Utilizaremos seletores DOM específicos para cada plataforma LLM para identificar corretamente as áreas de texto de entrada de prompts. Para sites não reconhecidos explicitamente, usaremos uma lógica genérica de detecção de áreas de texto.

```javascript
// Exemplo do detector genérico
function detectTextAreas() {
  // Primeiro tenta os seletores específicos
  const hostname = window.location.hostname;
  if (LLM_SITES[hostname]) {
    return document.querySelectorAll(LLM_SITES[hostname].textAreaSelector);
  }
  
  // Lógica de fallback genérica
  return document.querySelectorAll('textarea:not([readonly]), [contenteditable="true"]');
}
```

### 3. Injeção do Botão Flutuante
Quando uma área de texto válida for detectada, injetaremos um botão flutuante posicionado no canto inferior direito:
- Botão discreto com ícone intuitivo
- Animação suave ao aparecer/desaparecer
- Tooltip explicativo ao passar o mouse

```javascript
function injectButton(textArea) {
  const button = document.createElement('div');
  button.className = 'prompt-evaluator-button';
  button.innerHTML = '<svg>...</svg>'; // Ícone SVG
  button.title = 'Avaliar e otimizar prompt';
  
  // Posicionamento relativo ao textarea
  const rect = textArea.getBoundingClientRect();
  button.style.position = 'absolute';
  button.style.bottom = '10px';
  button.style.right = '10px';
  
  // Anexa ao DOM
  textArea.parentNode.appendChild(button);
  
  // Adiciona evento de clique
  button.addEventListener('click', () => {
    openSidePanel(textArea.value);
  });
}
```

### 4. Interface Lateral
Ao clicar no botão, uma interface lateral será aberta, contendo:
- Campo para visualização do prompt atual
- Botão para solicitar avaliação/otimização
- Área para exibir o prompt otimizado
- Botão para aplicar o prompt otimizado à área de texto
- Opção para copiar o prompt otimizado

O painel lateral será criado como um componente React isolado:

```jsx
function SidePanel({ prompt, onClose, onApply }) {
  const [optimizedPrompt, setOptimizedPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const evaluatePrompt = async () => {
    setIsLoading(true);
    try {
      const result = await api.evaluatePrompt(prompt);
      setOptimizedPrompt(result.evaluation.optimized_prompt);
    } catch (error) {
      console.error('Erro ao avaliar prompt:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="side-panel">
      <div className="side-panel-header">
        <h3>Avaliador de Prompts</h3>
        <button onClick={onClose}>X</button>
      </div>
      
      <div className="side-panel-content">
        <h4>Prompt Original</h4>
        <div className="prompt-display">{prompt}</div>
        
        <button 
          onClick={evaluatePrompt} 
          disabled={isLoading}
        >
          {isLoading ? 'Avaliando...' : 'Avaliar Prompt'}
        </button>
        
        {optimizedPrompt && (
          <>
            <h4>Prompt Otimizado</h4>
            <div className="prompt-display optimized">{optimizedPrompt}</div>
            
            <div className="button-group">
              <button onClick={() => onApply(optimizedPrompt)}>
                Aplicar
              </button>
              <button onClick={() => navigator.clipboard.writeText(optimizedPrompt)}>
                Copiar
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

### 5. Comunicação com Backend
- Autenticação: Implementaremos um sistema de autenticação (chave de API ou OAuth) para identificar usuários
- Endpoints: Utilizaremos os endpoints existentes para enviar prompts para avaliação
- Tratamento de Erros: Implementaremos tratamento robusto de erros de rede/API

```javascript
// Serviço API para comunicação com o backend
const api = {
  baseUrl: 'https://avaliadorprompt.com.br/api',
  
  async getCSRFToken() {
    const response = await fetch(`${this.baseUrl}/csrf-token`, {
      method: 'GET',
      credentials: 'include'
    });
    const data = await response.json();
    return data.csrf_token;
  },
  
  async evaluatePrompt(content) {
    const csrfToken = await this.getCSRFToken();
    
    const response = await fetch(`${this.baseUrl}/prompts/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      credentials: 'include',
      body: JSON.stringify({
        content,
        plan_type: 'free', // ou 'premium' dependendo do status do usuário
        target_llm: 'general' // pode ser personalizado
      })
    });
    
    if (!response.ok) {
      throw new Error(`Erro na API: ${response.status}`);
    }
    
    return await response.json();
  },
  
  async checkUserStatus(userId) {
    const response = await fetch(`${this.baseUrl}/free/status/${userId}`, {
      method: 'GET',
      credentials: 'include'
    });
    
    return await response.json();
  }
};
```

## Segurança

### Mitigação de Ataques
1. **Injeção de Código**: 
   - Sanitização rigorosa de todas as entradas de usuário
   - Uso de Content Security Policy (CSP) apropriado

2. **Proteção de Dados**:
   - Minimizar dados armazenados localmente
   - Criptografar dados sensíveis em trânsito e armazenamento
   - Implementar política de retenção de dados

3. **Autenticação e Autorização**:
   - Tokens de acesso com tempo de expiração curto
   - Renovação segura de tokens
   - Verificação de permissões para cada requisição

4. **Proteção contra XSS**:
   - Escape adequado de HTML em todas as saídas renderizadas
   - Uso de React para minimizar riscos de XSS através de JSX

5. **Comunicação Segura**:
   - Uso exclusivo de HTTPS para todas as comunicações
   - Implementação de CORS adequado no backend
   - Validação de origem das requisições

### Permissões da Extensão
Solicitaremos apenas as permissões mínimas necessárias:
- `tabs`: Para acessar a URL atual e detectar sites LLM
- `storage`: Para armazenar configurações do usuário
- `host permissions`: Apenas para os domínios específicos dos LLMs

## Construção e Distribuição

### Processo de Build
Utilizaremos um processo de build separado para Chrome e Safari:
- Webpack para empacotamento e otimização
- Babel para compatibilidade de navegadores
- PostCSS para processamento de CSS

#### Exemplo de configuração webpack.config.js:
```javascript
const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    background: './src/background/index.js',
    content: './src/content-scripts/index.js',
    popup: './src/popup/index.js'
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      }
    ]
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        { from: 'public', to: '.' }
      ]
    })
  ]
};
```

### Distribuição
- Chrome Web Store para versão Chrome/Edge/Opera
- Apple App Store para versão Safari

## Plano de Desenvolvimento

1. **Fase 1**: Configuração do ambiente e estrutura básica
   - Configuração do projeto React com Webpack
   - Configuração de manifest.json para Chrome e Safari
   - Implementação da detecção básica de sites LLM

2. **Fase 2**: Implementação da funcionalidade principal
   - Detecção de áreas de texto
   - Injeção do botão flutuante
   - Interface lateral básica

3. **Fase 3**: Integração com backend
   - Implementação de serviços de API
   - Autenticação e autorização
   - Tratamento e exibição de respostas

4. **Fase 4**: Refinamento e testes
   - Aprimoramento da UI/UX
   - Testes em diferentes navegadores e sites
   - Implementação de medidas de segurança

5. **Fase 5**: Distribuição
   - Preparação para publicação nas lojas
   - Documentação final
   - Estratégia de suporte pós-lançamento
