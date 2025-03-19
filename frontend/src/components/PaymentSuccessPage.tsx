import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './PaymentResult.css'; // Reusando o CSS do PaymentResult

interface PaymentSuccessPageProps {
  userId?: string;
}

const PaymentSuccessPage: React.FC<PaymentSuccessPageProps> = ({ userId }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [message, setMessage] = useState<string>("Verificando seu pagamento...");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verifyPayment = async () => {
      try {
        // Tenta extrair o ID do pagamento da URL
        const urlParams = new URLSearchParams(location.search);
        const billId = urlParams.get('bill_id');
        
        if (!billId) {
          setError("ID do pagamento não encontrado na URL");
          setIsLoading(false);
          return;
        }
        
        // Obtém o token do usuário
        const token = localStorage.getItem('token');
        if (!token) {
          setError("Usuário não autenticado");
          setIsLoading(false);
          return;
        }
        
        // Chama o endpoint para verificar e ativar o pagamento
        const response = await fetch(`/api/payments/verify-payment/${billId}`, {
          method: 'POST',
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
        
        if (result.success) {
          setMessage("Pagamento confirmado e plano premium ativado com sucesso!");
          
          // Redirecionar para a página principal após 3 segundos
          setTimeout(() => {
            navigate('/');
          }, 3000);
        } else {
          setMessage(`Seu pagamento foi recebido, mas ainda está sendo processado. Status: ${result.status}`);
          setError("O pagamento pode levar alguns minutos para ser confirmado. Por favor, tente novamente mais tarde.");
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