import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SidePanel from './SidePanel';

// Mock do serviço de API
jest.mock('../../services/api', () => ({
  evaluatePrompt: jest.fn(() => Promise.resolve({
    evaluation: {
      optimized_prompt: 'Prompt otimizado de teste',
      suggestions: ['Sugestão 1', 'Sugestão 2'],
      clarity_score: 8,
      context_score: 7,
      effectiveness_score: 7.5
    }
  }))
}));

describe('SidePanel Component', () => {
  const mockProps = {
    isOpen: true,
    prompt: 'Prompt de teste original',
    onClose: jest.fn(),
    onApply: jest.fn()
  };

  test('renderiza o painel corretamente quando aberto', () => {
    render(<SidePanel {...mockProps} />);
    
    expect(screen.getByText('Avaliador de Prompts')).toBeInTheDocument();
    expect(screen.getByText('Prompt Original')).toBeInTheDocument();
    expect(screen.getByText('Prompt de teste original')).toBeInTheDocument();
    expect(screen.getByText('Avaliar Prompt')).toBeInTheDocument();
  });

  test('renderiza o painel fechado quando isOpen é false', () => {
    const closedProps = { ...mockProps, isOpen: false };
    const { container } = render(<SidePanel {...closedProps} />);
    
    const panel = container.querySelector('.prompt-evaluator-side-panel');
    expect(panel).not.toHaveClass('open');
  });

  test('chama a função onClose quando o botão de fechar é clicado', () => {
    render(<SidePanel {...mockProps} />);
    
    const closeButton = screen.getByRole('button', { name: '✕' });
    fireEvent.click(closeButton);
    
    expect(mockProps.onClose).toHaveBeenCalledTimes(1);
  });

  test('dispara a avaliação quando o botão de avaliar é clicado', async () => {
    render(<SidePanel {...mockProps} />);
    
    const evaluateButton = screen.getByText('Avaliar Prompt');
    fireEvent.click(evaluateButton);
    
    // Aguarda a renderização após a chamada da API
    const optimizedPromptHeading = await screen.findByText('Prompt Otimizado');
    expect(optimizedPromptHeading).toBeInTheDocument();
    expect(await screen.findByText('Prompt otimizado de teste')).toBeInTheDocument();
  });
}); 