import React, { useState, useEffect } from 'react';
import PaymentResult from './PaymentResult';
import './PaymentForm.css';

interface PaymentFormProps {
  onClose: () => void;
  onSuccess: (checkoutUrl: string) => void;
}

interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  external_id: string;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onClose, onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [formData, setFormData] = useState({
    taxId: '',
    cellphone: '',
    address: '',
    addressNumber: '',
    complement: '',
    neighborhood: '',
    city: '',
    state: '',
    postalCode: '',
    paymentMethod: 'PIX' // Valor padrão
  });
  
  // Estado para controlar a exibição do resultado do pagamento
  const [showPaymentResult, setShowPaymentResult] = useState(false);
  const [paymentUrl, setPaymentUrl] = useState('');
  
  const paymentMethods = [
    { id: 'PIX', name: 'PIX' },
    { id: 'CREDIT_CARD', name: 'Cartão de Crédito' },
    { id: 'BOLETO', name: 'Boleto Bancário' }
  ];

  // Buscar produtos ativos quando o componente carregar
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch('/api/products?active_only=true', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('Erro ao buscar produtos');
        }

        const data = await response.json();
        setProducts(data);

        // Define o primeiro produto como selecionado por padrão
        if (data.length > 0) {
          setSelectedProductId(data[0].id);
        }
      } catch (error) {
        console.error('Erro ao buscar produtos:', error);
        setError('Não foi possível carregar os planos disponíveis');
      }
    };

    fetchProducts();
  }, []);

  // Buscar dados do usuário quando o componente carregar
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          return;
        }
        
        const response = await fetch('/api/users/me/payment-info', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Erro ao buscar dados do usuário');
        }
        
        const userData = await response.json();
        
        // Preenche o formulário com os dados salvos
        setFormData(prevData => ({
          ...prevData,
          taxId: userData.taxId || '',
          cellphone: userData.phone || '',
          address: userData.address || '',
          addressNumber: userData.addressNumber || '',
          complement: userData.complement || '',
          neighborhood: userData.neighborhood || '',
          city: userData.city || '',
          state: userData.state || '',
          postalCode: userData.postalCode || '',
          paymentMethod: userData.preferredPaymentMethod || 'PIX'
        }));
        
        console.log('Dados do usuário carregados com sucesso');
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        // Não exibimos erro para o usuário, apenas log para debug
      }
    };
    
    fetchUserData();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name === 'taxId') {
      setFormData(prev => ({
        ...prev,
        [name]: formatCpfCnpj(value)
      }));
    } else if (name === 'cellphone') {
      setFormData(prev => ({
        ...prev,
        [name]: formatPhone(value)
      }));
    } else if (name === 'postalCode') {
      setFormData(prev => ({
        ...prev,
        [name]: formatCep(value)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Formatador de CPF/CNPJ
  const formatCpfCnpj = (value: string) => {
    // Remove caracteres não numéricos
    const numbers = value.replace(/\D/g, '');
    
    // Formata como CPF (11 dígitos)
    if (numbers.length <= 11) {
      return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, (_, g1, g2, g3, g4) => {
        if (numbers.length < 10) return numbers;
        if (numbers.length === 10) return `${g1}.${g2}.${g3}`;
        return `${g1}.${g2}.${g3}-${g4}`;
      });
    } 
    // Formata como CNPJ (14 dígitos)
    else {
      return numbers.slice(0, 14).replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, (_, g1, g2, g3, g4, g5) => {
        if (numbers.length < 13) return numbers;
        if (numbers.length === 13) return `${g1}.${g2}.${g3}/${g4}`;
        return `${g1}.${g2}.${g3}/${g4}-${g5}`;
      });
    }
  };
  
  // Formatador de telefone
  const formatPhone = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    return numbers.replace(/(\d{2})(\d{5})(\d{4})/, (_, g1, g2, g3) => {
      if (numbers.length < 10) return numbers;
      return `(${g1}) ${g2}-${g3}`;
    }).slice(0, 15);
  };
  
  // Formatador de CEP
  const formatCep = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    return numbers.replace(/(\d{5})(\d{3})/, (_, g1, g2) => {
      if (numbers.length < 8) return numbers;
      return `${g1}-${g2}`;
    }).slice(0, 9);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    // Validação básica
    if (!formData.taxId || formData.taxId.length < 11) {
      setError('CPF/CNPJ inválido');
      setIsLoading(false);
      return;
    }

    if (!formData.cellphone || formData.cellphone.length < 10) {
      setError('Telefone celular inválido');
      setIsLoading(false);
      return;
    }
    
    if (!formData.postalCode || formData.postalCode.length < 8) {
      setError('CEP é obrigatório');
      setIsLoading(false);
      return;
    }

    try {
      // Obtém o token do localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Usuário não autenticado');
        setIsLoading(false);
        return;
      }

      // Prepara os dados para enviar
      const paymentData = {
        product_id: selectedProductId,
        payment_method: formData.paymentMethod,
        user_data: {
          taxId: formData.taxId.replace(/\D/g, ''), // Remove caracteres não numéricos
          cellphone: formData.cellphone.replace(/\D/g, ''), // Remove caracteres não numéricos
          address: formData.address,
          addressNumber: formData.addressNumber,
          complement: formData.complement,
          neighborhood: formData.neighborhood,
          city: formData.city,
          state: formData.state,
          postalCode: formData.postalCode.replace(/\D/g, '')
        }
      };

      // Envia solicitação para criar pagamento
      const response = await fetch('/api/payments/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(paymentData)
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Erro ao processar pagamento');
      }

      console.log('Pagamento criado:', data);
      
      // Verifica se recebemos a URL de checkout
      if (data.checkout_url) {
        // Armazena a URL para uso posterior
        setPaymentUrl(data.checkout_url);
        
        // Para cartão de crédito, redirecionamos direto para o checkout
        if (formData.paymentMethod === 'CREDIT_CARD') {
          onSuccess(data.checkout_url);
        } else {
          // Para outros métodos, mostramos a tela de detalhes do pagamento
          setShowPaymentResult(true);
        }
      } else {
        throw new Error('URL de pagamento não encontrada na resposta');
      }
    } catch (error) {
      console.error('Erro:', error);
      setError(error instanceof Error ? error.message : 'Erro ao processar pagamento');
    } finally {
      setIsLoading(false);
    }
  };

  // Se estiver mostrando o resultado do pagamento, renderizar o PaymentResult
  if (showPaymentResult) {
    return (
      <PaymentResult 
        checkoutUrl={paymentUrl} 
        paymentMethod={formData.paymentMethod} 
        onClose={onClose} 
      />
    );
  }

  return (
    <div className="payment-form-container">
      <h2>Concluir Assinatura</h2>
      <p>Complete seu cadastro para finalizar a assinatura</p>
      
      {error && <div className="payment-error">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <h3>Selecione seu plano</h3>
          <div className="product-selection">
            {products.length === 0 ? (
              <p>Carregando planos disponíveis...</p>
            ) : (
              products.map(product => (
                <div 
                  key={product.id} 
                  className={`product-card ${selectedProductId === product.id ? 'selected' : ''}`}
                  onClick={() => setSelectedProductId(product.id)}
                >
                  <h4>{product.name}</h4>
                  <p>{product.description}</p>
                  <div className="product-price">
                    <span>R$ {product.price.toFixed(2)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="form-section">
          <h3>Método de Pagamento</h3>
          <div className="payment-methods">
            {paymentMethods.map(method => (
              <div
                key={method.id}
                className={`payment-method-card ${formData.paymentMethod === method.id ? 'selected' : ''}`}
                onClick={() => setFormData(prev => ({ ...prev, paymentMethod: method.id }))}
              >
                {method.name}
              </div>
            ))}
          </div>
          
          <div className="payment-method-info">
            {formData.paymentMethod === 'PIX' && (
              <div className="pix-info">
                <p>Após preencher seus dados, você receberá um QR Code para pagamento via PIX.</p>
                <p>O pagamento será processado instantaneamente após a confirmação.</p>
              </div>
            )}
            
            {formData.paymentMethod === 'CREDIT_CARD' && (
              <div className="credit-card-info">
                <p>Você será redirecionado para uma página segura para inserir os dados do seu cartão.</p>
                <p>Aceitamos as principais bandeiras: Visa, Mastercard, American Express, Elo.</p>
              </div>
            )}
            
            {formData.paymentMethod === 'BOLETO' && (
              <div className="boleto-info">
                <p>O boleto será gerado após o preenchimento dos seus dados.</p>
                <p>O prazo para compensação é de até 3 dias úteis após o pagamento.</p>
              </div>
            )}
          </div>
        </div>
        
        <div className="form-section">
          <h3>Dados para Faturamento</h3>
          <div className="form-group">
            <label htmlFor="taxId">CPF/CNPJ*</label>
            <input
              type="text"
              id="taxId"
              name="taxId"
              value={formData.taxId}
              onChange={handleChange}
              required
              placeholder="000.000.000-00"
              maxLength={18}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="cellphone">Celular*</label>
            <input
              type="text"
              id="cellphone"
              name="cellphone"
              value={formData.cellphone}
              onChange={handleChange}
              required
              placeholder="(00) 00000-0000"
              maxLength={15}
            />
          </div>
        </div>
        
        <div className="form-section">
          <h3>Endereço (obrigatório)</h3>
          <div className="form-group">
            <label htmlFor="address">Rua*</label>
            <input
              type="text"
              id="address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              required
              placeholder="Nome da rua"
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="addressNumber">Número*</label>
              <input
                type="text"
                id="addressNumber"
                name="addressNumber"
                value={formData.addressNumber}
                onChange={handleChange}
                required
                placeholder="Número"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="complement">Complemento</label>
              <input
                type="text"
                id="complement"
                name="complement"
                value={formData.complement}
                onChange={handleChange}
                placeholder="Apto, Bloco, etc."
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="neighborhood">Bairro*</label>
            <input
              type="text"
              id="neighborhood"
              name="neighborhood"
              value={formData.neighborhood}
              onChange={handleChange}
              required
              placeholder="Bairro"
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="city">Cidade*</label>
              <input
                type="text"
                id="city"
                name="city"
                value={formData.city}
                onChange={handleChange}
                required
                placeholder="Cidade"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="state">Estado*</label>
              <input
                type="text"
                id="state"
                name="state"
                value={formData.state}
                onChange={handleChange}
                required
                placeholder="UF"
                maxLength={2}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="postalCode">CEP*</label>
              <input
                type="text"
                id="postalCode"
                name="postalCode"
                value={formData.postalCode}
                onChange={handleChange}
                required
                placeholder="00000-000"
                maxLength={9}
              />
            </div>
          </div>
        </div>
        
        <div className="payment-note">
          <p>Ao clicar em "Finalizar Pagamento", você será redirecionado para a plataforma segura do AbacatePay para completar o pagamento de acordo com o método escolhido.</p>
        </div>
        
        <div className="form-buttons">
          <button
            type="submit"
            className="payment-button"
            disabled={isLoading || !selectedProductId}
          >
            {isLoading ? 'Processando...' : 'Finalizar Pagamento'}
          </button>
          
          <button
            type="button"
            className="cancel-button"
            onClick={onClose}
            disabled={isLoading}
          >
            Voltar
          </button>
        </div>
      </form>
    </div>
  );
};

export default PaymentForm; 