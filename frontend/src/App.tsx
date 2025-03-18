import React from 'react';
import PromptForm from './components/PromptForm';
import './App.css';

const App: React.FC = () => {
  // ID do usuário mockado para desenvolvimento
  const userId = "user123";

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avaliador de Prompts IA</h1>
        <p>Otimize seus prompts para resultados melhores com qualquer LLM</p>
      </header>
      <main className="app-main">
        <PromptForm userId={userId} />
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Avaliador de Prompts IA. Todos os direitos reservados.</p>
      </footer>
    </div>
  );
};

export default App; 