/**
 * AnimaChat - Main embeddable chat component
 *
 * A complete, self-contained chat widget that can be dropped into any React app.
 */

import React, { useCallback } from 'react';
import { clsx } from 'clsx';
import { AnimaProvider, useAnima } from './AnimaProvider';
import { ChatMessages } from './components/ChatMessages';
import { MessageInput } from './components/MessageInput';
import { useChatModeStore } from './stores/chatModeStore';
import type { AnimaChatProps, Message, ChatResponse } from './types';

// =============================================================================
// Main AnimaChat Component
// =============================================================================

export function AnimaChat({
  endpoint,
  userId,
  sessionId,
  className,
  theme = 'system',
  initialMessages = [],
  onMessageSent,
  onResponseReceived,
  onConnectionChange,
  onError,
  showMemoryExplorer = false,
  showGoals = false,
  showSettings = false,
  placeholder = 'Share your thoughts...',
  disabled = false,
}: AnimaChatProps) {
  return (
    <AnimaProvider
      endpoint={endpoint}
      userId={userId}
      sessionId={sessionId}
      onConnect={() => onConnectionChange?.('connected')}
      onDisconnect={() => onConnectionChange?.('disconnected')}
      onMessage={onResponseReceived}
      onError={onError}
    >
      <AnimaChatInner
        className={className}
        theme={theme}
        initialMessages={initialMessages}
        onMessageSent={onMessageSent}
        showMemoryExplorer={showMemoryExplorer}
        showGoals={showGoals}
        showSettings={showSettings}
        placeholder={placeholder}
        disabled={disabled}
      />
    </AnimaProvider>
  );
}

// =============================================================================
// Inner Component (uses context)
// =============================================================================

interface AnimaChatInnerProps {
  className?: string;
  theme?: 'light' | 'dark' | 'system';
  initialMessages?: Message[];
  onMessageSent?: (message: Message) => void;
  showMemoryExplorer?: boolean;
  showGoals?: boolean;
  showSettings?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

function AnimaChatInner({
  className,
  theme = 'system',
  initialMessages = [],
  onMessageSent,
  showMemoryExplorer,
  showGoals,
  showSettings,
  placeholder,
  disabled,
}: AnimaChatInnerProps) {
  const {
    messages,
    sendMessage,
    isLoading,
    connectionStatus,
    pipelineStage,
    coreMemoriesCount,
    recentBreakthroughsCount,
    averageWonderIndex,
    currentReasoning,
    isReasoningStreaming,
  } = useAnima();

  // Get reasoning mode from chat mode store
  const reasoningMode = useChatModeStore((state) => state.reasoningMode);

  // Combine initial messages with current messages
  const allMessages = initialMessages.length > 0 && messages.length === 0
    ? initialMessages
    : messages;

  const handleSend = useCallback(
    async (content: string) => {
      const message: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      };

      onMessageSent?.(message);
      await sendMessage(content, { reasoningMode });
    },
    [sendMessage, onMessageSent, reasoningMode]
  );

  return (
    <div
      className={clsx(
        'anima-chat',
        `anima-theme-${theme}`,
        className
      )}
      data-theme={theme}
    >
      {/* Header */}
      <header className="anima-chat-header">
        <div className="anima-header-title">
          <span className="anima-logo">✨</span>
          <span className="anima-title">ANIMA</span>
        </div>

        <div className="anima-header-stats">
          {showMemoryExplorer && (
            <StatBadge
              icon="🧠"
              label="Memories"
              value={coreMemoriesCount}
            />
          )}
          {showGoals && (
            <StatBadge
              icon="💡"
              label="Insights"
              value={recentBreakthroughsCount}
            />
          )}
        </div>

        <div className="anima-header-actions">
          {showMemoryExplorer && (
            <button className="anima-header-button" aria-label="Open memory explorer">
              🧠
            </button>
          )}
          {showGoals && (
            <button className="anima-header-button" aria-label="View goals">
              🎯
            </button>
          )}
          {showSettings && (
            <button className="anima-header-button" aria-label="Settings">
              ⚙️
            </button>
          )}
        </div>
      </header>

      {/* Messages */}
      <ChatMessages
        messages={allMessages}
        pipelineStage={pipelineStage}
        showEmotions={true}
        className="anima-chat-body"
        currentReasoning={currentReasoning}
        isReasoningStreaming={isReasoningStreaming}
        reasoningMode={reasoningMode}
      />

      {/* Input */}
      <div className="anima-chat-footer">
        <MessageInput
          onSend={handleSend}
          placeholder={placeholder}
          disabled={disabled}
          isLoading={isLoading}
          connectionStatus={connectionStatus}
        />
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

interface StatBadgeProps {
  icon: string;
  label: string;
  value: number;
}

function StatBadge({ icon, label, value }: StatBadgeProps) {
  return (
    <div className="anima-stat-badge" title={label}>
      <span className="anima-stat-icon">{icon}</span>
      <span className="anima-stat-value">{value}</span>
    </div>
  );
}

// =============================================================================
// CSS Variables (can be overridden by consumers)
// =============================================================================

/**
 * Default CSS custom properties for AnimaChat styling.
 * Import this in your app or define your own values.
 *
 * :root {
 *   --anima-bg: #ffffff;
 *   --anima-bg-secondary: #f5f5f5;
 *   --anima-text: #1a1a1a;
 *   --anima-text-secondary: #666666;
 *   --anima-border: #e0e0e0;
 *   --anima-primary: #6366f1;
 *   --anima-primary-hover: #4f46e5;
 *   --anima-user-message-bg: #6366f1;
 *   --anima-user-message-text: #ffffff;
 *   --anima-assistant-message-bg: #f5f5f5;
 *   --anima-assistant-message-text: #1a1a1a;
 *   --anima-emotion-joy: #FFD700;
 *   --anima-emotion-love: #FF69B4;
 *   --anima-emotion-sadness: #4169E1;
 *   --anima-emotion-anger: #DC143C;
 *   --anima-emotion-fear: #800080;
 *   --anima-emotion-surprise: #FF8C00;
 *   --anima-emotion-trust: #32CD32;
 *   --anima-emotion-anticipation: #00CED1;
 *   --anima-emotion-neutral: #808080;
 *   --anima-radius: 8px;
 *   --anima-font-family: system-ui, -apple-system, sans-serif;
 * }
 *
 * [data-theme="dark"] {
 *   --anima-bg: #1a1a1a;
 *   --anima-bg-secondary: #2a2a2a;
 *   --anima-text: #ffffff;
 *   --anima-text-secondary: #999999;
 *   --anima-border: #3a3a3a;
 *   --anima-assistant-message-bg: #2a2a2a;
 *   --anima-assistant-message-text: #ffffff;
 * }
 */
