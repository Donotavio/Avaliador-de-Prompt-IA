// Arquivo para configuração dos testes
import '@testing-library/jest-dom';

// Mock do objeto global chrome
global.chrome = {
  storage: {
    local: {
      get: jest.fn(),
      set: jest.fn()
    }
  },
  runtime: {
    sendMessage: jest.fn(),
    onMessage: {
      addListener: jest.fn()
    },
    onInstalled: {
      addListener: jest.fn()
    },
    lastError: null
  },
  tabs: {
    create: jest.fn()
  }
} as unknown as typeof chrome; 