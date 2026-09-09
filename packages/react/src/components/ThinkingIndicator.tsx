/**
 * ThinkingIndicator - Shows pipeline processing status with optional reasoning display
 */

import React, { useState, useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import type { PipelineStage } from '../types';

interface ThinkingIndicatorProps {
  stage: PipelineStage;
  /** Current reasoning text being streamed */
  reasoning?: string;
  /** Whether reasoning is actively streaming */
  isReasoningStreaming?: boolean;
  /** Reasoning mode (affects estimated times) */
  reasoningMode?: 'quick' | 'deep';
  className?: string;
}

const stageLabels: Record<PipelineStage, string> = {
  idle: '',
  analyzing_emotions: 'Analyzing emotions...',
  building_context: 'Building context from your memories...',
  reviewing_goals: 'Reviewing your goals...',
  connecting_beliefs: 'Connecting to your core beliefs...',
  reasoning: 'Generating reasoning chain...',
  generating_response: 'Generating response...',
  enriching: 'Enriching with insights...',
};

const stageIcons: Record<PipelineStage, string> = {
  idle: '',
  analyzing_emotions: '💭',
  building_context: '🧠',
  reviewing_goals: '🎯',
  connecting_beliefs: '💫',
  reasoning: '🧠',
  generating_response: '✨',
  enriching: '🌟',
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function ThinkingIndicator({
  stage,
  reasoning,
  isReasoningStreaming,
  reasoningMode = 'quick',
  className,
}: ThinkingIndicatorProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isReasoningOpen, setIsReasoningOpen] = useState(false);
  const startTimeRef = useRef<number>(Date.now());

  // Timer
  useEffect(() => {
    if (stage === 'idle') return;

    startTimeRef.current = Date.now();
    setElapsedSeconds(0);

    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [stage]);

  // Auto-open reasoning section when streaming starts
  useEffect(() => {
    if (isReasoningStreaming) {
      setIsReasoningOpen(true);
    }
  }, [isReasoningStreaming]);

  if (stage === 'idle') {
    return null;
  }

  const isDeep = reasoningMode === 'deep';

  return (
    <div className={clsx('anima-thinking-indicator', className)}>
      {/* Timer */}
      <div className="anima-thinking-timer">
        <span className="anima-thinking-timer__clock">⏱</span>
        <span className="anima-thinking-timer__time">{formatTime(elapsedSeconds)}</span>
        {isDeep && (
          <span className="anima-thinking-timer__badge">Deep</span>
        )}
      </div>

      {/* Stage Status */}
      <div className="anima-thinking-content">
        <span className="anima-thinking-icon">{stageIcons[stage]}</span>
        <span className="anima-thinking-text">{stageLabels[stage]}</span>
        <div className="anima-thinking-dots">
          <span className="anima-dot" />
          <span className="anima-dot" />
          <span className="anima-dot" />
        </div>
      </div>

      {/* Reasoning Preview (collapsible) */}
      {reasoning && (
        <div className="anima-thinking-reasoning">
          <button
            type="button"
            className="anima-thinking-reasoning__toggle"
            onClick={() => setIsReasoningOpen(!isReasoningOpen)}
          >
            <span>View reasoning chain</span>
            <span
              className="anima-thinking-reasoning__chevron"
              style={{ transform: isReasoningOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
            >
              ▾
            </span>
          </button>

          {isReasoningOpen && (
            <div className="anima-thinking-reasoning__content">
              {reasoning}
            </div>
          )}
        </div>
      )}

      <style>{`
        .anima-thinking-indicator {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 8px 0;
        }

        .anima-thinking-timer {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: var(--anima-text-tertiary, #888);
        }

        .anima-thinking-timer__clock {
          font-size: 12px;
        }

        .anima-thinking-timer__time {
          font-family: monospace;
        }

        .anima-thinking-timer__badge {
          padding: 1px 6px;
          border-radius: 4px;
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          background: var(--anima-primary-light, rgba(99, 102, 241, 0.15));
          color: var(--anima-primary-color, #6366f1);
        }

        .anima-thinking-content {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .anima-thinking-icon {
          font-size: 16px;
        }

        .anima-thinking-text {
          font-size: 13px;
          color: var(--anima-text-secondary, #999);
          font-style: italic;
        }

        .anima-thinking-dots {
          display: flex;
          gap: 3px;
        }

        .anima-dot {
          width: 4px;
          height: 4px;
          border-radius: 50%;
          background: var(--anima-text-tertiary, #666);
          animation: anima-dot-bounce 1.4s infinite ease-in-out;
        }

        .anima-dot:nth-child(2) { animation-delay: 0.2s; }
        .anima-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes anima-dot-bounce {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }

        .anima-thinking-reasoning {
          margin-top: 4px;
        }

        .anima-thinking-reasoning__toggle {
          display: flex;
          align-items: center;
          gap: 4px;
          background: none;
          border: none;
          padding: 4px 0;
          cursor: pointer;
          font-size: 12px;
          color: var(--anima-text-tertiary, #888);
          transition: color 0.2s;
        }

        .anima-thinking-reasoning__toggle:hover {
          color: var(--anima-text-secondary, #bbb);
        }

        .anima-thinking-reasoning__chevron {
          transition: transform 0.2s ease;
          font-size: 10px;
        }

        .anima-thinking-reasoning__content {
          margin-top: 6px;
          padding: 8px 12px;
          border-left: 2px solid var(--anima-border-color, rgba(128, 128, 128, 0.2));
          background: var(--anima-bg-secondary, rgba(0, 0, 0, 0.1));
          border-radius: 0 6px 6px 0;
          font-size: 12px;
          line-height: 1.5;
          color: var(--anima-text-secondary, #ccc);
          white-space: pre-wrap;
          max-height: 200px;
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
}
