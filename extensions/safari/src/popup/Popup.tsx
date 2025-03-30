import React, { useEffect, useState } from 'react';
import { PlanType } from '../types';

interface UserInfo {
  id?: string;
  plan_type: PlanType;
  email?: string;
  remaining_evaluations: number;
  is_premium?: boolean;
}

const Popup: React.FC = () => {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  
  useEffect(() => {
    // Carrega as informações do usuário
    const loadUserInfo = async () => {
      try {
        // Obtém dados do storage local
        chrome.storage.local.get(['userInfo'], (result) => {
          if (result.userInfo) {
            setUserInfo(result.userInfo);
          } else {
            setUserInfo({
              plan_type: PlanType.FREE,
              remaining_evaluations: 3
            });
          }
          setLoading(false);
        });
        
        // Atualiza o status do usuário no servidor
        chrome.runtime.sendMessage(
          { action: 'checkUserStatus' },
          (response) => {
            if (!chrome.runtime.lastError && response && !response.error) {
              setUserInfo(response);
            }
          }
        );
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        setLoading(false);
      }
    };
    
    loadUserInfo();
  }, []);
  
  const handleOpenWebsite = () => {
    chrome.tabs.create({ url: 'https://avaliadorprompt.com.br' });
  };
  
  const handleOpenSettings = () => {
    chrome.tabs.create({ url: 'https://avaliadorprompt.com.br/account' });
  };
  
  if (loading) {
    return (
      <div className="popup-container loading">
        <div className="spinner"></div>
        <p>Carregando...</p>
      </div>
    );
  }
  
  return (
    <div className="popup-container">
      <div className="popup-header">
        <h1>Avaliador de Prompts</h1>
        <p className="version">v1.0.0</p>
      </div>
      
      <div className="popup-content">
        <div className="plan-info">
          <span className="plan-type">
            {userInfo?.is_premium ? 'Plano Premium' : 'Plano Gratuito'}
          </span>
          
          {!userInfo?.is_premium && (
            <div className="remaining-evaluations">
              <span className="label">Avaliações Restantes:</span>
              <span className="value">{userInfo?.remaining_evaluations || 0}</span>
            </div>
          )}
        </div>
        
        <div className="popup-instructions">
          <p>
            Esta extensão detecta automaticamente as áreas de texto em sites de IA como 
            ChatGPT, Claude e Gemini.
          </p>
          <p>
            Clique no botão <strong>✏️</strong> que aparece próximo à área de texto 
            para avaliar e otimizar seu prompt.
          </p>
        </div>
        
        <div className="popup-actions">
          <button 
            className="button-primary"
            onClick={handleOpenWebsite}
          >
            Visitar Website
          </button>
          
          <button 
            className="button-secondary"
            onClick={handleOpenSettings}
          >
            Configurações
          </button>
        </div>
      </div>
      
      <div className="popup-footer">
        <p>
          © {new Date().getFullYear()} Avaliador de Prompts
        </p>
      </div>
    </div>
  );
};

export default Popup; 