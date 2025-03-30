# Avaliador de Prompts - Extensão para Navegadores

Esta extensão permite avaliar e otimizar prompts em sites de LLMs como ChatGPT, Claude, Gemini e outros.

## Funcionalidades

- Detecção automática de áreas de texto em sites de LLMs
- Botão flutuante para acesso rápido ao avaliador
- Interface lateral para exibição de resultados
- Prompt otimizado com sugestões de melhoria
- Verificação de status de usuário (gratuito/premium)
- Contagem de avaliações restantes

## Suporte a Plataformas

A extensão suporta as seguintes plataformas:

- ChatGPT (chat.openai.com)
- Claude (claude.ai)
- Gemini (gemini.google.com)
- Perplexity (perplexity.ai)
- Copilot (copilot.microsoft.com)
- Hugging Face Chat (huggingface.co/chat)
- Poe (poe.com)
- Grok (grok.com)
- DeepSeek (chat.deepseek.com)

## Requisitos de Desenvolvimento

- Node.js 18+ 
- npm ou yarn

## Instalação para Desenvolvimento

### Chrome/Edge

1. Clone este repositório
2. Instale as dependências:
```
cd extensions/chrome
npm install
```
3. Compile a extensão:
```
npm run build
```
4. Abra Chrome/Edge e navegue para `chrome://extensions/`
5. Ative o "Modo de desenvolvedor"
6. Clique em "Carregar sem compactação" e selecione a pasta `dist` criada no passo 3

### Safari

1. É necessário ter Xcode instalado
2. Instale as dependências:
```
cd extensions/safari
npm install
```
3. Compile a extensão:
```
npm run build
```
4. Abra o projeto no Xcode e siga as instruções para instalação em desenvolvimento

## Uso

1. Acesse qualquer site de LLM suportado
2. A extensão detectará automaticamente as áreas de texto
3. Um botão flutuante aparecerá no canto inferior direito da área de texto
4. Clique no botão para abrir o painel lateral de avaliação
5. Clique em "Avaliar Prompt" para analisar seu prompt
6. Veja as sugestões e o prompt otimizado
7. Clique em "Aplicar" para substituir seu prompt pelo otimizado

## Limites da Versão Gratuita

- 3 avaliações gratuitas por dia
- Funcionalidades básicas de avaliação
- Para remover limitações, faça upgrade para o plano premium

## Estrutura do Projeto

```
extensions/
├── chrome/               # Versão para Chrome/Edge/Opera
│   ├── public/           # Arquivos estáticos
│   ├── src/              # Código fonte
│   │   ├── components/   # Componentes React
│   │   ├── services/     # Serviços de API
│   │   ├── utils/        # Utilitários
│   │   ├── background/   # Script de background
│   │   ├── content-scripts/ # Content scripts
│   │   └── popup/        # Interface do popup
│   ├── package.json      # Dependências
│   └── webpack.config.js # Configuração de build
└── safari/               # Versão para Safari (estrutura similar)
```

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request 