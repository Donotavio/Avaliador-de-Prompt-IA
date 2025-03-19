import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import PromptForm from './components/PromptForm';
import PremiumModal from './components/PremiumModal';
import PaymentSuccessPage from './components/PaymentSuccessPage';
import { InfoIcon, UserIcon, LogoutIcon, LoginIcon } from './components/Icons';

// Ícone de prompt para o logo
const PromptIcon = () => (
  <svg className="logo-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    {/* Balão de conversa */}
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    
    {/* Cérebro dentro do balão */}
    <path d="M14 8.5c0-.83-.67-1.5-1.5-1.5h-2c-.83 0-1.5.67-1.5 1.5M9 12.5c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5" />
    <path d="M9 8.5v4M14 8.5v4" />
    <path d="M11.5 7v7" />
    <path d="M9 10h5" />
  </svg>
);

// Ícone de coroa para usuários premium
const CrownIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
  </svg>
);

// Ícone para usuários free
const TagIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
    <line x1="7" y1="7" x2="7.01" y2="7"></line>
  </svg>
);

// Componente para exibir informações do usuário logado
const UserDisplay: React.FC<{ userName: string; isPremium: boolean; onLogout: () => void }> = ({ userName, isPremium, onLogout }) => {
  return (
    <div className="user-display">
      <span className="user-name">
        <UserIcon size={18} className="user-icon" /> {userName}
        {isPremium && (
          <span className="premium-badge" title="Usuário Premium">
            <CrownIcon size={16} />
            Premium
          </span>
        )}
        {!isPremium && (
          <span className="free-badge" title="Usuário Free">
            <TagIcon size={16} />
            Free
          </span>
        )}
      </span>
      <button className="logout-button" onClick={onLogout}>
        <LogoutIcon size={18} />
        <span>Sair</span>
      </button>
    </div>
  );
};

