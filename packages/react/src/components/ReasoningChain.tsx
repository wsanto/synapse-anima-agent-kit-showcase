/**
 * ReasoningChain Component
 *
 * Displays ANIMA's reasoning/thought process with progressive disclosure.
 * Shows why ANIMA responded the way it did, including what beliefs,
 * memories, goals, and emotions influenced the response.
 *
 * Features:
 * - Letter-by-letter streaming animation
 * - Starts collapsed with blur gradient preview
 * - Smooth expand/collapse
 * - Token usage footer
 * - "Thought for X seconds" completion state
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { preprocessReasoning } from '../utils/reasoning';

export interface ReasoningChainProps {
  /** The reasoning text to display */
  reasoning?: string;
  /** Whether reasoning is actively being streamed */
  isStreaming?: boolean;
  /** Token usage metrics */
  tokenCount?: {
    reasoning_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  /** Time taken for reasoning in seconds */
  completionTime?: number;
  /** Custom class name */
  className?: string;
}

export function ReasoningChain({
  reasoning,
  isStreaming = false,
  tokenCount,
  completionTime,
  className = '',
}: ReasoningChainProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [thoughtDuration, setThoughtDuration] = useState<number>(0);
  const animationRef = useRef<number>();

  // Track when reasoning completes
  useEffect(() => {
    if (!isStreaming && reasoning && !isComplete) {
      setIsComplete(true);
      const duration = completionTime || Math.ceil((reasoning.length / 1000) * 4);
      setThoughtDuration(duration);
    }
  }, [isStreaming, reasoning, isComplete, completionTime]);

  // Letter-by-letter streaming animation
  useEffect(() => {
    if (!reasoning || !isExpanded) {
      setDisplayedText('');
      return;
    }

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    let currentIndex = 0;
    const text = reasoning;
    const startTime = Date.now();
    const charsPerSecond = 80;

    const animate = () => {
      const elapsed = (Date.now() - startTime) / 1000;
      const targetIndex = Math.min(Math.floor(elapsed * charsPerSecond), text.length);

      if (targetIndex !== currentIndex) {
        currentIndex = targetIndex;
        setDisplayedText(text.slice(0, currentIndex));
      }

      if (currentIndex < text.length) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [reasoning, isExpanded]);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  // Don't render if no content
  if (!reasoning && !isStreaming) {
    return null;
  }

  const shouldShowPreview = !isExpanded && reasoning && reasoning.length > 100;
  const processed = preprocessReasoning(displayedText);

  return (
    <div className={`anima-reasoning-chain ${className}`}>
      {/* Header Button */}
      <button
        type="button"
        className="anima-reasoning-chain__header"
        onClick={toggleExpanded}
      >
        <span className="anima-reasoning-chain__label">
          {isComplete
            ? `Thought for ${thoughtDuration} seconds`
            : isStreaming
            ? 'Thinking...'
            : 'View reasoning chain'}
        </span>

        {isStreaming && (
          <span className="anima-reasoning-chain__dots">
            <span className="anima-reasoning-chain__dot" />
            <span className="anima-reasoning-chain__dot" />
            <span className="anima-reasoning-chain__dot" />
          </span>
        )}

        <span
          className="anima-reasoning-chain__chevron"
          style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </button>

      {/* Collapsed Preview */}
      {!isExpanded && shouldShowPreview && (
        <div
          className="anima-reasoning-chain__preview"
          onClick={toggleExpanded}
        >
          <div className="anima-reasoning-chain__preview-text">
            {reasoning.slice(0, 150)}...
          </div>
          <div className="anima-reasoning-chain__preview-gradient" />
        </div>
      )}

      {/* Expanded Content */}
      {isExpanded && (
        <div className="anima-reasoning-chain__content">
          <div
            className="anima-reasoning-chain__text"
            dangerouslySetInnerHTML={{ __html: simpleMarkdown(processed) }}
          />
          {displayedText.length < (reasoning?.length || 0) && (
            <span className="anima-reasoning-chain__cursor" />
          )}

          {/* Token Usage Footer */}
          {tokenCount && (
            <div className="anima-reasoning-chain__tokens">
              <div className="anima-reasoning-chain__tokens-left">
                {tokenCount.reasoning_tokens != null && (
                  <span>Reasoning: <strong>{tokenCount.reasoning_tokens.toLocaleString()}</strong> tokens</span>
                )}
                {tokenCount.completion_tokens != null && (
                  <span>Response: <strong>{tokenCount.completion_tokens.toLocaleString()}</strong> tokens</span>
                )}
              </div>
              {tokenCount.total_tokens != null && (
                <span>Total: <strong>{tokenCount.total_tokens.toLocaleString()}</strong> tokens</span>
              )}
            </div>
          )}
        </div>
      )}

      <style>{`
        .anima-reasoning-chain {
          margin-bottom: 12px;
          border: 1px solid var(--anima-border-color, rgba(128, 128, 128, 0.2));
          border-radius: 8px;
          overflow: hidden;
          background: var(--anima-bg-secondary, rgba(0, 0, 0, 0.15));
        }

        .anima-reasoning-chain__header {
          width: 100%;
          padding: 10px 14px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: none;
          border: none;
          cursor: pointer;
          color: var(--anima-text-secondary, #999);
          transition: background 0.2s ease;
        }

        .anima-reasoning-chain__header:hover {
          background: var(--anima-bg-hover, rgba(128, 128, 128, 0.1));
        }

        .anima-reasoning-chain__label {
          font-size: 13px;
          font-weight: 400;
        }

        .anima-reasoning-chain__dots {
          display: flex;
          gap: 3px;
          margin-left: 8px;
        }

        .anima-reasoning-chain__dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--anima-primary-color, #f59e0b);
          opacity: 0.5;
          animation: anima-reasoning-dot-pulse 1.4s infinite ease-in-out;
        }

        .anima-reasoning-chain__dot:nth-child(2) {
          animation-delay: 0.2s;
        }

        .anima-reasoning-chain__dot:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes anima-reasoning-dot-pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }

        .anima-reasoning-chain__chevron {
          transition: transform 0.3s ease;
          display: flex;
          align-items: center;
        }

        .anima-reasoning-chain__preview {
          position: relative;
          padding: 0 14px 8px;
          cursor: pointer;
          overflow: hidden;
          max-height: 60px;
        }

        .anima-reasoning-chain__preview-text {
          font-size: 13px;
          color: var(--anima-text-tertiary, rgba(150, 150, 150, 0.8));
          font-family: monospace;
          line-height: 1.5;
        }

        .anima-reasoning-chain__preview-gradient {
          position: absolute;
          inset: 0;
          top: auto;
          height: 40px;
          background: linear-gradient(to top, var(--anima-bg-secondary, rgba(0, 0, 0, 0.3)), transparent);
          pointer-events: none;
        }

        .anima-reasoning-chain__content {
          border-top: 1px solid var(--anima-border-color, rgba(128, 128, 128, 0.15));
          padding: 14px;
          max-height: 400px;
          overflow-y: auto;
        }

        .anima-reasoning-chain__text {
          font-size: 13px;
          line-height: 1.6;
          color: var(--anima-text-primary, #e0e0e0);
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .anima-reasoning-chain__text strong {
          color: var(--anima-text-bright, #fff);
          font-weight: 600;
        }

        .anima-reasoning-chain__text p {
          margin: 6px 0;
        }

        .anima-reasoning-chain__cursor {
          display: inline-block;
          width: 2px;
          height: 14px;
          background: var(--anima-primary-color, #f59e0b);
          opacity: 0.5;
          margin-left: 2px;
          vertical-align: middle;
          animation: anima-reasoning-cursor-blink 0.6s infinite;
        }

        @keyframes anima-reasoning-cursor-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }

        .anima-reasoning-chain__tokens {
          margin-top: 12px;
          padding-top: 10px;
          border-top: 1px solid var(--anima-border-color, rgba(128, 128, 128, 0.15));
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 11px;
          color: var(--anima-text-tertiary, #777);
        }

        .anima-reasoning-chain__tokens-left {
          display: flex;
          gap: 16px;
        }

        .anima-reasoning-chain__tokens strong {
          color: var(--anima-text-secondary, #aaa);
        }
      `}</style>
    </div>
  );
}

/**
 * Simple markdown to HTML converter for reasoning text.
 * Handles bold, italic, paragraphs, and line breaks.
 */
function simpleMarkdown(text: string): string {
  if (!text) return '';

  return text
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic: *text*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Line breaks to paragraphs
    .replace(/\n\n/g, '</p><p>')
    // Single line breaks
    .replace(/\n/g, '<br/>')
    // Wrap in paragraph
    .replace(/^(.+)$/, '<p>$1</p>');
}

export default ReasoningChain;
