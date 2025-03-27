import React from 'react';
import Card from '../components/Card';

const PrivacyPage: React.FC = () => {
  // Ícone de escudo para a política de privacidade
  const ShieldIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </svg>
  );

  // Ícone para seções numeradas
  const NumberIcon = ({ number }: { number: number }) => (
    <div className="section-number">{number}</div>
  );

  return (
    <div className="policy-page">
      <div className="policy-header">
        <ShieldIcon />
        <h1>Política de Privacidade</h1>
        <p>Como protegemos e utilizamos suas informações</p>
        <p className="last-updated">Última atualização: 27/03/2025</p>
      </div>
      
      <Card>
        <div className="policy-content">
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={1} />
              <h2>Introdução</h2>
            </div>
            <p>
              Bem-vindo à Política de Privacidade do Avaliador de Prompt IA. Este documento explica como coletamos, 
              usamos e protegemos suas informações pessoais quando você utiliza nossa plataforma.
            </p>
            <p>
              Ao utilizar nossos serviços, você concorda com as práticas descritas nesta política.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={2} />
              <h2>Informações que Coletamos</h2>
            </div>
            <p>Podemos coletar os seguintes tipos de informações:</p>
            <ul className="policy-list">
              <li><strong>Informações de conta:</strong> nome, endereço de e-mail e dados de autenticação quando você se registra.</li>
              <li><strong>Dados de uso:</strong> informações sobre como você utiliza nossa plataforma, incluindo prompts submetidos para avaliação.</li>
              <li><strong>Informações técnicas:</strong> endereço IP, tipo de navegador, dispositivo e sistema operacional.</li>
              <li><strong>Informações de pagamento:</strong> dados necessários para processar transações quando você adquire serviços premium.</li>
            </ul>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={3} />
              <h2>Como Utilizamos suas Informações</h2>
            </div>
            <p>Utilizamos suas informações para:</p>
            <ul className="policy-list">
              <li>Fornecer, manter e melhorar nossos serviços</li>
              <li>Processar transações e enviar notificações relacionadas</li>
              <li>Responder a solicitações de suporte e contato</li>
              <li>Detectar e prevenir atividades fraudulentas</li>
              <li>Personalizar sua experiência com base em suas preferências</li>
              <li>Desenvolver novos recursos e funcionalidades</li>
            </ul>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={4} />
              <h2>Compartilhamento de Informações</h2>
            </div>
            <p>
              Não vendemos suas informações pessoais. Podemos compartilhar suas informações nas seguintes circunstâncias:
            </p>
            <ul className="policy-list">
              <li>Com provedores de serviços que nos ajudam a operar nossa plataforma</li>
              <li>Para cumprir obrigações legais</li>
              <li>Para proteger nossos direitos, privacidade, segurança ou propriedade</li>
              <li>Em conexão com uma fusão, aquisição ou venda de ativos</li>
            </ul>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={5} />
              <h2>Segurança</h2>
            </div>
            <p>
              Implementamos medidas de segurança técnicas e organizacionais para proteger suas informações contra acesso não autorizado, 
              alteração, divulgação ou destruição.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={6} />
              <h2>Seus Direitos</h2>
            </div>
            <p>Dependendo da sua localização, você pode ter direitos relacionados aos seus dados pessoais, incluindo:</p>
            <ul className="policy-list">
              <li>Acessar, corrigir ou excluir seus dados</li>
              <li>Restringir ou se opor ao processamento de seus dados</li>
              <li>Solicitar a portabilidade de seus dados</li>
              <li>Retirar seu consentimento a qualquer momento</li>
            </ul>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={7} />
              <h2>Alterações nesta Política</h2>
            </div>
            <p>
              Podemos atualizar esta política periodicamente. Publicaremos quaisquer alterações em nosso site e, 
              se as alterações forem significativas, forneceremos um aviso mais proeminente.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <NumberIcon number={8} />
              <h2>Contato</h2>
            </div>
            <p>
              Se você tiver dúvidas ou preocupações sobre esta política ou nossas práticas de privacidade, 
              entre em contato conosco em <a href="mailto:contato@avaliadorprompt.com">contato@avaliadorprompt.com</a>.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default PrivacyPage; 