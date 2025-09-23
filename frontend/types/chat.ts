/**
 * TypeScript interfaces for the modular chatbot frontend.
 */

export interface Message {
  content: string;
  sender: "user" | "agent";
  timestamp: string;
  agentType?: string;
}

export interface ConversationContext {
  conversationId: string;
  userId: string;
  timestamp: string;
  messageHistory: Message[];
}

export interface AgentDecision {
  selectedAgent: string;
  confidence: number;
  reasoning: string;
  alternatives: string[];
}

export interface AgentResponse {
  content: string;
  sourceAgent: string;
  executionTime: number;
  metadata: Record<string, any>;
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  userId: string;
  conversationId: string;
}

export interface ChatResponse {
  response: string;
  source_agent_response: string;
  agent_workflow: Array<{
    agent: string;
    decision: string;
  }>;
}
