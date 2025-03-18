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
      </header>
      <main className="app-main">
        <PromptForm userId={userId} />
      </main>
    </div>
  );
};

export default App; 