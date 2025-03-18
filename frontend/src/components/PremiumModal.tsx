import React from 'react';

interface PremiumModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const handlePurchase = () => {
    // Aqui implementaremos a integração com o sistema de pagamento
    window.open('https://buy.stripe.com/test_yourlink', '_blank');
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Plano Premium</h2>
        <p>Aproveite todas as vantagens do plano premium:</p>
        <ul>
          <li>Avaliações ilimitadas</li>
          <li>Análise detalhada dos prompts</li>
          <li>Sugestões avançadas de otimização</li>
          <li>Suporte prioritário</li>
        </ul>
        <div className="price-section">
          <span className="price">$10</span>
          <span className="period">/mês</span>
        </div>
        <div className="modal-buttons">
          <button className="premium-button" onClick={handlePurchase}>
            Assinar Agora
          </button>
          <button className="cancel-button" onClick={onClose}>
            Continuar no Plano Gratuito
          </button>
        </div>
      </div>
    </div>
  );
};

export default PremiumModal; 