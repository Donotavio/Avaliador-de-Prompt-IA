import React, { useState } from 'react';
import { CheckIcon } from '../components/Icons';

interface PremiumModalProps {
  onClose: () => void;
  refreshPage?: boolean;
}

const PremiumModal: React.FC<PremiumModalProps> = ({ onClose, refreshPage = false }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProceedToPayment = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
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
        setError('Não foi possível obter os dados do usuário.');
        return;
      }
      
      const userData = JSON.parse(userDataStr);
      
      // Dados mínimos necessários para o endpoint de pagamento
      const paymentData = {
        product_id: "premium_monthly", // ID do produto no backend
        payment_method: "pix", // Método de pagamento padrão
        customer: {
          name: userData.fullName,
          email: userData.email,
          tax_id: "00000000000", // CPF genérico
          phone: "11999998888", // Telefone genérico
          address: {
            street: "Rua do Cliente",
            number: "123",
            complement: "",
            neighborhood: "Centro",
            city: "São Paulo",
            state: "SP",
            country: "BR",
            address_zip_code: "01000000"
          }
        },
        completion_url: window.location.origin + "/payment-success"
      };

      console.log('Enviando dados para criar pagamento:', paymentData);

      // Fazer requisição para o servidor para iniciar o pagamento
      const response = await fetch('/api/payments/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(paymentData)
      });

      // Ler o corpo da resposta
      let responseData;
      try {
        responseData = await response.json();
      } catch (e) {
        console.error('Erro ao parsejar resposta JSON:', e);
        throw new Error('Erro ao processar resposta do servidor');
      }
      
      if (!response.ok) {
        // Extrair detalhes do erro
        let errorMessage = 'Erro ao processar pagamento';
        
        if (responseData && responseData.detail) {
          // Se o erro for um objeto, tentar extrair sua mensagem
          if (typeof responseData.detail === 'object') {
            errorMessage = JSON.stringify(responseData.detail);
          } else {
            errorMessage = responseData.detail;
          }
        }
        
        throw new Error(errorMessage);
      }
      
      // Se a resposta for bem-sucedida, use os dados recebidos
      if (responseData && responseData.checkout_url) {
        console.log('Redirecionando para:', responseData.checkout_url);
        // Redirecionar para o checkout do AbacatePay
        window.location.href = responseData.checkout_url;
      } else {
        throw new Error('URL de checkout não encontrada na resposta');
      }
    } catch (error) {
      console.error('Erro durante o processo de pagamento:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro ao processar o pagamento: ${errorMessage}`);
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