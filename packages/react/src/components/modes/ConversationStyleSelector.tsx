/**
 * ConversationStyleSelector - Allows users to select the conversation style
 */

import React from 'react';
import { useChatModeStore } from '../../stores/chatModeStore';
import type { ConversationStyle } from '../../types';

interface StyleOption {
  value: ConversationStyle;
  label: string;
  description: string;
  color: string;
}

const CONVERSATION_STYLES: StyleOption[] = [
  {
    value: 'balanced',
    label: 'Balanced',
    description: 'Emotionally intelligent with balanced approach',
    color: '#6366f1',
  },
  {
    value: 'therapeutic',
    label: 'Therapeutic',
    description: 'Deep emotional support and validation',
    color: '#ec4899',
  },
  {
    value: 'crisis',
    label: 'Crisis',
    description: 'Immediate stabilization and grounding',
    color: '#ef4444',
  },
  {
    value: 'coaching',
    label: 'Coaching',
    description: 'Performance optimization and growth',
    color: '#f59e0b',
  },
  {
    value: 'casual',
    label: 'Casual',
    description: 'Relaxed, flowing conversation',
    color: '#10b981',
  },
  {
    value: 'analytical',
    label: 'Analytical',
    description: 'Deep pattern analysis and insights',
    color: '#3b82f6',
  },
];

export interface ConversationStyleSelectorProps {
  /** Custom class name */
  className?: string;
  /** Show as dropdown instead of buttons */
  variant?: 'buttons' | 'dropdown';
  /** Callback when style changes */
  onStyleChange?: (style: ConversationStyle | null) => void;
}

export const ConversationStyleSelector: React.FC<ConversationStyleSelectorProps> = ({
  className = '',
  variant = 'buttons',
  onStyleChange,
}) => {
  const conversationStyle = useChatModeStore((state) => state.conversationStyle);
  const setConversationStyle = useChatModeStore((state) => state.setConversationStyle);

  const handleStyleSelect = (style: ConversationStyle | null) => {
    setConversationStyle(style);
    onStyleChange?.(style);
  };

  if (variant === 'dropdown') {
    return (
      <div className={`anima-conversation-style-dropdown ${className}`}>
        <select
          value={conversationStyle || ''}
          onChange={(e) =>
            handleStyleSelect(e.target.value ? (e.target.value as ConversationStyle) : null)
          }
          className="anima-conversation-style-dropdown__select"
        >
          <option value="">Auto (based on context)</option>
          {CONVERSATION_STYLES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <style>{`
          .anima-conversation-style-dropdown__select {
            padding: 8px 12px;
            border: 1px solid var(--anima-border-color, #e0e0e0);
            border-radius: 8px;
            background: var(--anima-bg-secondary, #f8f8f8);
            font-family: inherit;
            font-size: 14px;
            cursor: pointer;
            min-width: 160px;
          }

          .anima-conversation-style-dropdown__select:focus {
            outline: none;
            border-color: var(--anima-primary-color, #6366f1);
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className={`anima-conversation-style-selector ${className}`}>
      <div className="anima-conversation-style-selector__options">
        {CONVERSATION_STYLES.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`anima-conversation-style-selector__option ${
              conversationStyle === option.value
                ? 'anima-conversation-style-selector__option--active'
                : ''
            }`}
            onClick={() =>
              handleStyleSelect(conversationStyle === option.value ? null : option.value)
            }
            title={option.description}
            style={
              conversationStyle === option.value
                ? ({ '--style-color': option.color } as React.CSSProperties)
                : undefined
            }
          >
            <span
              className="anima-conversation-style-selector__indicator"
              style={{ backgroundColor: option.color }}
            />
            <span className="anima-conversation-style-selector__label">{option.label}</span>
          </button>
        ))}
      </div>

      <style>{`
        .anima-conversation-style-selector__options {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .anima-conversation-style-selector__option {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border: 1px solid var(--anima-border-color, #e0e0e0);
          border-radius: 16px;
          background: var(--anima-bg-secondary, #f8f8f8);
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: inherit;
          font-size: 13px;
        }

        .anima-conversation-style-selector__option:hover {
          border-color: var(--anima-border-hover, #ccc);
        }

        .anima-conversation-style-selector__option--active {
          border-color: var(--style-color, #6366f1);
          background: color-mix(in srgb, var(--style-color, #6366f1) 10%, white);
        }

        .anima-conversation-style-selector__indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .anima-conversation-style-selector__label {
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};

export default ConversationStyleSelector;
