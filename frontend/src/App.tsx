import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import ConversationSelector from './components/ConversationSelector';
import { ConversationContext } from '../types';
import styles from './App.module.css';

const App: React.FC = () => {
  const [currentConversation, setCurrentConversation] = useState<string>('');
  const [conversations, setConversations] = useState<ConversationContext[]>([]);
  const [userId] = useState<string>(() => `user_${Date.now()}`);

  const handleConversationSelect = (conversationId: string) => {
    setCurrentConversation(conversationId);
  };

  const handleNewConversation = () => {
    const newConversationId = `conv_${Date.now()}`;
    const newConversation: ConversationContext = {
      conversationId: newConversationId,
      userId,
      timestamp: new Date().toISOString(),
      messageHistory: []
    };
    
    setConversations(prev => [...prev, newConversation]);
    setCurrentConversation(newConversationId);
  };

  const updateConversation = (conversationId: string, messageHistory: any[]) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.conversationId === conversationId 
          ? { ...conv, messageHistory }
          : conv
      )
    );
  };

  return (
    <div className={styles.app}>
      <div className={styles.sidebar}>
        <ConversationSelector
          conversations={conversations}
          currentConversation={currentConversation}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
        />
      </div>
      <div className={styles.mainContent}>
        {currentConversation ? (
          <ChatInterface
            conversationId={currentConversation}
            userId={userId}
            onUpdateConversation={updateConversation}
          />
        ) : (
          <div className={styles.welcomeMessage}>
            <h2>Welcome to Modular Chatbot</h2>
            <p>Select a conversation or create a new one to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;