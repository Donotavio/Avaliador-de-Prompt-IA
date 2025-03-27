import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import PromptForm from './components/PromptForm';
import PremiumModal from './components/PremiumModal';
import PaymentSuccessPage from './components/PaymentSuccessPage';
import { UserIcon, LogoutIcon, LoginIcon } from './components/Icons';
import PasswordField from './components/PasswordField';
import { TOKEN_EXPIRED_EVENT } from './services/auth';
import { API_BASE_URL } from './services/api';
// Importando as páginas de rodapé do arquivo de índice
import { ContactPage, PrivacyPage, TermsPage } from './pages';

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
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [userId, setUserId] = useState('');
  const [verificationToken, setVerificationToken] = useState('');
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [isResendingToken, setIsResendingToken] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const toggleMode = () => setIsLogin(!isLogin);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleVerificationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Limita a entrada a 6 caracteres numéricos
    const { value } = e.target;
    const numericValue = value.replace(/[^0-9]/g, '').slice(0, 6);
    setVerificationToken(numericValue);
  };

  const handleForgotPassword = () => {
    setShowForgotPassword(true);
  };

  const handleBackToLogin = () => {
    setShowForgotPassword(false);
    setShowVerification(false);
  };

  const handleSubmitForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          frontend_url: `${window.location.origin}/reset-password`
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Erro ao processar solicitação');
      }

      // Exibir mensagem de sucesso
      alert('Se o e-mail estiver cadastrado, você receberá instruções para recuperar sua senha.');
      setShowForgotPassword(false);
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerificationError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: verificationToken,
          user_id: userId
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao verificar e-mail');
      }

      // Se a verificação for bem-sucedida, faça login automático
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        
        // Busca os dados do usuário
        const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
          }
        });
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          localStorage.setItem('user', JSON.stringify({
            id: userData.id,
            email: userData.email,
            fullName: userData.full_name,
            isVerified: userData.is_email_verified
          }));
        }
        
        onClose();
        onLoginSuccess();
      } else {
        // Se não receber tokens, volte para login
        setShowVerification(false);
      }
    } catch (error) {
      console.error('Erro:', error);
      setVerificationError(error instanceof Error ? error.message : 'Erro ao verificar e-mail');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (resendCooldown > 0) return;
    
    setIsResendingToken(true);
    setVerificationError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao reenviar código');
      }

      // Inicia o contador de cooldown (60 segundos)
      setResendCooldown(60);
      const countdownInterval = setInterval(() => {
        setResendCooldown(prev => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      console.error('Erro:', error);
      setVerificationError(error instanceof Error ? error.message : 'Erro ao reenviar código');
    } finally {
      setIsResendingToken(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        // Login
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
          fullName: userData.full_name,
          isVerified: userData.is_email_verified
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
        const registerResponse = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
            full_name: formData.full_name
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

        const userData = await registerResponse.json();
        
        // Configurar para exibir o modal de verificação
        setUserId(userData.id);
        setShowVerification(true);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
      setIsLoading(false);
    }
  };

  if (showForgotPassword) {
    return (
      <div className="auth-modal-overlay" onClick={onClose}>
        <div className="auth-modal-container" onClick={e => e.stopPropagation()}>
          <button className="auth-close-button" onClick={onClose}>×</button>
          <div className="auth-modal-header">
            <h2 className="auth-modal-title">Recuperar Senha</h2>
          </div>
          <div className="auth-modal-content">
            <form onSubmit={handleSubmitForgotPassword}>
              <div className="auth-form-group">
                <label htmlFor="email">E-mail</label>
                <input 
                  type="email" 
                  id="email" 
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              {error && <div className="auth-error-message">{error}</div>}
              
              <div className="auth-form-actions recovery-actions">
                <button
                  type="button"
                  className="auth-secondary-button"
                  onClick={handleBackToLogin}
                >
                  Voltar
                </button>
                <button
                  type="submit"
                  className="auth-primary-button"
                  disabled={isLoading}
                >
                  {isLoading ? 'Enviando...' : 'Enviar link de recuperação'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  if (showVerification) {
    return (
      <div className="auth-modal-overlay" onClick={onClose}>
        <div className="auth-modal-container" onClick={e => e.stopPropagation()}>
          <button className="auth-close-button" onClick={onClose}>×</button>
          <div className="auth-modal-header">
            <h2 className="auth-modal-title">Verificação de E-mail</h2>
          </div>
          <div className="auth-modal-content">
            <div className="message-container">
              <p>Um código de verificação foi enviado para o seu e-mail.</p>
              <p>Por favor, insira o código para verificar sua conta:</p>
            </div>
            
            <form onSubmit={handleVerifyEmail}>
              <div className="auth-form-group verification-input">
                <label htmlFor="verificationToken">Código de verificação</label>
                <input 
                  type="text" 
                  id="verificationToken" 
                  name="verificationToken"
                  value={verificationToken}
                  onChange={handleVerificationChange}
                  maxLength={6}
                  placeholder="Insira o código de 6 dígitos"
                  required
                />
              </div>

              {verificationError && <div className="auth-error-message">{verificationError}</div>}
              
              <div className="auth-form-actions">
                <button
                  type="submit"
                  className="auth-primary-button"
                  disabled={isLoading || verificationToken.length !== 6}
                >
                  {isLoading ? 'Verificando...' : 'Verificar'}
                </button>
              </div>
              
              <div className="auth-toggle-mode">
                <button 
                  type="button" 
                  className="auth-text-button" 
                  onClick={handleResendVerification}
                  disabled={isResendingToken || resendCooldown > 0}
                >
                  {resendCooldown > 0 
                    ? `Reenviar código (${resendCooldown}s)` 
                    : isResendingToken 
                      ? 'Reenviando...' 
                      : 'Reenviar código'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

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
              <PasswordField 
                id="password" 
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>

            {!isLogin && (
              <div className="auth-form-group">
                <label htmlFor="password_confirm">Confirmar Senha*</label>
                <PasswordField 
                  id="password_confirm" 
                  name="password_confirm"
                  value={formData.password_confirm}
                  onChange={handleChange}
                  required
                />
              </div>
            )}

            {isLogin && (
              <div className="auth-forgot-password">
                <button 
                  type="button" 
                  className="auth-text-button"
                  onClick={handleForgotPassword}
                >
                  Esqueceu a senha?
                </button>
              </div>
            )}

            <div className="auth-form-actions">
              <button
                type="submit"
                className="auth-submit-button"
                disabled={isLoading}
              >
                {isLoading
                  ? 'Processando...'
                  : isLogin
                    ? 'Entrar'
                    : 'Criar Conta'
                }
              </button>
            </div>
          </form>
          
          <div className="auth-toggle-mode">
            <span>{isLogin ? 'Ainda não tem conta?' : 'Já tem uma conta?'}</span>
            <button
              type="button"
              className="auth-text-button"
              onClick={toggleMode}
            >
              {isLogin ? 'Criar Conta' : 'Fazer Login'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente para redefinição de senha
const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [formData, setFormData] = useState({
    token: token || '',
    new_password: '',
    confirm_password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    // Validação básica
    if (formData.new_password !== formData.confirm_password) {
      setError('As senhas não coincidem');
      setIsLoading(false);
      return;
    }

    if (formData.new_password.length < 8) {
      setError('A senha deve ter pelo menos 8 caracteres');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: formData.token,
          new_password: formData.new_password
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Erro ao redefinir senha');
      }

      setSuccess(true);
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="reset-password-container error-container">
        <h2>Link Inválido</h2>
        <p>O link de recuperação de senha é inválido ou expirou.</p>
        <a href="/" className="button-link">Voltar para o início</a>
      </div>
    );
  }

  if (success) {
    return (
      <div className="reset-password-container success-container">
        <h2>Senha Redefinida</h2>
        <p>Sua senha foi redefinida com sucesso!</p>
        <a href="/" className="button-link">Voltar para o início</a>
      </div>
    );
  }

  return (
    <div className="reset-password-container">
      <h2>Redefinir Senha</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <PasswordField
            id="new_password"
            name="new_password"
            value={formData.new_password}
            onChange={handleChange}
            required
            minLength={8}
            label="Nova Senha"
            showHint={true}
          />
        </div>
        
        <div className="form-group">
          <PasswordField
            id="confirm_password"
            name="confirm_password"
            value={formData.confirm_password}
            onChange={handleChange}
            required
            label="Confirmar Senha"
          />
        </div>
        
        <button
          type="submit"
          className="submit-button"
          disabled={isLoading}
        >
          {isLoading ? 'Processando...' : 'Redefinir Senha'}
        </button>
      </form>
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
  const [userChanged, setUserChanged] = useState<boolean>(false);
  const [showTokenExpiredModal, setShowTokenExpiredModal] = useState<boolean>(false);

  // Função para verificar o status premium do usuário (mover para antes dos useEffect)
  const checkPremiumStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${API_BASE_URL}/payments/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
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
  }, [isPremium]); // Adicionar isPremium como dependência

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
  }, [checkPremiumStatus]);
  
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
  }, [isLoggedIn, checkPremiumStatus]);
  
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
    // Atualizar o estado do usuário sem recarregar a página
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userObj = JSON.parse(storedUser);
        setUserId(userObj.id);
        setUserName(userObj.fullName || userObj.email);
        setIsLoggedIn(true);
        setIsAdmin(userObj.id === 'admin');
        setUserChanged(true);
      } catch (e) {
        console.error('Erro ao parsear dados do usuário:', e);
      }
    }
  };

  // Verificar status premium quando componente montar
  useEffect(() => {
    if (isLoggedIn) {
      checkPremiumStatus();
    }
  }, [isLoggedIn, checkPremiumStatus]);

  // Verificar status premium novamente quando usuário logar
  useEffect(() => {
    if (userChanged) {
      checkPremiumStatus();
      setUserChanged(false);
    }
  }, [userChanged, checkPremiumStatus]);

  // Adicionar listener para evento de token expirado
  useEffect(() => {
    const handleTokenExpired = () => {
      // Limpa dados do usuário
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      setUserId("anon");
      setUserName("");
      setIsLoggedIn(false);
      setIsAdmin(false);
      setIsPremium(false);
      
      // Mostra modal de login com mensagem de sessão expirada
      setShowTokenExpiredModal(true);
    };

    // Adiciona o listener para o evento
    window.addEventListener(TOKEN_EXPIRED_EVENT, handleTokenExpired);

    // Remove o listener quando o componente for desmontado
    return () => {
      window.removeEventListener(TOKEN_EXPIRED_EVENT, handleTokenExpired);
    };
  }, []);

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
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/terms" element={<TermsPage />} />
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

        {/* Modal de sessão expirada */}
        {showTokenExpiredModal && (
          <div className="auth-modal-overlay">
            <div className="auth-modal-container">
              <div className="auth-modal-header">
                <h2 className="auth-modal-title">Sessão Expirada</h2>
              </div>
              <div className="auth-modal-content">
                <p>Sua sessão expirou. Por favor, faça login novamente para continuar.</p>
                <div className="auth-form-actions">
                  <button
                    className="auth-primary-button"
                    onClick={() => {
                      setShowTokenExpiredModal(false);
                      setShowLoginModal(true);
                    }}
                  >
                    Fazer Login
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de login */}
        {showLoginModal && (
          <LoginModal
            onClose={() => setShowLoginModal(false)}
            onLoginSuccess={handleLoginSuccess}
          />
        )}

        {/* Modal de upgrade para premium */}
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