import React, { useState, useEffect, useRef } from "react";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { Message } from "../../types";
import { ApiService, ApiError } from "../services/api";
import styles from "./ChatInterface.module.css";

interface ChatInterfaceProps {
  conversationId: string;
  userId: string;
  onUpdateConversation: (
    conversationId: string,
    messageHistory: Message[]
  ) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  conversationId,
  userId,
  onUpdateConversation,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await ApiService.healthCheck();
      setIsConnected(healthy);
    };
    checkHealth();
  }, []);

  // Reset messages when conversation changes
  useEffect(() => {
    setMessages([]);
    setError(null);
  }, [conversationId]);

  const handleSendMessage = async (messageContent: string) => {
    if (!messageContent.trim() || isLoading) return;

    const userMessage: Message = {
      content: messageContent,
      sender: "user",
      timestamp: new Date().toISOString(),
    };

    // Add user message immediately
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    try {
      const response = await ApiService.sendMessage({
        message: messageContent,
        userId,
        conversationId,
      });

      // Determine which agent handled the response
      const handlingAgent =
        response.agent_workflow?.find(
          (workflow) => workflow.agent !== "RouterAgent"
        )?.agent || "Unknown";

      const agentMessage: Message = {
        content: response.response,
        sender: "agent",
        timestamp: new Date().toISOString(),
        agentType: handlingAgent,
      };

      const updatedMessages = [...newMessages, agentMessage];
      setMessages(updatedMessages);
      onUpdateConversation(conversationId, updatedMessages);
    } catch (err) {
      console.error("Failed to send message:", err);

      let errorMessage = "Failed to send message. Please try again.";

      if (err instanceof ApiError) {
        switch (err.code) {
          case "NETWORK_ERROR":
            errorMessage =
              "Unable to connect to the server. Please check your connection.";
            setIsConnected(false);
            break;
          case "VALIDATION_ERROR":
            errorMessage = "Invalid message format. Please try again.";
            break;
          case "RATE_LIMIT_EXCEEDED":
            errorMessage =
              "Too many requests. Please wait a moment before trying again.";
            break;
          default:
            errorMessage = err.message || errorMessage;
        }
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    // Optionally retry the last message
  };

  const handleClearError = () => {
    setError(null);
  };

  return (
    <div className={styles.chatInterface}>
      <div className={styles.header}>
        <h2>Conversation</h2>
        <div className={styles.status}>
          <div
            className={`${styles.statusIndicator} ${
              isConnected ? styles.connected : styles.disconnected
            }`}
          />
          <span>{isConnected ? "Connected" : "Disconnected"}</span>
        </div>
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <span className={styles.errorMessage}>{error}</span>
          <div className={styles.errorActions}>
            <button onClick={handleRetry} className={styles.retryButton}>
              Retry
            </button>
            <button onClick={handleClearError} className={styles.dismissButton}>
              ×
            </button>
          </div>
        </div>
      )}

      <div className={styles.messagesContainer}>
        <MessageList messages={messages} isLoading={isLoading} />
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputContainer}>
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isLoading || !isConnected}
          placeholder={
            !isConnected
              ? "Disconnected - check your connection"
              : isLoading
              ? "Sending..."
              : "Type your message..."
          }
        />
      </div>
    </div>
  );
};

export default ChatInterface;
