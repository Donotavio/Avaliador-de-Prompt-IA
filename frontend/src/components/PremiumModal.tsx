import React, { useState } from 'react';
import { CheckIcon } from '../components/Icons';
import PaymentForm from './PaymentForm';

interface PremiumModalProps {
  onClose: () => void;
  refreshPage?: boolean;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  const handleProceedToPayment = async () => {
    // Verificar se o usuário está logado
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Você precisa estar logado para assinar o plano premium.');
      setTimeout(() => onClose(), 3000);
      return;
    }

    // Obter dados do usuário do localStorage
    const userDataStr = localStorage.getItem('user');
    if (!userDataStr) {
      setError('Você precisa estar logado para assinar o plano premium.');
      setTimeout(() => onClose(), 3000);
      return;
    }
    
    // Mostrar o formulário de pagamento
    setShowPaymentForm(true);
  };

  const handlePaymentSuccess = (checkoutUrl: string) => {
    // Redirecionamos para o checkout do AbacatePay
    window.location.href = checkoutUrl;
  };

  const handlePaymentError = (errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
  };

  if (showPaymentForm) {
    return (
      <div className="auth-modal-overlay" onClick={onClose}>
        <div onClick={e => e.stopPropagation()} className="payment-form-container">
          <PaymentForm 
            onClose={() => setShowPaymentForm(false)} 
            onSuccess={handlePaymentSuccess}
            onError={handlePaymentError}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="modal premium-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Plano Premium</h2>
          <button className="auth-close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="premium-content">
          <p className="premium-intro">Aproveite todas as vantagens do plano premium:</p>
          
          <ul className="premium-features">
            <li>
              <CheckIcon size={24} />
              <span>Avaliações ilimitadas</span>
              <span className="premium-benefit-tag">Ilimitado</span>
            </li>
            <li>
              <CheckIcon size={24} />
              <span>Análise detalhada dos prompts</span>
            </li>
            <li>
              <CheckIcon size={24} />
              <span>Sugestões avançadas de otimização</span>
            </li>
            <li>
              <CheckIcon size={24} />
              <span>Suporte prioritário</span>
            </li>
          </ul>
          
          <div className="premium-price">
            <div className="price-value">49</div>
            <span className="price-period">/mês</span>
          </div>
          
          {error && (
            <div className="payment-error">
              {error}
            </div>
          )}
          
          <div className="premium-actions">
            <button 
              className="btn-primary" 
              onClick={handleProceedToPayment}
              disabled={isLoading}
            >
              {isLoading ? 'Processando...' : 'Começar Agora'}
            </button>
            
            <button className="btn-secondary" onClick={onClose}>
              Continuar no Plano Gratuito
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PremiumModal; 