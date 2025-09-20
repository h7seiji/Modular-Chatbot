import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock the API service to avoid network calls in tests
jest.mock('../services/api', () => ({
  ApiService: {
    sendMessage: jest.fn(),
    healthCheck: jest.fn().mockResolvedValue(true),
  },
  ApiError: class MockApiError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'ApiError';
    }
  }
}));

test('renders welcome message when no conversation is selected', () => {
  render(<App />);
  const welcomeElement = screen.getByText(/Welcome to Modular Chatbot/i);
  expect(welcomeElement).toBeInTheDocument();
});

test('renders conversation selector', () => {
  render(<App />);
  const conversationsHeader = screen.getByRole('heading', { name: /Conversations/i });
  expect(conversationsHeader).toBeInTheDocument();
});

test('renders new conversation button', () => {
  render(<App />);
  const newConversationButton = screen.getByTitle(/Start new conversation/i);
  expect(newConversationButton).toBeInTheDocument();
});