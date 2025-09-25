import React from 'react';
import { Message } from '../../types';
import styles from './MessageList.module.css';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getAgentDisplayName = (agentType?: string) => {
    if (!agentType) return 'Assistant';
    
    switch (agentType) {
      case 'MathAgent':
        return 'Math Assistant';
      case 'KnowledgeAgent':
        return 'Knowledge Assistant';
      case 'RouterAgent':
        return 'Router';
      default:
        return agentType;
    }
  };

  const getAgentIcon = (agentType?: string) => {
    switch (agentType) {
      case 'MathAgent':
        return '🧮';
      case 'KnowledgeAgent':
        return '📚';
      case 'RouterAgent':
        return '🔀';
      default:
        return '🤖';
    }
  };

  return (
    <div className={styles.messageList}>
      {messages.length === 0 && !isLoading && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>💬</div>
          <h3>Start a conversation</h3>
          <p>Ask me about InfinitePay services or mathematical calculations!</p>
          <div className={styles.exampleQueries}>
            <div className={styles.exampleQuery}>
              <span className={styles.exampleIcon}>📚</span>
              "What are the card machine fees?"
            </div>
            <div className={styles.exampleQuery}>
              <span className={styles.exampleIcon}>🧮</span>
              "What is 65 × 3.11?"
            </div>
          </div>
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={index}
          className={`${styles.messageItem} ${
            message.sender === 'user' ? styles.userMessage : styles.agentMessage
          }`}
        >
          <div className={styles.messageContent}>
            <div className={styles.messageHeader}>
              {message.sender === 'agent' && (
                <div className={styles.agentInfo}>
                  <span className={styles.agentIcon}>
                    {getAgentIcon(message.agentType)}
                  </span>
                  <span className={styles.agentName}>
                    {getAgentDisplayName(message.agentType)}
                  </span>
                </div>
              )}
              <span className={styles.timestamp}>
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
            <div className={styles.messageText}>
              {message.content}
            </div>
          </div>
        </div>
      ))}

      {isLoading && (
        <div className={`${styles.messageItem} ${styles.agentMessage}`}>
          <div className={styles.messageContent}>
            <div className={styles.messageHeader}>
              <div className={styles.agentInfo}>
                <span className={styles.agentIcon}>🤖</span>
                <span className={styles.agentName}>Assistant</span>
              </div>
            </div>
            <div className={styles.loadingIndicator}>
              <div className={styles.typingDots}>
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className={styles.loadingText}>Thinking...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;