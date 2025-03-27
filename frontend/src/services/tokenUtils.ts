/**
 * Utilitários para trabalhar com tokens JWT
 */

/**
 * Verifica se um token JWT está expirado
 * @param token Token JWT a ser verificado
 * @returns true se o token estiver expirado, false caso contrário
 */
export const isTokenExpired = (token: string | null): boolean => {
  if (!token) return true;
  
  try {
    // Dividir o token JWT em suas partes
    const base64Url = token.split('.')[1];
    if (!base64Url) return true;
    
    // Decodificar a parte do payload
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(window.atob(base64));
    
    // Verificar a expiração (exp é em segundos desde a epoch)
    const expirationTime = payload.exp * 1000; // Converter para milissegundos
    const currentTime = Date.now();
    
    return currentTime >= expirationTime;
  } catch (error) {
    console.error('Erro ao verificar expiração do token:', error);
    return true; // Em caso de erro, considerar o token como expirado
  }
};

/**
 * Verifica se o token atual é válido
 * @returns true se o token for válido, false caso contrário
 */
export const isTokenValid = (): boolean => {
  const token = localStorage.getItem('token');
  return !isTokenExpired(token);
}; 