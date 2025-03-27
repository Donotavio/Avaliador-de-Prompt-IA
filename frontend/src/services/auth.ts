import { setCsrfToken, fetchCsrfToken, API_BASE_URL, apiFetch } from './api';
import { isTokenExpired } from './tokenUtils';

// Interface para dados de login
interface LoginData {
  username: string;
  password: string;
}

// Interface para resposta do login
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Interface para perfil do usuário
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_premium: boolean;
  is_email_verified: boolean;
}

// Evento personalizado para notificar expiração de token
export const TOKEN_EXPIRED_EVENT = 'token_expired';

// Função para notificar que o token expirou
export const notifyTokenExpired = () => {
  // Dispara um evento para que componentes possam reagir à expiração do token
  window.dispatchEvent(new CustomEvent(TOKEN_EXPIRED_EVENT));
};

// Função para fazer login
export const login = async (data: LoginData): Promise<boolean> => {
  try {
    // Constrói FormData para compatibilidade com OAuth2
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);

    // Faz a requisição de login
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      credentials: 'include', // Importante para receber o cookie CSRF
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro no login');
    }

    // Processa a resposta
    const responseData: LoginResponse = await response.json();
    
    // Armazena o token JWT
    localStorage.setItem('token', responseData.access_token);
    localStorage.setItem('refresh_token', responseData.refresh_token);
    
    // O cookie CSRF já foi definido automaticamente pelo servidor
    // Agora obtém o token CSRF explicitamente para uso no frontend
    try {
      const csrfToken = await fetchCsrfToken();
      setCsrfToken(csrfToken);
    } catch (e) {
      console.warn('Não foi possível obter token CSRF após login', e);
    }

    return true;
  } catch (error) {
    console.error('Erro no login:', error);
    return false;
  }
};

// Função para fazer logout
export const logout = async (): Promise<boolean> => {
  try {
    // Obtém token CSRF se possível
    try {
      await fetchCsrfToken();
    } catch (e) {
      console.warn('Não foi possível obter token CSRF para logout');
    }

    // Faz a requisição de logout
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
        // O cabeçalho X-CSRF-Token é adicionado automaticamente pela função fetchCsrfToken
      }
    });

    // Limpa tokens locais independente da resposta
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setCsrfToken('');
    
    return response.ok;
  } catch (error) {
    console.error('Erro no logout:', error);
    
    // Limpa tokens locais mesmo em caso de erro
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setCsrfToken('');
    
    return false;
  }
};

// Função para verificar se o usuário está autenticado
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('token');
  if (!token) return false;
  
  // Verifica se o token está expirado
  if (isTokenExpired(token)) {
    // Se expirado, tenta refresh automático
    refreshToken().catch(() => {
      // Se o refresh falhar, notifica a expiração do token
      notifyTokenExpired();
    });
    return false;
  }
  
  return true;
};

// Função para atualizar token JWT usando o refresh token
export const refreshToken = async (): Promise<boolean> => {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return false;
    }

    // Verifica se o refresh token também está expirado
    if (isTokenExpired(refreshToken)) {
      notifyTokenExpired();
      return false;
    }

    const response = await apiFetch('/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      notifyTokenExpired();
      return false;
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Atualiza token CSRF após refresh
    try {
      const csrfToken = await fetchCsrfToken();
      setCsrfToken(csrfToken);
    } catch (e) {
      console.warn('Não foi possível atualizar token CSRF após refresh', e);
    }

    return true;
  } catch (error) {
    console.error('Erro ao atualizar token:', error);
    notifyTokenExpired();
    return false;
  }
};

// Função para obter dados do usuário atual
export const getCurrentUser = async (): Promise<UserProfile | null> => {
  try {
    // Verifica se o token está disponível e válido
    if (!isAuthenticated()) {
      return null;
    }

    const response = await apiFetch('/auth/me', {
      method: 'GET'
    });

    if (!response.ok) {
      // Se o token estiver expirado, tenta atualizá-lo
      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          // Tenta novamente após atualizar o token
          return getCurrentUser();
        } else {
          notifyTokenExpired();
          return null;
        }
      }
      return null;
    }

    return response.json();
  } catch (error) {
    console.error('Erro ao obter usuário atual:', error);
    return null;
  }
}; 