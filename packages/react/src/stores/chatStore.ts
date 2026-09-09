/**
 * Chat Store - Manages chat messages and connection state
 */

import { create } from 'zustand';
import type {
  Message,
  ChatState,
  ConnectionStatus,
  PipelineStage,
  ChatResponse,
} from '../types';

interface ChatActions {
  // Message management
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  appendToMessage: (id: string, content: string) => void;
  clearMessages: () => void;

  // Connection state
  setConnectionStatus: (status: ConnectionStatus) => void;
  setPipelineStage: (stage: PipelineStage) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;

  // Streaming support
  startStreaming: (messageId: string) => void;
  endStreaming: (messageId: string, finalContent: string, response?: ChatResponse) => void;

  // Reasoning state
  setCurrentReasoning: (reasoning: string | null) => void;
  setIsReasoningStreaming: (isStreaming: boolean) => void;

  // Reset
  reset: () => void;
}

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  connectionStatus: 'disconnected',
  pipelineStage: 'idle',
  error: null,
  currentReasoning: null,
  isReasoningStreaming: false,
};

export const useChatStore = create<ChatState & ChatActions>((set) => ({
  ...initialState,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  appendToMessage: (id, content) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + content } : msg
      ),
    })),

  clearMessages: () =>
    set({ messages: [] }),

  setConnectionStatus: (status) =>
    set({ connectionStatus: status }),

  setPipelineStage: (stage) =>
    set({ pipelineStage: stage }),

  setLoading: (isLoading) =>
    set({ isLoading }),

  setError: (error) =>
    set({ error }),

  startStreaming: (messageId) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, isStreaming: true } : msg
      ),
    })),

  endStreaming: (messageId, finalContent, response) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              content: finalContent,
              isStreaming: false,
              emotions: response?.emotions,
              reasoning: response?.reasoning,
              llmUsage: response?.llmUsage,
              contextMetadata: response?.contextMetadata,
              metadata: {
                ...msg.metadata,
                goalsDetected: response?.goalsDetected,
                beliefsDetected: response?.beliefsDetected,
                wonderIndex: response?.wonderIndex,
                breakthroughDetected: response?.breakthroughDetected,
              },
            }
          : msg
      ),
      pipelineStage: 'idle',
      isLoading: false,
      currentReasoning: null,
      isReasoningStreaming: false,
    })),

  setCurrentReasoning: (reasoning) =>
    set({ currentReasoning: reasoning }),

  setIsReasoningStreaming: (isStreaming) =>
    set({ isReasoningStreaming: isStreaming }),

  reset: () => set(initialState),
}));

// Selector hooks for optimized re-renders
export const useMessages = () => useChatStore((state) => state.messages);
export const useConnectionStatus = () => useChatStore((state) => state.connectionStatus);
export const usePipelineStage = () => useChatStore((state) => state.pipelineStage);
export const useIsLoading = () => useChatStore((state) => state.isLoading);
export const useChatError = () => useChatStore((state) => state.error);
export const useCurrentReasoning = () => useChatStore((state) => state.currentReasoning);
export const useIsReasoningStreaming = () => useChatStore((state) => state.isReasoningStreaming);
