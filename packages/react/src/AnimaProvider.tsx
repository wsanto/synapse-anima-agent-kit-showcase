/**
 * AnimaProvider - Context provider for Synapse ANIMA Agent
 *
 * Provides chat, memory, and preferences context to all child components.
 */

import React, { createContext, useContext, useMemo, type ReactNode } from 'react';
import { useAnimaChat } from './hooks/useAnimaChat';
import { useAnimaMemory } from './hooks/useAnimaMemory';
import { useAnimaPreferences } from './hooks/useAnimaPreferences';
import type {
  Message,
  ChatResponse,
  ConnectionStatus,
  PipelineStage,
  Memory,
  Breakthrough,
  EmotionalTrajectoryPoint,
  UserPreferences,
} from './types';

// =============================================================================
// Context Types
// =============================================================================

interface AnimaContextValue {
  // Chat
  sendMessage: (content: string, options?: { reasoningMode?: 'quick' | 'deep' }) => Promise<void>;
  messages: Message[];
  isLoading: boolean;
  connectionStatus: ConnectionStatus;
  pipelineStage: PipelineStage;
  error: string | null;
  clearMessages: () => void;
  connect: () => void;
  disconnect: () => void;

  // Reasoning state (for live display)
  currentReasoning: string | null;
  isReasoningStreaming: boolean;

  // Memory
  memories: Memory[];
  breakthroughs: Breakthrough[];
  emotionalTrajectory: EmotionalTrajectoryPoint[];
  memoryViewMode: 'timeline' | 'graph' | 'analytics';
  setMemoryViewMode: (mode: 'timeline' | 'graph' | 'analytics') => void;
  coreMemoriesCount: number;
  recentBreakthroughsCount: number;
  averageWonderIndex: number;
  dominantEmotion: string | null;

  // Preferences
  preferences: UserPreferences;
  setPreferences: (preferences: UserPreferences) => void;
  resetPreferences: () => void;

  // Config
  userId: string;
  sessionId?: string;
}

const AnimaContext = createContext<AnimaContextValue | null>(null);

// =============================================================================
// Provider Props
// =============================================================================

interface AnimaProviderProps {
  /** WebSocket endpoint URL */
  endpoint: string;
  /** User identifier */
  userId: string;
  /** Optional session identifier */
  sessionId?: string;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Callback when connected */
  onConnect?: () => void;
  /** Callback when disconnected */
  onDisconnect?: () => void;
  /** Callback on message received */
  onMessage?: (response: ChatResponse) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Children */
  children: ReactNode;
}

// =============================================================================
// Provider Component
// =============================================================================

export function AnimaProvider({
  endpoint,
  userId,
  sessionId,
  autoConnect = true,
  onConnect,
  onDisconnect,
  onMessage,
  onError,
  children,
}: AnimaProviderProps) {
  // Initialize hooks
  const chat = useAnimaChat({
    endpoint,
    userId,
    sessionId,
    autoConnect,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
  });

  const memory = useAnimaMemory();
  const preferences = useAnimaPreferences();

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo<AnimaContextValue>(
    () => ({
      // Chat
      sendMessage: chat.sendMessage,
      messages: chat.messages,
      isLoading: chat.isLoading,
      connectionStatus: chat.connectionStatus,
      pipelineStage: chat.pipelineStage,
      error: chat.error,
      clearMessages: chat.clearMessages,
      connect: chat.connect,
      disconnect: chat.disconnect,

      // Reasoning state
      currentReasoning: chat.currentReasoning,
      isReasoningStreaming: chat.isReasoningStreaming,

      // Memory
      memories: memory.memories,
      breakthroughs: memory.breakthroughs,
      emotionalTrajectory: memory.emotionalTrajectory,
      memoryViewMode: memory.viewMode,
      setMemoryViewMode: memory.setViewMode,
      coreMemoriesCount: memory.coreMemoriesCount,
      recentBreakthroughsCount: memory.recentBreakthroughsCount,
      averageWonderIndex: memory.averageWonderIndex,
      dominantEmotion: memory.dominantEmotion,

      // Preferences
      preferences: preferences.preferences,
      setPreferences: preferences.setAllPreferences,
      resetPreferences: preferences.resetToDefaults,

      // Config
      userId,
      sessionId,
    }),
    [chat, memory, preferences, userId, sessionId]
  );

  return (
    <AnimaContext.Provider value={contextValue}>
      {children}
    </AnimaContext.Provider>
  );
}

// =============================================================================
// Hook to consume context
// =============================================================================

export function useAnima(): AnimaContextValue {
  const context = useContext(AnimaContext);

  if (!context) {
    throw new Error('useAnima must be used within an AnimaProvider');
  }

  return context;
}

// =============================================================================
// Selective hooks for optimized re-renders
// =============================================================================

export function useAnimaConnection() {
  const context = useAnima();
  return {
    connectionStatus: context.connectionStatus,
    connect: context.connect,
    disconnect: context.disconnect,
    error: context.error,
  };
}

export function useAnimaMessages() {
  const context = useAnima();
  return {
    messages: context.messages,
    sendMessage: context.sendMessage,
    clearMessages: context.clearMessages,
    isLoading: context.isLoading,
    pipelineStage: context.pipelineStage,
  };
}

export function useAnimaEmotions() {
  const context = useAnima();
  return {
    emotionalTrajectory: context.emotionalTrajectory,
    dominantEmotion: context.dominantEmotion,
    averageWonderIndex: context.averageWonderIndex,
  };
}
