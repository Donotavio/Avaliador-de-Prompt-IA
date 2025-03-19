import React, { useState } from 'react';
import PaymentForm from './PaymentForm';
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

enum ModalStep {
  INTRO = 'intro',
  REGISTER = 'register',
  PAYMENT = 'payment'
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const [currentStep, setCurrentStep] = useState<ModalStep>(ModalStep.INTRO);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    full_name: '',
    password: '',
    password_confirm: ''
  });

  // Função para verificar se o usuário está logado
  const isLoggedIn = (): boolean => {
    return !!localStorage.getItem('token');
  };

  // Avança para o passo de pagamento ou registro dependendo se o usuário está logado
  const handlePurchase = () => {
    if (isLoggedIn()) {
      // Se o usuário já estiver logado, vai direto para pagamento
      setCurrentStep(ModalStep.PAYMENT);
    } else {
      // Se não estiver logado, mostra formulário de cadastro
      setCurrentStep(ModalStep.REGISTER);
    }
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

      // Após registro e login bem-sucedidos, avança para o passo de pagamento
      setCurrentStep(ModalStep.PAYMENT);
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar solicitação');
    } finally {
      setIsLoading(false);
    }
  };

  // Função chamada quando o pagamento é processado com sucesso
  const handlePaymentSuccess = (checkoutUrl: string) => {
    // Redireciona para a URL de pagamento
    window.location.href = checkoutUrl;
  };

  // Renderiza o passo atual do modal
  const renderStep = () => {
    switch (currentStep) {
      case ModalStep.INTRO:
        return (
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
              <button className="premium-button" onClick={handlePurchase}>
                {isLoggedIn() ? 'Assinar Agora' : 'Criar Conta'}
              </button>
              <button className="cancel-button" onClick={handleContinueFree}>
                Continuar no Plano Gratuito
              </button>
            </div>
          </>
        );
        
      case ModalStep.REGISTER:
        return (
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
                <button type="submit" className="premium-button" disabled={isLoading}>
                  {isLoading ? 'Processando...' : 'Continuar'}
                </button>
                <button type="button" className="back-button" onClick={() => setCurrentStep(ModalStep.INTRO)}>
                  Voltar
                </button>
              </div>
            </form>
          </>
        );
        
      case ModalStep.PAYMENT:
        return (
          <PaymentForm 
            onClose={() => setCurrentStep(ModalStep.INTRO)} 
            onSuccess={handlePaymentSuccess} 
          />
        );
    }
  };

  return (
    <div className="modal-overlay" onClick={currentStep === ModalStep.INTRO ? onClose : undefined}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {renderStep()}
      </div>
    </div>
  );
};

export default PremiumModal; 