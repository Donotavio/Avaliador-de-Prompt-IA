import React, { useState } from 'react';
import PaymentForm from './PaymentForm';
import { CheckIcon, CloseIcon, InfoIcon } from './Icons';

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

  // Função chamada quando o usuário clica em "Começar Agora"
  const handlePurchase = () => {
    // Verifica se o usuário já está logado
    const isUserLoggedIn = localStorage.getItem('token') !== null;
    
    if (isUserLoggedIn) {
      // Se já está logado, vai direto para o pagamento
      setCurrentStep(ModalStep.PAYMENT);
    } else {
      // Se não está logado, vai para o formulário de registro
      setCurrentStep(ModalStep.REGISTER);
    }
  };

  // Função chamada quando o usuário clica em "Continuar no Plano Gratuito"
  const handleContinueFree = () => {
    closeModal();
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
      const registerResponse = await fetch('/api/auth/register', {
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

      // Login automático
      const loginResponse = await fetch('/api/auth/login', {
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

  // Função para lidar com o sucesso do pagamento
  const handlePaymentSuccess = (checkoutUrl: string) => {
    window.location.href = checkoutUrl;
  };

  // Função para lidar com erros no pagamento
  const handlePaymentError = (error: string) => {
    setPaymentError(error);
  };

  const closeModal = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    onClose();
  };

  // Renderiza o passo atual do modal
  const renderStepContent = () => {
    switch (currentStep) {
      case ModalStep.INTRO:
        return (
          <div className="premium-content">
            <h3>Aproveite todas as vantagens do plano premium:</h3>
            <ul className="premium-features">
              <li><CheckIcon /> Avaliações ilimitadas</li>
              <li><CheckIcon /> Análise detalhada dos prompts</li>
              <li><CheckIcon /> Sugestões avançadas de otimização</li>
              <li><CheckIcon /> Suporte prioritário</li>
            </ul>
            <div className="premium-price">
              <span className="price-value">R$49</span>
              <span className="price-period">/mês</span>
            </div>
            <div className="premium-actions">
              <button 
                className="btn btn-primary btn-lg w-full"
                onClick={() => handlePurchase()}
                disabled={isLoading}
              >
                {isLoading ? 'Processando...' : 'Começar Agora'}
              </button>
              <button 
                className="btn btn-outline btn-sm mt-4 w-full"
                onClick={() => handleContinueFree()}
              >
                Continuar no Plano Gratuito
              </button>
            </div>
          </div>
        );
        
      case ModalStep.REGISTER:
        return (
          <div className="auth-modal-container">
            <button className="auth-close-button" onClick={closeModal}>
              <CloseIcon size={20} />
            </button>
            
            <div className="auth-modal-header">
              <h2 className="auth-modal-title">Criar Conta</h2>
              <p>Preencha os dados abaixo para criar sua conta</p>
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
                  <div className="auth-form-password-hint">
                    <InfoIcon size={14} />
                    <span>Mínimo de 8 caracteres</span>
                  </div>
                </div>
                
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
                
                <button type="submit" className="auth-submit-button" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <div className="spinner"></div>
                      <span>Processando...</span>
                    </>
                  ) : 'Continuar'}
                </button>
              </form>
              
              <div className="auth-alternate-action" style={{marginTop: '1rem', textAlign: 'center'}}>
                Já tem uma conta?
                <button type="button" onClick={() => setCurrentStep(ModalStep.PAYMENT)}>
                  Entrar
                </button>
              </div>
            </div>
          </div>
        );
        
      case ModalStep.PAYMENT:
        return (
          <PaymentForm 
            onClose={onClose} 
            onSuccess={handlePaymentSuccess} 
            onError={handlePaymentError} 
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <div 
      className="modal-backdrop" 
      onClick={closeModal}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.5)'
      }}
    >
      <div 
        className="modal premium-modal" 
        onClick={e => e.stopPropagation()}
        style={{ 
          position: 'relative',
          zIndex: 1001,
          background: 'white',
          borderRadius: '8px',
          maxWidth: '500px',
          width: '100%',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}
      >
        <div className="modal-header">
          <h2 className="modal-title">
            {currentStep === ModalStep.INTRO && 'Plano Premium'}
            {currentStep === ModalStep.REGISTER && 'Criar Conta'}
            {currentStep === ModalStep.PAYMENT && 'Pagamento'}
          </h2>
          <button className="modal-close" onClick={closeModal}>
            <CloseIcon />
          </button>
        </div>
        <div className="modal-body">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
};

export default PremiumModal; 