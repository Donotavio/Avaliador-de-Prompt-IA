import React, { useState, useEffect, useCallback } from 'react';
import './PaymentResult.css';

interface PaymentResultProps {
  checkoutUrl: string;
  paymentMethod: string;
  onClose: () => void;
}

interface PaymentDetails {
  status: string;
  qrCodeUrl?: string;
  qrCodeText?: string;
  boletoUrl?: string;
  boletoCode?: string;
  message?: string;
  error?: string;
}

const PaymentResult: React.FC<PaymentResultProps> = ({ checkoutUrl, paymentMethod, onClose }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null);
  const [countdown, setCountdown] = useState(600); // 10 minutos em segundos
  
  // Função para extrair o ID do pagamento da URL
  const extractPaymentIdFromUrl = useCallback((url: string): string => {
    // Implementação simplificada, você precisará adaptar para o formato real da sua URL
    const urlParts = url.split('/');
    return urlParts[urlParts.length - 1];
  }, []);
  
  // Funções memorizadas para evitar recriações em cada renderização
  const checkPaymentStatus = useCallback(async () => {
    try {
      const paymentId = extractPaymentIdFromUrl(checkoutUrl);
      
      const response = await fetch(`/api/payments/status/${paymentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Erro ao verificar status do pagamento');
      }
      
      const data = await response.json();
      
      if (data.status === 'paid') {
        setPaymentDetails(prev => prev ? { ...prev, status: 'paid', message: 'Pagamento confirmado! Redirecionando...' } : null);
        
        // Redirecionar após pagamento confirmado
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 3000);
      }
    } catch (error) {
      console.error('Erro ao verificar status do pagamento:', error);
    }
  }, [checkoutUrl, extractPaymentIdFromUrl]);
  
  const fetchPaymentDetails = useCallback(async () => {
    setIsLoading(true);
    try {
      const paymentId = extractPaymentIdFromUrl(checkoutUrl);
      
      const response = await fetch(`/api/payments/details/${paymentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Erro ao obter detalhes do pagamento');
      }
      
      const data = await response.json();
      
      setPaymentDetails({
        status: data.status || 'pending',
        qrCodeUrl: data.qr_code_url,
        qrCodeText: data.qr_code_text,
        boletoUrl: data.boleto_url,
        boletoCode: data.boleto_code,
        message: data.message,
        error: data.error
      });
      
      // Se houver erro na obtenção dos detalhes mas temos a URL de checkout,
      // podemos mostrar um botão para redirecionar para ela
      if (data.error && data.checkout_url) {
        setError(`Não foi possível obter os detalhes de pagamento. 
                 Você pode continuar para a página de pagamento do AbacatePay.`);
      }
    } catch (error) {
      console.error('Erro ao buscar detalhes do pagamento:', error);
      setError('Não foi possível obter os detalhes do pagamento. Você será redirecionado para o checkout.');
      
      // Adicionar um atraso antes do redirecionamento
      setTimeout(() => {
        window.location.href = checkoutUrl;
      }, 3000);
    } finally {
      setIsLoading(false);
    }
  }, [checkoutUrl, extractPaymentIdFromUrl]);
  
  // Se for PIX, periodicamente verifica o status do pagamento
  useEffect(() => {
    if (paymentMethod === 'PIX' && paymentDetails?.status === 'pending') {
      const intervalId = setInterval(() => {
        checkPaymentStatus();
      }, 15000); // A cada 15 segundos
      
      return () => clearInterval(intervalId);
    }
  }, [paymentMethod, paymentDetails, checkPaymentStatus]);
  
  // Contador regressivo
  useEffect(() => {
    if (countdown > 0 && (paymentMethod === 'PIX' || paymentMethod === 'BOLETO') && paymentDetails?.status === 'pending') {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [countdown, paymentMethod, paymentDetails]);
  
  // Busca os detalhes do pagamento ao carregar o componente
  useEffect(() => {
    fetchPaymentDetails();
  }, [fetchPaymentDetails]);
  
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const renderPixPayment = () => {
    if (!paymentDetails) return null;
    
    return (
      <div className="pix-payment">
        <h3>Pagamento via PIX</h3>
        
        {paymentDetails.status === 'paid' ? (
          <div className="payment-success">
            <div className="success-icon">✓</div>
            <p>Pagamento confirmado com sucesso!</p>
            <p>Redirecionando para o dashboard...</p>
          </div>
        ) : (
          <>
            <div className="qr-code-container">
              {paymentDetails.qrCodeUrl ? (
                <img src={paymentDetails.qrCodeUrl} alt="QR Code para pagamento PIX" />
              ) : (
                <div className="qr-code-placeholder">QR Code não disponível</div>
              )}
            </div>
            
            {paymentDetails.qrCodeText && (
              <div className="pix-code">
                <h4>Código PIX</h4>
                <div className="pix-code-text">
                  <p>{paymentDetails.qrCodeText}</p>
                  <button
                    className="copy-button"
                    onClick={() => {
                      navigator.clipboard.writeText(paymentDetails.qrCodeText || '');
                      alert('Código PIX copiado!');
                    }}
                  >
                    Copiar
                  </button>
                </div>
              </div>
            )}
            
            <div className="payment-instructions">
              <p>Escaneie o QR Code ou copie o código PIX com seu aplicativo bancário.</p>
              <p>O pagamento será confirmado automaticamente em instantes após o envio.</p>
              <p className="payment-expiry">
                Tempo restante: <span className="countdown">{formatTime(countdown)}</span>
              </p>
            </div>
          </>
        )}
      </div>
    );
  };
  
  const renderBoletoPayment = () => {
    if (!paymentDetails) return null;
    
    return (
      <div className="boleto-payment">
        <h3>Pagamento via Boleto</h3>
        
        {paymentDetails.status === 'paid' ? (
          <div className="payment-success">
            <div className="success-icon">✓</div>
            <p>Pagamento confirmado com sucesso!</p>
            <p>Redirecionando para o dashboard...</p>
          </div>
        ) : (
          <>
            {paymentDetails.boletoCode && (
              <div className="boleto-code">
                <h4>Código de Barras</h4>
                <div className="boleto-code-text">
                  <p>{paymentDetails.boletoCode}</p>
                  <button
                    className="copy-button"
                    onClick={() => {
                      navigator.clipboard.writeText(paymentDetails.boletoCode || '');
                      alert('Código de barras copiado!');
                    }}
                  >
                    Copiar
                  </button>
                </div>
              </div>
            )}
            
            {paymentDetails.boletoUrl && (
              <div className="boleto-actions">
                <a 
                  href={paymentDetails.boletoUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="download-button"
                >
                  Baixar Boleto
                </a>
              </div>
            )}
            
            <div className="payment-instructions">
              <p>O boleto pode ser pago em qualquer banco ou casa lotérica.</p>
              <p>O prazo para compensação é de até 3 dias úteis após o pagamento.</p>
              <p className="payment-expiry">
                Boleto válido até: <span className="countdown">3 dias úteis</span>
              </p>
            </div>
          </>
        )}
      </div>
    );
  };
  
  const renderCreditCardRedirect = () => {
    return (
      <div className="credit-card-redirect">
        <h3>Pagamento via Cartão de Crédito</h3>
        <p>Você será redirecionado para a página segura do nosso processador de pagamentos.</p>
        <p>Não se preocupe, seus dados estão protegidos.</p>
        
        <div className="redirect-actions">
          <a 
            href={checkoutUrl} 
            className="redirect-button"
          >
            Ir para Página de Pagamento
          </a>
          <button
            className="cancel-button"
            onClick={onClose}
          >
            Cancelar
          </button>
        </div>
      </div>
    );
  };
  
  if (isLoading) {
    return (
      <div className="payment-result loading">
        <div className="loader"></div>
        <p>Carregando informações de pagamento...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="payment-result error">
        <h3>Erro</h3>
        <p>{error}</p>
        <div className="error-actions">
          <button onClick={() => window.location.href = checkoutUrl} className="redirect-button">
            Ir para Página de Pagamento
          </button>
          <button onClick={onClose} className="cancel-button">
            Voltar
          </button>
        </div>
      </div>
    );
  }
  
  if (paymentDetails?.error) {
    return (
      <div className="payment-result warning">
        <h3>Informações de Pagamento</h3>
        <p>Ocorreu um problema ao obter os detalhes do pagamento, mas você pode continuar para a página de checkout.</p>
        <div className="error-actions">
          <button onClick={() => window.location.href = checkoutUrl} className="redirect-button">
            Ir para Página de Pagamento
          </button>
          <button onClick={onClose} className="cancel-button">
            Voltar
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="payment-result">
      {paymentMethod === 'PIX' && renderPixPayment()}
      {paymentMethod === 'BOLETO' && renderBoletoPayment()}
      {paymentMethod === 'CREDIT_CARD' && renderCreditCardRedirect()}
      
      <div className="payment-actions">
        {paymentMethod !== 'CREDIT_CARD' && paymentDetails?.status !== 'paid' && (
          <button
            className="cancel-button"
            onClick={onClose}
          >
            Voltar
          </button>
        )}
      </div>
    </div>
  );
};

export default PaymentResult; 