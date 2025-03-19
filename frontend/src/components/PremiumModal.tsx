import React, { useState } from 'react';
import './PremiumModal.css';

interface PremiumModalProps {
  onClose: () => void;
  refreshPage?: boolean;
}

interface UserFormData {
  email: string;
  full_name: string;
  password: string;
  password_confirm: string;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    full_name: '',
    password: '',
    password_confirm: ''
  });

  const handlePurchase = () => {
    // Se o usuário não estiver logado, mostrar formulário de cadastro
    setShowRegisterForm(true);
  };

  const handleContinueFree = () => {
    // Primeiro fecha o modal
    onClose();
    
    // Depois recarrega a página com um pequeno atraso
    if (refreshPage) {
      setTimeout(() => {
        window.location.reload();
      }, 100); // Pequeno atraso para garantir que o React atualize o estado
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPaymentError(null);
    setIsLoading(true);

    // Validações básicas
    if (formData.password !== formData.password_confirm) {
      setError('As senhas não coincidem');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('A senha deve ter pelo menos 8 caracteres');
      setIsLoading(false);
      return;
    }

    try {
      // Registrar o usuário
      const registerResponse = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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

      const userData = await registerResponse.json();
      console.log("Usuário registrado com sucesso:", userData);

      // Login automático após registro
      const loginResponse = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'username': formData.email,
          'password': formData.password,
        }),
      });

      if (!loginResponse.ok) {
        const data = await loginResponse.json();
        throw new Error(data.detail || 'Erro ao fazer login');
      }

      const loginData = await loginResponse.json();
      console.log("Login realizado com sucesso:", loginData);
      
      // Salvar token no localStorage
      localStorage.setItem('token', loginData.access_token);
      localStorage.setItem('user', JSON.stringify({
        id: loginData.user_id,
        email: loginData.email,
        fullName: loginData.full_name
      }));

      // Redirecionar para a página principal com o usuário já logado
      // Em vez de tentar criar o pagamento aqui
      onClose();
      if (refreshPage) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePaymentClick = async () => {
    setIsLoading(true);
    setPaymentError(null);
    
    // Verificar se o usuário está logado
    const token = localStorage.getItem('token');
    
    if (!token) {
      setPaymentError('Você precisa fazer login para continuar');
      setIsLoading(false);
      return;
    }
    
    try {
      // Verificar se o token é válido
      const userProfileResponse = await fetch('/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!userProfileResponse.ok) {
        // Se o token não for válido, limpar o localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setPaymentError('Sessão expirada. Por favor, faça login novamente.');
        setIsLoading(false);
        return;
      }
      
      // Criar pagamento para assinatura premium
      const paymentResponse = await fetch('/payments/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_type: 'premium',
          amount: 49.90
        }),
      });

      if (!paymentResponse.ok) {
        const data = await paymentResponse.json();
        throw new Error(data.detail || 'Erro ao criar pagamento');
      }

      const paymentData = await paymentResponse.json();
      
      // Verificar se há URL de checkout
      if (!paymentData.checkout_url) {
        throw new Error('URL de checkout não disponível');
      }
      
      // Redirecionar para URL de checkout
      window.location.href = paymentData.checkout_url;
    } catch (error) {
      console.error('Erro ao criar pagamento:', error);
      setPaymentError(error instanceof Error ? error.message : 'Erro ao processar pagamento');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={showRegisterForm ? undefined : onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {!showRegisterForm ? (
          <>
            <h2>Plano Premium</h2>
            <p>Aproveite todas as vantagens do plano premium:</p>
            <ul>
              <li>Avaliações ilimitadas</li>
              <li>Análise detalhada dos prompts</li>
              <li>Sugestões avançadas de otimização</li>
              <li>Suporte prioritário</li>
            </ul>
            <div className="price-section">
              <span className="price">R$49</span>
              <span className="period">/mês</span>
            </div>
            
            {paymentError && <div className="error-message">{paymentError}</div>}
            
            <div className="modal-buttons">
              {localStorage.getItem('token') ? (
                // Se o usuário já estiver logado, mostrar botão de pagamento direto
                <button className="premium-button" onClick={handlePaymentClick} disabled={isLoading}>
                  {isLoading ? 'Processando...' : 'Assinar Agora'}
                </button>
              ) : (
                // Se não estiver logado, mostrar botão para cadastro
                <button className="premium-button" onClick={handlePurchase}>
                  Criar Conta
                </button>
              )}
              <button className="cancel-button" onClick={handleContinueFree}>
                Continuar no Plano Gratuito
              </button>
            </div>
          </>
        ) : (
          <>
            <h2>Criar Conta</h2>
            <p>Preencha os dados abaixo para criar sua conta</p>
            
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
              
              <div className="form-group">
                <label htmlFor="password">Senha*</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  minLength={8}
                />
                <small>Mínimo de 8 caracteres</small>
              </div>
              
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
              
              <div className="modal-buttons">
                <button 
                  type="submit" 
                  className="premium-button"
                  disabled={isLoading}
                >
                  {isLoading ? 'Processando...' : 'Criar Conta'}
                </button>
                <button 
                  type="button" 
                  className="cancel-button"
                  onClick={() => setShowRegisterForm(false)}
                  disabled={isLoading}
                >
                  Voltar
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default PremiumModal; 