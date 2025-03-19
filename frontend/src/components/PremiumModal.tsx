import React, { useState } from 'react';
import { CheckIcon } from '../components/Icons';

interface PremiumModalProps {
  onClose: () => void;
  refreshPage?: boolean;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleProceedToPayment = async () => {
    setIsLoading(true);
    try {
      // Verificar se o usuário está logado
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Você precisa estar logado para assinar o plano premium.');
        onClose();
        return;
      }

      // Fazer requisição para o servidor para iniciar o pagamento
      const response = await fetch('/api/payments/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao processar pagamento');
      }

      const data = await response.json();
      
      // Redirecionar para o checkout do AbacatePay
      window.location.href = data.checkout_url;
    } catch (error) {
      console.error('Erro:', error);
      alert(`Erro ao processar o pagamento: ${error instanceof Error ? error.message : 'Erro desconhecido'}`);
      setIsLoading(false);
    }
  };

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