import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

interface PaymentSuccessPageProps {
  userId?: string;
}

const PaymentSuccessPage: React.FC<PaymentSuccessPageProps> = ({ userId }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [message, setMessage] = useState<string>("Verificando seu pagamento...");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Função para atualizar o status premium no localStorage
  const updateLocalPremiumStatus = () => {
    // Atualiza o status premium no localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userObj = JSON.parse(storedUser);
        userObj.isPremium = true;
        localStorage.setItem('user', JSON.stringify(userObj));
      } catch (e) {
        console.error('Erro ao atualizar status premium no localStorage:', e);
      }
    }
  };

  useEffect(() => {
    const verifyPayment = async () => {
      try {
        // Obtém o token do usuário
        const token = localStorage.getItem('token');
        if (!token) {
          setError("Usuário não autenticado");
          setIsLoading(false);
          return;
        }
        
        // Chama o endpoint para verificar o status da assinatura atual
        const response = await fetch(`/api/payments/status`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Erro ao verificar pagamento');
        }
        
        const result = await response.json();
        
        if (result.subscription && result.subscription.abacate_payment_id) {
          // Como o AbacatePay só redireciona para essa página quando o pagamento é bem-sucedido,
          // marcamos automaticamente como sucesso
          setMessage("Pagamento confirmado e plano premium ativado com sucesso!");
          
          // Opcionalmente, informa o backend que o pagamento foi bem-sucedido
          try {
            // Tenta ativar o pagamento no backend
            const activationResponse = await fetch(`/api/payments/verify-payment/${result.subscription.abacate_payment_id}?success=true`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });

            if (activationResponse.ok) {
              // Atualiza o status premium no localStorage
              updateLocalPremiumStatus();
            }
          } catch (activationError) {
            // Apenas loga o erro, mas não mostra para o usuário
            console.error('Erro ao ativar pagamento:', activationError);
          }
          
          // Redirecionar para a página principal após 3 segundos
          setTimeout(() => {
            navigate('/');
          }, 3000);
        } else {
          setError("Não foi possível encontrar informações do pagamento");
        }
      } catch (error) {
        console.error('Erro ao verificar pagamento:', error);
        setError(error instanceof Error ? error.message : 'Erro desconhecido ao verificar pagamento');
      } finally {
        setIsLoading(false);
      }
    };
    
    verifyPayment();
  }, [location, navigate, userId]);
  
  const handleReturnClick = () => {
    navigate('/');
  };
  
  return (
    <div className="payment-result">
      <div className="payment-success">
        <div className="payment-logo">
          <img src="/abacate-logo.png" alt="AbacatePay" />
        </div>
        
        <h2>Pagamento confirmado!</h2>
        
        {isLoading ? (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Verificando seu pagamento...</p>
          </div>
        ) : (
          <>
            <p>{message}</p>
            {error && <p className="error-message">{error}</p>}
          </>
        )}
        
        <button 
          className="return-button"
          onClick={handleReturnClick}
        >
          Retornar para página principal
        </button>
      </div>
    </div>
  );
};

export default PaymentSuccessPage; 