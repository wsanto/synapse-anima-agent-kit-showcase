/**
 * ChatModeSelector - Allows users to select the chat mode (ask_advice, set_goals, explore)
 */

import React from 'react';
import { useChatModeStore } from '../../stores/chatModeStore';
import type { ChatMode } from '../../types';

interface ChatModeOption {
  value: ChatMode;
  label: string;
  description: string;
  icon: string;
}

const CHAT_MODES: ChatModeOption[] = [
  {
    value: 'ask_advice',
    label: 'Ask Advice',
    description: 'Get personalized guidance and insights',
    icon: '💡',
  },
  {
    value: 'set_goals',
    label: 'Set Goals',
    description: 'Define and track your objectives',
    icon: '🎯',
  },
  {
    value: 'explore',
    label: 'Explore',
    description: 'Open-ended discovery and reflection',
    icon: '🧭',
  },
];

export interface ChatModeSelectorProps {
  /** Custom class name */
  className?: string;
  /** Show descriptions */
  showDescriptions?: boolean;
  /** Compact mode (icons only) */
  compact?: boolean;
  /** Callback when mode changes */
  onModeChange?: (mode: ChatMode | null) => void;
}

export const ChatModeSelector: React.FC<ChatModeSelectorProps> = ({
  className = '',
  showDescriptions = false,
  compact = false,
  onModeChange,
}) => {
  const chatMode = useChatModeStore((state) => state.chatMode);
  const setChatMode = useChatModeStore((state) => state.setChatMode);

  const handleModeSelect = (mode: ChatMode) => {
    const newMode = chatMode === mode ? null : mode;
    setChatMode(newMode);
    onModeChange?.(newMode);
  };

  return (
    <div className={`anima-chat-mode-selector ${className}`}>
      <div className="anima-chat-mode-selector__options">
        {CHAT_MODES.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`anima-chat-mode-selector__option ${
              chatMode === option.value ? 'anima-chat-mode-selector__option--active' : ''
            } ${compact ? 'anima-chat-mode-selector__option--compact' : ''}`}
            onClick={() => handleModeSelect(option.value)}
            title={compact ? `${option.label}: ${option.description}` : undefined}
          >
            <span className="anima-chat-mode-selector__icon">{option.icon}</span>
            {!compact && (
              <>
                <span className="anima-chat-mode-selector__label">{option.label}</span>
                {showDescriptions && (
                  <span className="anima-chat-mode-selector__description">
                    {option.description}
                  </span>
                )}
              </>
            )}
          </button>
        ))}
      </div>

      <style>{`
        .anima-chat-mode-selector__options {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .anima-chat-mode-selector__option {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          border: 1px solid var(--anima-border-color, #e0e0e0);
          border-radius: 8px;
          background: var(--anima-bg-secondary, #f8f8f8);
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: inherit;
          font-size: 14px;
        }

        .anima-chat-mode-selector__option:hover {
          border-color: var(--anima-primary-color, #6366f1);
          background: var(--anima-bg-hover, #f0f0f0);
        }

        .anima-chat-mode-selector__option--active {
          border-color: var(--anima-primary-color, #6366f1);
          background: var(--anima-primary-light, #eef2ff);
          color: var(--anima-primary-color, #6366f1);
        }

        .anima-chat-mode-selector__option--compact {
          padding: 8px 12px;
        }

        .anima-chat-mode-selector__icon {
          font-size: 18px;
        }

        .anima-chat-mode-selector__label {
          font-weight: 500;
        }

        .anima-chat-mode-selector__description {
          font-size: 12px;
          color: var(--anima-text-secondary, #666);
          display: block;
          margin-top: 2px;
        }
      `}</style>
    </div>
  );
};

export default ChatModeSelector;
