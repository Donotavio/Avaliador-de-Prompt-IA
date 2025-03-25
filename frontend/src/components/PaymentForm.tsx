import React, { useState, useEffect } from 'react';
import { AlertIcon } from './Icons';
import { API_BASE_URL } from '../services/api';

interface PaymentFormProps {
  onClose: () => void;
  onSuccess: (checkoutUrl: string) => void;
  onError?: (error: string) => void;
}

// Interface para produto na aplicação
interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  external_id: string;
}

// Interface para produto recebido da API
interface ApiProduct {
  id: string;
  name: string;
  description: string;
  price?: number;
  price_in_cents?: number;
  external_id: string;
  active?: boolean;
  recurrence_period_days?: number;
  created_at?: string;
  updated_at?: string;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onClose, onSuccess, onError }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUserData, setIsLoadingUserData] = useState(false);
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

  // Buscar produtos ativos quando o componente carregar
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/products?active_only=true`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Erro ao buscar produtos');
        }

        const data = await response.json() as ApiProduct[];
        
        // Garante que o preço esteja no formato correto (em centavos)
        const productsWithFormattedPrice: Product[] = data.map((product: ApiProduct) => ({
          id: product.id,
          name: product.name,
          description: product.description,
          price: product.price_in_cents || product.price || 0,
          external_id: product.external_id
        }));
        
        setProducts(productsWithFormattedPrice);

        // Define o primeiro produto como selecionado por padrão
        if (productsWithFormattedPrice.length > 0) {
          setSelectedProductId(productsWithFormattedPrice[0].id);
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
        
        setIsLoadingUserData(true);
        const response = await fetch(`${API_BASE_URL}/users/me/payment-info`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error('Erro ao buscar dados do usuário');
        }
        
        const userData = await response.json();
        
        // Preenche o formulário com os dados salvos
        setFormData(prevData => ({
          ...prevData,
          taxId: userData.taxId || userData.tax_id || '',
          cellphone: userData.phone || userData.cellphone || '',
          address: userData.address || '',
          addressNumber: userData.addressNumber || userData.address_number || '',
          complement: userData.complement || '',
          neighborhood: userData.neighborhood || '',
          city: userData.city || '',
          state: userData.state || '',
          postalCode: userData.postalCode || userData.postal_code || '',
          paymentMethod: userData.preferredPaymentMethod || userData.preferred_payment_method || 'PIX'
        }));
        
        console.log('Dados do usuário carregados com sucesso');
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        // Exibimos um erro mais amigável para o usuário
        setError('Não foi possível carregar seus dados salvos. Você pode preenchê-los manualmente.');
        setTimeout(() => setError(null), 5000); // Remove a mensagem após 5 segundos
      } finally {
        setIsLoadingUserData(false);
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

  // Validação de CPF simples
  const isValidCPF = (cpf: string) => {
    // Remove caracteres não numéricos
    const cleanCPF = cpf.replace(/\D/g, '');
    
    // Verifica se tem 11 dígitos
    if (cleanCPF.length !== 11) {
      return false;
    }
    
    // Verifica se todos os dígitos são iguais (CPF inválido, mas com formato correto)
    if (/^(\d)\1{10}$/.test(cleanCPF)) {
      return false;
    }
    
    // Para uma validação básica, apenas verificamos o comprimento
    // Em uma aplicação real, você deve implementar o algoritmo completo de validação
    return true;
  };

  // Atualizar o tratamento de erros para usar a função onError quando disponível
  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    if (onError) {
      onError(errorMessage);
    }
  };

  // Função auxiliar para criar pagamento diretamente no AbacatePay
  const createDirectPayment = async (token: string, paymentData: any) => {
    // Mapear os dados do formulário para o formato esperado pelo AbacatePay
    const abacatePayData = {
      frequency: 'ONE_TIME',
      methods: [paymentData.payment_method],
      products: [{
        externalId: 'premium-plan',
        name: 'Assinatura Premium',
        description: 'Acesso ilimitado à avaliação de prompts por 30 dias',
        quantity: 1,
        price: 4990
      }],
      customer: {
        name: paymentData.user_data.name,
        email: paymentData.user_data.email,
        taxId: paymentData.user_data.tax_id,
        cellphone: paymentData.user_data.cellphone
      },
      // URLs simples sem parâmetros dinâmicos
      returnUrl: window.location.origin,
      completionUrl: window.location.origin,
      webhookUrl: window.location.origin + '/api/webhook',
      devMode: true
    };
    
    // Enviar para o endpoint de proxy que não vai modificar as URLs
    const response = await fetch(`${API_BASE_URL}/payments/proxy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(abacatePayData)
    });
    
    return response;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Validação básica dos campos
    if (!selectedProductId) {
      handleError('Selecione um plano');
      setIsLoading(false);
      return;
    }
    
    if (!formData.paymentMethod) {
      handleError('Selecione um método de pagamento');
      setIsLoading(false);
      return;
    }
    
    if (!formData.taxId || !isValidCPF(formData.taxId)) {
      handleError('CPF inválido');
      setIsLoading(false);
      return;
    }
    
    if (!formData.cellphone || formData.cellphone.length < 10) {
      handleError('Telefone celular é obrigatório');
      setIsLoading(false);
      return;
    }
    
    if (!formData.address) {
      handleError('Endereço é obrigatório');
      setIsLoading(false);
      return;
    }
    
    if (!formData.addressNumber) {
      handleError('Número é obrigatório');
      setIsLoading(false);
      return;
    }
    
    if (!formData.neighborhood) {
      handleError('Bairro é obrigatório');
      setIsLoading(false);
      return;
    }
    
    if (!formData.city) {
      handleError('Cidade é obrigatória');
      setIsLoading(false);
      return;
    }
    
    if (!formData.state) {
      handleError('Estado é obrigatório');
      setIsLoading(false);
      return;
    }
    
    if (!formData.postalCode || formData.postalCode.length < 8) {
      handleError('CEP é obrigatório');
      setIsLoading(false);
      return;
    }

    try {
      // Obtém o token do localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        handleError('Usuário não autenticado');
        setIsLoading(false);
        return;
      }

      // Prepara os dados para enviar
      const paymentData = {
        product_id: selectedProductId,
        payment_method: 'PIX',  // Sempre utiliza PIX independente do valor no formData
        // Sinalizador para o backend não modificar URLs
        use_raw_urls: true,
        // URLs simples sem parâmetros - isso deve ser enviado para API diretamente
        return_url: window.location.origin,
        completion_url: window.location.origin,
        webhook_url: window.location.origin + '/api/webhook',
        // Modo de desenvolvimento para testes
        dev_mode: true,
        user_data: {
          name: localStorage.getItem('userName') || 'Cliente',
          email: localStorage.getItem('userEmail') || '',
          tax_id: formData.taxId.replace(/\D/g, ''),
          cellphone: formData.cellphone.replace(/\D/g, ''),
          // Campos de endereço no formato que o backend espera
          address_street: formData.address,
          address_number: formData.addressNumber,
          address_complement: formData.complement || '',
          address_neighborhood: formData.neighborhood,
          address_city: formData.city,
          address_state: formData.state,
          address_country: 'BR',
          address_zip_code: formData.postalCode.replace(/\D/g, '')
        }
      };

      console.log('Enviando dados de pagamento:', paymentData);

      // Tenta primeiro o caminho padrão do backend
      let response;
      try {
        response = await fetch(`${API_BASE_URL}/payments/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(paymentData)
        });
        
        const data = await response.json();
        
        // Se obteve sucesso, prossegue normalmente
        if (response.ok) {
          console.log('Pagamento criado com sucesso:', data);
          if (data.checkout_url) {
            onSuccess(data.checkout_url);
            return;
          }
        } 
        // Se falhou devido a erro de URL
        else if (data.detail && 
          (data.detail.includes('completionUrl must match format') || 
           data.detail.includes('must match format "uri"') || 
           data.detail.includes('FST_ERR_VALIDATION'))) {
          
          console.log('Erro de validação de URL, tentando método alternativo');
          
          // Tenta via endpoint proxy que não manipula as URLs
          const directResponse = await createDirectPayment(token, paymentData);
          const directData = await directResponse.json();
          
          if (directResponse.ok && directData.checkout_url) {
            console.log('Pagamento criado com método alternativo:', directData);
            onSuccess(directData.checkout_url);
            return;
          } else {
            console.error('Método alternativo também falhou:', directData);
            throw new Error('Não foi possível processar o pagamento após múltiplas tentativas');
          }
        } 
        // Outros erros do backend
        else {
          console.error('Erro no backend:', data);
          throw new Error(data.detail || 'Erro ao processar pagamento');
        }
      } catch (error) {
        console.error('Erro ao processar pagamento:', error);
        
        // Extrair a mensagem de erro
        let errorMessage = 'Erro ao processar pagamento';
        
        if (error instanceof Error) {
          errorMessage = error.message;
          
          // Verificar se é um erro específico de SQL/banco de dados
          if (errorMessage.includes('SQL syntax') || errorMessage.includes('MariaDB') || errorMessage.includes('ProgrammingError')) {
            errorMessage = 'Erro no sistema ao salvar seus dados. Nossa equipe foi notificada.';
            console.error('Erro de SQL detectado:', error);
          }
        }
        
        handleError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Erro ao processar pagamento:', error);
      
      // Extrair a mensagem de erro
      let errorMessage = 'Erro ao processar pagamento';
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Verificar se é um erro específico de SQL/banco de dados
        if (errorMessage.includes('SQL syntax') || errorMessage.includes('MariaDB') || errorMessage.includes('ProgrammingError')) {
          errorMessage = 'Erro no sistema ao salvar seus dados. Nossa equipe foi notificada.';
          console.error('Erro de SQL detectado:', error);
        }
      }
      
      handleError(errorMessage);
    }
  };

  return (
    <div className="payment-form">
      <div className="modal-header">
        <h2>Pagamento</h2>
        <button className="modal-close-btn" onClick={onClose}>×</button>
      </div>

      <div className="modal-content">
        <h3>Concluir Assinatura</h3>
        <p className="modal-subtitle">Complete seu cadastro para finalizar a assinatura</p>
        
        <div className="plan-info">
          <h4>Selecione seu plano</h4>
          {products.length > 0 ? (
            <div className="plan-options">
              {products.map(product => (
                <div 
                  key={product.id}
                  className={`plan-option ${selectedProductId === product.id ? 'selected' : ''}`}
                  onClick={() => setSelectedProductId(product.id)}
                >
                  <div className="plan-name">Assinatura {product.name}</div>
                  <div className="plan-description">{product.description}</div>
                  <div className="plan-price">R$ {(product.price / 100).toFixed(2)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="loading-text">Carregando planos disponíveis...</p>
          )}
        </div>

        <h4>Método de Pagamento</h4>
        <div className="payment-methods">
          <div className="payment-method-option selected">
            PIX
          </div>
        </div>

        <div className="payment-info-box">
          <p>Após preencher seus dados, você receberá um QR Code para pagamento via PIX.</p>
          <p>O pagamento será processado instantaneamente após a confirmação.</p>
        </div>

        {error && (
          <div className="form-error">
            <AlertIcon /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="billing-form">
          <h4>Dados para Faturamento</h4>
          
          {isLoadingUserData && (
            <div className="loading-indicator">
              <p>Carregando seus dados salvos...</p>
            </div>
          )}
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="taxId">CPF/CNPJ*</label>
              <input
                type="text"
                id="taxId"
                name="taxId"
                value={formData.taxId}
                onChange={handleChange}
                placeholder="000.000.000-00"
                className="form-control"
                required
              />
              <div className="form-helper">
                Documento necessário para emissão de nota fiscal e identificação do pagamento.
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="cellphone">Celular*</label>
              <input
                type="text"
                id="cellphone"
                name="cellphone"
                value={formData.cellphone}
                onChange={handleChange}
                placeholder="(00) 00000-0000"
                className="form-control"
                required
              />
              <div className="form-helper">
                Usado para contato e suporte relacionado à sua assinatura.
              </div>
            </div>
          </div>

          <h4>Endereço (obrigatório)</h4>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="address">Rua*</label>
              <input
                type="text"
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="Nome da rua"
                className="form-control"
                required
              />
              <div className="form-helper">
                Endereço completo para registro da assinatura.
              </div>
            </div>
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
                placeholder="Número"
                className="form-control"
                required
              />
              <div className="form-helper">
                Número do endereço.
              </div>
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
                className="form-control"
              />
              <div className="form-helper">
                Informações adicionais como apartamento, bloco ou ponto de referência.
              </div>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="neighborhood">Bairro*</label>
              <input
                type="text"
                id="neighborhood"
                name="neighborhood"
                value={formData.neighborhood}
                onChange={handleChange}
                placeholder="Bairro"
                className="form-control"
                required
              />
              <div className="form-helper">
                Bairro do endereço para registro.
              </div>
            </div>
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
                placeholder="Cidade"
                className="form-control"
                required
              />
              <div className="form-helper">
                Cidade onde o endereço está localizado.
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="state">Estado*</label>
              <input
                type="text"
                id="state"
                name="state"
                value={formData.state}
                onChange={handleChange}
                placeholder="UF"
                className="form-control"
                required
              />
              <div className="form-helper">
                Estado (UF) onde o endereço está localizado.
              </div>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="postalCode">CEP*</label>
              <input
                type="text"
                id="postalCode"
                name="postalCode"
                value={formData.postalCode}
                onChange={handleChange}
                placeholder="00000-000"
                className="form-control"
                required
              />
              <div className="form-helper">
                Código postal do endereço para validação e registro.
              </div>
            </div>
          </div>

          <div className="checkout-disclaimer">
            <p>Ao clicar em "Finalizar Pagamento", você será redirecionado para a plataforma segura do AbacatePay para completar o pagamento de acordo com o método escolhido.</p>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Processando...' : 'Finalizar Pagamento'}
            </button>
            <button 
              type="button" 
              className="btn btn-outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Voltar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PaymentForm; 