import React from 'react';
import Card from '../components/Card';

const TermsPage: React.FC = () => {
  // Ícone de documento para termos de uso
  const DocumentIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>
  );

  // Ícone para seções
  const SectionIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
      <line x1="7" y1="7" x2="7.01" y2="7"></line>
    </svg>
  );

  return (
    <div className="container page-container">
      <div className="policy-header text-center">
        <DocumentIcon />
        <h1 className="main-title">Termos de Uso</h1>
        <p className="subtitle">Condições para utilização da nossa plataforma</p>
        <p className="last-updated">Última atualização: {new Date().toLocaleDateString('pt-BR')}</p>
      </div>
      
      <Card className="policy-card">
        <div className="policy-content">
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">1. Aceitação dos Termos</h2>
            </div>
            <p>
              Ao acessar ou usar o Avaliador de Prompt IA, você concorda em cumprir e ficar vinculado a estes Termos de Uso. 
              Se você não concordar com qualquer parte destes termos, não poderá acessar ou usar nossos serviços.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">2. Descrição do Serviço</h2>
            </div>
            <p>
              O Avaliador de Prompt IA é uma plataforma que permite aos usuários analisar e melhorar prompts para modelos 
              de linguagem de IA. Oferecemos tanto funcionalidades gratuitas quanto premium.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">3. Contas de Usuário</h2>
            </div>
            <p>
              Para acessar certos recursos, você precisa criar uma conta. Você é responsável por manter a confidencialidade 
              de suas credenciais e por todas as atividades realizadas em sua conta. Notifique-nos imediatamente sobre qualquer 
              uso não autorizado da sua conta.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">4. Uso Aceitável</h2>
            </div>
            <p>Ao usar nossos serviços, você concorda em não:</p>
            <ul className="policy-list">
              <li>Violar leis ou regulamentos aplicáveis</li>
              <li>Enviar conteúdo ilegal, ofensivo, difamatório ou prejudicial</li>
              <li>Tentar interferir ou comprometer a integridade ou segurança de nossos sistemas</li>
              <li>Coletar dados de usuários sem autorização</li>
              <li>Usar nossos serviços para spam ou publicidade não solicitada</li>
              <li>Tentar contornar limitações técnicas ou medidas de segurança</li>
            </ul>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">5. Conteúdo do Usuário</h2>
            </div>
            <p>
              Você mantém a propriedade de qualquer conteúdo que enviar para nossa plataforma. Ao enviar conteúdo, 
              você nos concede uma licença mundial, não exclusiva e isenta de royalties para usar, modificar, exibir e 
              distribuir esse conteúdo em conexão com nossos serviços.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">6. Assinaturas e Pagamentos</h2>
            </div>
            <p>
              Oferecemos planos de assinatura pagos que concedem acesso a recursos adicionais. As cobranças são feitas 
              conforme as informações fornecidas durante o processo de compra. Você pode cancelar sua assinatura a qualquer momento.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">7. Propriedade Intelectual</h2>
            </div>
            <p>
              Nossa plataforma, incluindo todo o conteúdo, recursos e funcionalidades, é de nossa propriedade ou de nossos 
              licenciadores e é protegida por leis de propriedade intelectual. Nenhuma parte de nossos serviços pode ser 
              reproduzida, distribuída ou explorada comercialmente sem nossa permissão prévia por escrito.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">8. Limitação de Responsabilidade</h2>
            </div>
            <p>
              Em nenhuma circunstância seremos responsáveis por quaisquer danos indiretos, incidentais, especiais, 
              consequenciais ou punitivos, incluindo perda de lucros, resultantes do uso ou incapacidade de usar nossos serviços.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">9. Modificações nos Termos</h2>
            </div>
            <p>
              Reservamo-nos o direito de modificar estes termos a qualquer momento. Alterações entrarão em vigor após a 
              publicação dos termos atualizados. O uso contínuo de nossos serviços após tais alterações constitui sua 
              aceitação dos novos termos.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">10. Rescisão</h2>
            </div>
            <p>
              Podemos encerrar ou suspender seu acesso aos nossos serviços imediatamente, sem aviso prévio, por qualquer 
              motivo, incluindo violação destes Termos de Uso.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">11. Lei Aplicável</h2>
            </div>
            <p>
              Estes termos serão regidos e interpretados de acordo com as leis do Brasil, independentemente de seus 
              princípios de conflito de leis.
            </p>
          </div>
          
          <div className="policy-section">
            <div className="section-header">
              <SectionIcon />
              <h2 className="section-title">12. Contato</h2>
            </div>
            <p>
              Se você tiver alguma dúvida sobre estes Termos de Uso, entre em contato conosco pelo e-mail 
              <a href="mailto:termos@avaliadorprompt.com.br" className="contact-link"> termos@avaliadorprompt.com.br</a>.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default TermsPage; 