import React from 'react';
import { ConversationContext } from '../../types';
import styles from './ConversationSelector.module.css';

interface ConversationSelectorProps {
  conversations: ConversationContext[];
  currentConversation: string;
  onConversationSelect: (conversationId: string) => void;
  onNewConversation: () => void;
}

const ConversationSelector: React.FC<ConversationSelectorProps> = ({
  conversations,
  currentConversation,
  onConversationSelect,
  onNewConversation,
}) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getConversationPreview = (conversation: ConversationContext) => {
    if (conversation.messageHistory.length === 0) {
      return 'New conversation';
    }
    const lastMessage = conversation.messageHistory[conversation.messageHistory.length - 1];
    return lastMessage.content.length > 50 
      ? lastMessage.content.substring(0, 50) + '...'
      : lastMessage.content;
  };

  return (
    <div className={styles.conversationSelector}>
      <div className={styles.header}>
        <h3>Conversations</h3>
        <button 
          className={styles.newConversationButton}
          onClick={onNewConversation}
          title="Start new conversation"
        >
          +
        </button>
      </div>
      
      <div className={styles.conversationList}>
        {conversations.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No conversations yet</p>
            <p>Click + to start chatting</p>
          </div>
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.conversationId}
              className={`${styles.conversationItem} ${
                currentConversation === conversation.conversationId 
                  ? styles.active 
                  : ''
              }`}
              onClick={() => onConversationSelect(conversation.conversationId)}
            >
              <div className={styles.conversationPreview}>
                {getConversationPreview(conversation)}
              </div>
              <div className={styles.conversationMeta}>
                <span className={styles.timestamp}>
                  {formatTimestamp(conversation.timestamp)}
                </span>
                <span className={styles.messageCount}>
                  {conversation.messageHistory.length} messages
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationSelector;