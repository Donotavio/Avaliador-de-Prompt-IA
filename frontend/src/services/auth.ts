import { setCsrfToken, fetchCsrfToken } from './api';

// URL base da API
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://avaliadorprompt.com.br/api'
  : 'http://localhost:8000/api';

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
    setCsrfToken('');
    
    return response.ok;
  } catch (error) {
    console.error('Erro no logout:', error);
    
    // Limpa tokens locais mesmo em caso de erro
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setCsrfToken('');
    
    return false;
  }
};

// Função para verificar se o usuário está autenticado
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('token');
};

// Função para atualizar token JWT usando o refresh token
export const refreshToken = async (): Promise<boolean> => {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return false;
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
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
    return false;
  }
};

// Função para obter dados do usuário atual
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
}

// Função para obter dados do usuário atual
export const getCurrentUser = async (): Promise<UserProfile | null> => {
  try {
    // Verifica se o token está disponível
    if (!isAuthenticated()) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      // Se o token estiver expirado, tenta atualizá-lo
      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          // Tenta novamente após atualizar o token
          return getCurrentUser();
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