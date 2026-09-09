/**
 * ChatMessages - Renders chat message history with emotional context
 */

import React, { useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import { StructuredMessage } from './content-blocks';
import { ThinkingIndicator } from './ThinkingIndicator';
import { ReasoningChain } from './ReasoningChain';
import type { Message, PipelineStage, ReasoningMode, EmotionAnalysis } from '../types';

interface ChatMessagesProps {
  messages: Message[];
  pipelineStage?: PipelineStage;
  showEmotions?: boolean;
  autoScroll?: boolean;
  className?: string;
  renderMessage?: (message: Message) => React.ReactNode;
  /** Current reasoning text being streamed (for live display) */
  currentReasoning?: string | null;
  /** Whether reasoning is actively streaming */
  isReasoningStreaming?: boolean;
  /** Current reasoning mode */
  reasoningMode?: ReasoningMode;
}

export function ChatMessages({
  messages,
  pipelineStage = 'idle',
  showEmotions = true,
  autoScroll = true,
  className,
  renderMessage,
  currentReasoning,
  isReasoningStreaming = false,
  reasoningMode = 'quick',
}: ChatMessagesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, autoScroll]);

  return (
    <div ref={containerRef} className={clsx('anima-chat-messages', className)}>
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {messages.map((message) =>
            renderMessage ? (
              renderMessage(message)
            ) : (
              <React.Fragment key={message.id}>
                {message.role === 'assistant' && message.reasoning && (
                  <ReasoningChain
                    reasoning={message.reasoning}
                    isStreaming={false}
                    tokenCount={message.llmUsage}
                  />
                )}
                <MessageBubble
                  message={message}
                  showEmotions={showEmotions}
                />
              </React.Fragment>
            )
          )}
        </>
      )}

      {pipelineStage !== 'idle' && (
        <ThinkingIndicator
          stage={pipelineStage}
          reasoning={currentReasoning || undefined}
          isReasoningStreaming={isReasoningStreaming}
          reasoningMode={reasoningMode}
        />
      )}
    </div>
  );
}

// =============================================================================
// Message Bubble
// =============================================================================

interface MessageBubbleProps {
  message: Message;
  showEmotions?: boolean;
}

function MessageBubble({ message, showEmotions }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  return (
    <div
      className={clsx(
        'anima-message',
        isUser ? 'anima-message-user' : 'anima-message-assistant',
        isStreaming && 'anima-message-streaming'
      )}
    >
      <div className="anima-message-content">
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <StructuredMessage content={message.content} />
        )}

        {isStreaming && (
          <span className="anima-cursor" />
        )}
      </div>

      {!isUser && showEmotions && message.emotions && (
        <EmotionBadge emotions={message.emotions} />
      )}

      <MessageTimestamp timestamp={message.timestamp} />
    </div>
  );
}

// =============================================================================
// Emotion Badge
// =============================================================================

interface EmotionBadgeProps {
  emotions: EmotionAnalysis;
}

const emotionColors: Record<string, string> = {
  joy: 'var(--anima-emotion-joy, #FFD700)',
  love: 'var(--anima-emotion-love, #FF69B4)',
  sadness: 'var(--anima-emotion-sadness, #4169E1)',
  anger: 'var(--anima-emotion-anger, #DC143C)',
  fear: 'var(--anima-emotion-fear, #800080)',
  surprise: 'var(--anima-emotion-surprise, #FF8C00)',
  trust: 'var(--anima-emotion-trust, #32CD32)',
  anticipation: 'var(--anima-emotion-anticipation, #00CED1)',
  neutral: 'var(--anima-emotion-neutral, #808080)',
};

function EmotionBadge({ emotions }: EmotionBadgeProps) {
  const color = emotionColors[emotions.category] || emotionColors.neutral;
  const intensityPercent = Math.round(emotions.intensity * 100);

  return (
    <div
      className="anima-emotion-badge"
      style={{ '--emotion-color': color } as React.CSSProperties}
    >
      <span className="anima-emotion-category">{emotions.category}</span>
      <span className="anima-emotion-intensity">{intensityPercent}%</span>
    </div>
  );
}

// =============================================================================
// Message Timestamp
// =============================================================================

interface MessageTimestampProps {
  timestamp: Date;
}

function MessageTimestamp({ timestamp }: MessageTimestampProps) {
  const date = new Date(timestamp);
  const timeString = date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <time className="anima-message-timestamp" dateTime={date.toISOString()}>
      {timeString}
    </time>
  );
}

// =============================================================================
// Empty State
// =============================================================================

function EmptyState() {
  return (
    <div className="anima-empty-state">
      <div className="anima-empty-icon">💭</div>
      <h3 className="anima-empty-title">Start a conversation</h3>
      <p className="anima-empty-description">
        Share your thoughts, goals, or feelings. I&apos;m here to listen and help.
      </p>
    </div>
  );
}
