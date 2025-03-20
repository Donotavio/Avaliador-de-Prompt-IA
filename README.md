# Avaliador de Prompts IA

Sistema especialista para avaliação e otimização de prompts para Inteligência Artificial.

## Descrição

Este projeto oferece uma interface web para auxiliar usuários na avaliação, otimização e criação de prompts eficazes para interação com modelos de IA como ChatGPT, GPT-4 e DALL·E.

## Funcionalidades

- Avaliação de prompts existentes
- Sugestões de otimização
- Análise de clareza e eficácia
- Verificação de contexto e especificidade
- Recomendações de melhores práticas

## Tecnologias

### Backend
- Python
- FastAPI
- Pydantic
- pytest

### Frontend
- React
- Material-UI
- ESLint
- Prettier

## Instalação

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Executando o Projeto

### Backend

```bash
cd backend
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm start
```

## Estrutura do Projeto

```bash
avaliador_prompt_ia/
├── backend/
│   ├── api/
│   ├── core/
│   ├── schemas/
│   ├── tests/
│   └── utils/
└── frontend/
    ├── public/
    └── src/
```

## Contribuição

1. Faça o fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

MIT 

## Segurança da Aplicação

### Configuração CORS Segura

A aplicação implementa medidas de segurança CORS (Cross-Origin Resource Sharing) para proteger contra ataques de origem cruzada:

- **Origens Permitidas**: Apenas domínios específicos podem acessar a API
- **Métodos Permitidos**: Apenas GET, POST, PUT e DELETE são permitidos
- **Cabeçalhos Permitidos**: Apenas cabeçalhos essenciais são permitidos

### Executando com Verificações de Segurança

Para iniciar o servidor com verificações automáticas de segurança:

```bash
cd backend
./run_server.py
```

Este script garante que:
1. O servidor inicie corretamente
2. As configurações CORS estejam aplicadas conforme esperado
3. Os cabeçalhos de segurança HTTP estejam configurados

### Verificação Manual de Segurança

Para executar verificações de segurança manualmente:

```bash
cd backend
python -m tools.security_checker
```

### Implantação Segura na Hostinger

Para implantação em produção na Hostinger, siga as instruções detalhadas no arquivo `backend/SECURITY.md`. 