// Componente de botão de login
const LoginButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  return (
    <button className="login-button" onClick={onClick}>
      <LoginIcon size={18} />
      <span>Entrar</span>
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
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
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
        const registerResponse = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            full_name: formData.full_name,
            password: formData.password
          }),
        });

        if (!registerResponse.ok) {
          const errorData = await registerResponse.json();
          console.error('Erro de registro:', errorData);
          
          // Tenta extrair mensagens de erro específicas
          if (errorData.detail) {
            // Se o erro for um objeto, converte para string
            if (typeof errorData.detail === 'object') {
              if (errorData.detail.msg) {
                throw new Error(errorData.detail.msg);
              } else {
                throw new Error('Dados inválidos. Verifique as informações e tente novamente.');
              }
            } else {
              // Se for formato de campo específico, como 'Email inválido'
              if (errorData.detail.includes('email')) {
                throw new Error('Email inválido. Informe um endereço de email no formato correto (ex: nome@dominio.com)');
              } else {
                throw new Error(errorData.detail);
              }
            }
          } else {
            throw new Error('Erro ao registrar usuário. Verifique os dados e tente novamente.');
          }
        }

        // Login automático após registro
        const loginResponse = await fetch('/api/auth/login', {
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
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-container" onClick={e => e.stopPropagation()}>
        <button className="auth-close-button" onClick={onClose}>×</button>
        
        <div className="auth-modal-header">
          <h2 className="auth-modal-title">{isLogin ? 'Entrar' : 'Criar Conta'}</h2>
        </div>
        
        <div className="auth-modal-content">
          {error && <div className="auth-error-message">{error}</div>}
          
          <form onSubmit={handleSubmit}>
            <div className="auth-form-group">
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
              <div className="auth-form-group">
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

            <div className="auth-form-group">
              <label htmlFor="password">Senha*</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
              />
              {!isLogin && (
                <div className="auth-form-password-hint">
                  <InfoIcon />
                  <span>Mínimo de 8 caracteres</span>
                </div>
              )}
            </div>

            {!isLogin && (
              <div className="auth-form-group">
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

            <button type="submit" className="auth-submit-button" disabled={isLoading}>
              {isLoading ? (
                <>
                  <div className="spinner"></div>
                  <span>Processando...</span>
                </>
              ) : (
                isLogin ? 'Entrar' : 'Cadastrar'
              )}
            </button>
          </form>
        </div>
        
        <div className="auth-modal-footer">
          <div className="auth-alternate-action">
            {isLogin ? 'Não tem uma conta?' : 'Já tem uma conta?'}
            <button type="button" onClick={toggleMode}>
              {isLogin ? 'Cadastre-se' : 'Entrar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente principal da aplicação
const App: React.FC = () => {
  const [userId, setUserId] = useState<string>("anon");
  const [userName, setUserName] = useState<string>("");
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [isPremiumModalOpen, setIsPremiumModalOpen] = useState<boolean>(false);
  const [isPremium, setIsPremium] = useState<boolean>(false);

  // Verifica se há um usuário logado no localStorage
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userObj = JSON.parse(storedUser);
        setUserId(userObj.id);
        setUserName(userObj.fullName || userObj.email);
        setIsLoggedIn(true);
        setIsAdmin(userObj.id === 'admin');
        
        // Se o objeto do usuário já tiver a flag isPremium
        if (userObj.hasOwnProperty('isPremium')) {
          setIsPremium(userObj.isPremium);
        }
        
        // Verifica o status premium do usuário
        checkPremiumStatus();
      } catch (e) {
        console.error('Erro ao parsear dados do usuário:', e);
        // Em caso de erro, limpa o localStorage para evitar problemas
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);
  
  // Verificar o status premium quando o aplicativo é montado e a cada 30 segundos
  useEffect(() => {
    // Verificação inicial
    checkPremiumStatus();
    
    // Configurar verificação periódica
    const intervalId = setInterval(() => {
      if (isLoggedIn) {
        checkPremiumStatus();
      }
    }, 30000); // 30 segundos
    
    // Limpar o intervalo quando o componente for desmontado
    return () => clearInterval(intervalId);
  }, [isLoggedIn]);
  
  // Função para verificar o status premium do usuário
  const checkPremiumStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch('/api/payments/status', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const newPremiumStatus = data.is_active || false;
        
        // Só atualiza o estado se o status mudou
        if (newPremiumStatus !== isPremium) {
          setIsPremium(newPremiumStatus);
          
          // Atualiza também no localStorage para persistência
          const storedUser = localStorage.getItem('user');
          if (storedUser) {
            try {
              const userObj = JSON.parse(storedUser);
              userObj.isPremium = newPremiumStatus;
              localStorage.setItem('user', JSON.stringify(userObj));
            } catch (e) {
              console.error('Erro ao atualizar status premium no localStorage:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Erro ao verificar status premium:', error);
    }
  };
  
  // Função para efetuar logout (limpeza de dados)
  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUserId("anon");
    setUserName("");
    setIsLoggedIn(false);
    setIsAdmin(false);
    setIsPremium(false);
    // Opcional: recarregar a página para garantir um estado limpo
    window.location.reload();
  };

  // Função chamada após login bem-sucedido
  const handleLoginSuccess = () => {
    // Recarregar a página para atualizar o estado
    window.location.reload();
  };

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="container">
            <div className="app-header-content">
              <div className="logo">
                <a href="/">
                  <PromptIcon />
                  Avaliador de Prompt IA
                  <span className="beta-badge">Beta</span>
                </a>
              </div>
              <div className="user-actions">
                {isLoggedIn ? (
                  <UserDisplay 
                    userName={userName} 
                    isPremium={isPremium}
                    onLogout={handleLogout} 
                  />
                ) : (
                  <LoginButton onClick={() => setShowLoginModal(true)} />
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="app-main">
          <div className="container">
            <Routes>
              <Route path="/" element={
                <PromptForm 
                  userId={userId} 
                  isAdmin={isAdmin}
                  isPremium={isPremium}
                  openPremiumModal={() => setIsPremiumModalOpen(true)} 
                />
              } />
              <Route path="/payment-success" element={
                <PaymentSuccessPage userId={userId} />
              } />
              {/* Rota fallback para páginas não encontradas */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
        </main>

        <footer className="app-footer">
          <div className="container">
            <div className="app-footer-content">
              <div className="app-footer-links">
                <a href="/privacy" className="app-footer-link">Privacidade</a>
                <a href="/terms" className="app-footer-link">Termos</a>
                <a href="/contact" className="app-footer-link">Contato</a>
              </div>
              <div className="app-footer-copyright">
                &copy; {new Date().getFullYear()} Avaliador de Prompts. Todos os direitos reservados.
              </div>
            </div>
          </div>
        </footer>

        {showLoginModal && (
          <LoginModal 
            onClose={() => setShowLoginModal(false)} 
            onLoginSuccess={handleLoginSuccess} 
          />
        )}

        {isPremiumModalOpen && (
          <PremiumModal 
            onClose={() => setIsPremiumModalOpen(false)} 
            refreshPage={true}
          />
        )}
      </div>
    </Router>
  );
};

export default App; 