/**
 * MessageInput - Chat input with send functionality
 */

import React, { useState, useCallback, useRef, type KeyboardEvent, type FormEvent } from 'react';
import { clsx } from 'clsx';
import type { ConnectionStatus } from '../types';

interface MessageInputProps {
  onSend: (message: string) => void | Promise<void>;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  connectionStatus?: ConnectionStatus;
  className?: string;
  maxLength?: number;
  showCharCount?: boolean;
  autoFocus?: boolean;
}

export function MessageInput({
  onSend,
  placeholder = 'Type your message...',
  disabled = false,
  isLoading = false,
  connectionStatus = 'connected',
  className,
  maxLength = 4000,
  showCharCount = false,
  autoFocus = true,
}: MessageInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isDisabled = disabled || isLoading || connectionStatus !== 'connected';

  const handleSubmit = useCallback(
    async (e?: FormEvent) => {
      e?.preventDefault();

      const trimmedValue = value.trim();
      if (!trimmedValue || isDisabled) return;

      setValue('');
      await onSend(trimmedValue);

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    },
    [value, isDisabled, onSend]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Submit on Enter (without Shift)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      if (newValue.length <= maxLength) {
        setValue(newValue);

        // Auto-resize textarea
        const textarea = e.target;
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
      }
    },
    [maxLength]
  );

  const charCount = value.length;
  const isNearLimit = charCount > maxLength * 0.9;

  return (
    <form onSubmit={handleSubmit} className={clsx('anima-message-input', className)}>
      <div className="anima-input-wrapper">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder(connectionStatus, placeholder)}
          disabled={isDisabled}
          className="anima-textarea"
          rows={1}
          autoFocus={autoFocus}
          aria-label="Message input"
        />

        <button
          type="submit"
          disabled={isDisabled || !value.trim()}
          className="anima-send-button"
          aria-label="Send message"
        >
          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <SendIcon />
          )}
        </button>
      </div>

      <div className="anima-input-footer">
        {connectionStatus !== 'connected' && (
          <ConnectionStatusIndicator status={connectionStatus} />
        )}

        {showCharCount && (
          <span
            className={clsx(
              'anima-char-count',
              isNearLimit && 'anima-char-count-warning'
            )}
          >
            {charCount}/{maxLength}
          </span>
        )}

        <span className="anima-input-hint">
          Press Enter to send, Shift+Enter for new line
        </span>
      </div>
    </form>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function getPlaceholder(status: ConnectionStatus, defaultPlaceholder: string): string {
  switch (status) {
    case 'connecting':
      return 'Connecting...';
    case 'reconnecting':
      return 'Reconnecting...';
    case 'disconnected':
      return 'Disconnected - trying to reconnect...';
    case 'error':
      return 'Connection error';
    default:
      return defaultPlaceholder;
  }
}

function SendIcon() {
  return (
    <svg
      className="anima-send-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function LoadingSpinner() {
  return (
    <svg
      className="anima-loading-spinner"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" opacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" />
    </svg>
  );
}

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
}

function ConnectionStatusIndicator({ status }: ConnectionStatusIndicatorProps) {
  const statusConfig: Record<ConnectionStatus, { label: string; className: string }> = {
    disconnected: { label: 'Disconnected', className: 'anima-status-disconnected' },
    connecting: { label: 'Connecting...', className: 'anima-status-connecting' },
    connected: { label: 'Connected', className: 'anima-status-connected' },
    reconnecting: { label: 'Reconnecting...', className: 'anima-status-reconnecting' },
    error: { label: 'Connection error', className: 'anima-status-error' },
  };

  const config = statusConfig[status];

  return (
    <div className={clsx('anima-connection-status', config.className)}>
      <span className="anima-status-dot" />
      <span className="anima-status-label">{config.label}</span>
    </div>
  );
}
