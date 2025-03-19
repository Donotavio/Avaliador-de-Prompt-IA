import React, { useState, useEffect } from 'react';
import PromptForm from './components/PromptForm';
import PremiumModal from './components/PremiumModal';
import './App.css';

// Componente para exibir informações do usuário logado
const UserDisplay: React.FC<{ userName: string; onLogout: () => void }> = ({ userName, onLogout }) => {
  return (
    <div className="user-display">
      <span className="user-name">Olá, {userName}</span>
      <button className="logout-button" onClick={onLogout}>
        Sair
      </button>
    </div>
  );
};

// Componente de botão de login
const LoginButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  return (
    <button className="login-button" onClick={onClick}>
      Entrar
    </button>
  );
};

// Modal de login
const LoginModal: React.FC<{ onClose: () => void; onLoginSuccess: () => void }> = ({ onClose, onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    password_confirm: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const toggleMode = () => setIsLogin(!isLogin);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        // Login
        const response = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            'username': formData.email,
            'password': formData.password,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Erro ao fazer login');
        }

        const userData = await response.json();
        
        // Salvar dados do usuário no localStorage
        localStorage.setItem('token', userData.access_token);
        localStorage.setItem('user', JSON.stringify({
          id: userData.user_id,
          email: userData.email,
          fullName: userData.full_name
        }));

        // Fechar modal e notificar sucesso
        onClose();
        onLoginSuccess();
      } else {
        // Registro
        // Validações
        if (formData.password !== formData.password_confirm) {
          throw new Error('As senhas não coincidem');
        }

        if (formData.password.length < 8) {
          throw new Error('A senha deve ter pelo menos 8 caracteres');
        }

        // Registrar
        const registerResponse = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            full_name: formData.full_name,
            password: formData.password
          }),
        });

        if (!registerResponse.ok) {
          const data = await registerResponse.json();
          throw new Error(data.detail || 'Erro ao registrar usuário');
        }

        // Login automático após registro
        const loginResponse = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            'username': formData.email,
            'password': formData.password,
          }),
        });

        if (!loginResponse.ok) {
          const data = await loginResponse.json();
          throw new Error(data.detail || 'Erro ao fazer login automático');
        }

        const loginData = await loginResponse.json();
        
        // Salvar dados
        localStorage.setItem('token', loginData.access_token);
        localStorage.setItem('user', JSON.stringify({
          id: loginData.user_id,
          email: loginData.email,
          fullName: loginData.full_name
        }));

        // Fechar modal e notificar sucesso
        onClose();
        onLoginSuccess();
      }
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-modal-overlay" onClick={onClose}>
      <div className="login-modal-content" onClick={e => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        <h2>{isLogin ? 'Entrar' : 'Criar Conta'}</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email*</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="full_name">Nome Completo*</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Senha*</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="password_confirm">Confirmar Senha*</label>
              <input
                type="password"
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                required
              />
            </div>
          )}

          <div className="form-actions">
            <button type="submit" className="login-submit-button" disabled={isLoading}>
              {isLoading ? 'Processando...' : isLogin ? 'Entrar' : 'Cadastrar'}
            </button>
          </div>
        </form>

        <div className="toggle-mode">
          <p>
            {isLogin ? 'Não tem uma conta?' : 'Já tem uma conta?'}
            <button type="button" onClick={toggleMode} className="toggle-button">
              {isLogin ? 'Cadastre-se' : 'Entrar'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  // Estado para gerenciar o ID do usuário
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [isPremiumModalOpen, setIsPremiumModalOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  
  // Verifica se há um usuário logado no localStorage
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userObj = JSON.parse(storedUser);
        setUserId(userObj.id);
        setUserName(userObj.fullName || userObj.email);
      } catch (e) {
        console.error('Erro ao parsear dados do usuário:', e);
        // Em caso de erro, limpa o localStorage para evitar problemas
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);
  
  // Função para efetuar logout (limpeza de dados)
  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUserId(null);
    setUserName('');
    // Opcional: recarregar a página para garantir um estado limpo
    window.location.reload();
  };

  // Função para abrir o modal de login
  const handleLoginClick = () => {
    setIsLoginModalOpen(true);
  };

  // Função chamada após login bem-sucedido
  const handleLoginSuccess = () => {
    // Recarregar a página para atualizar o estado
    window.location.reload();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avaliador de Prompts IA</h1>
        <p>Otimize seus prompts para resultados melhores com qualquer LLM</p>
        <div className="header-actions">
          <button 
            className="buy-premium-button" 
            onClick={() => setIsPremiumModalOpen(true)}
          >
            Comprar Premium
          </button>
          
          {userId ? (
            <UserDisplay userName={userName} onLogout={handleLogout} />
          ) : (
            <LoginButton onClick={handleLoginClick} />
          )}
        </div>
      </header>
      <main className="app-main">
        <PromptForm userId={userId || "anon"} />
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Avaliador de Prompts IA. Todos os direitos reservados.</p>
      </footer>

      {isPremiumModalOpen && (
        <PremiumModal 
          onClose={() => setIsPremiumModalOpen(false)}
          refreshPage={true}
        />
      )}

      {isLoginModalOpen && (
        <LoginModal 
          onClose={() => setIsLoginModalOpen(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}
    </div>
  );
};

export default App; 