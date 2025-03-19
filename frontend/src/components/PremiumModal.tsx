import React from 'react';

interface PremiumModalProps {
  onClose: () => void;
  refreshPage?: boolean;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const handlePurchase = () => {
    // Aqui implementaremos a integração com o sistema de pagamento
    window.open('https://buy.stripe.com/test_yourlink', '_blank');
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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
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
        <div className="modal-buttons">
          <button className="premium-button" onClick={handlePurchase}>
            Assinar Agora
          </button>
          <button className="cancel-button" onClick={handleContinueFree}>
            Continuar no Plano Gratuito
          </button>
        </div>
      </div>
    </div>
  );
};

export default PremiumModal; 