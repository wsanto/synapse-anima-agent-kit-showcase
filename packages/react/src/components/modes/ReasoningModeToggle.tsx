/**
 * ReasoningModeToggle - Toggle between quick and deep reasoning modes
 */

import React from 'react';
import { useChatModeStore } from '../../stores/chatModeStore';
import type { ReasoningMode } from '../../types';

export interface ReasoningModeToggleProps {
  /** Custom class name */
  className?: string;
  /** Compact variant */
  compact?: boolean;
  /** Show labels */
  showLabels?: boolean;
  /** Callback when mode changes */
  onModeChange?: (mode: ReasoningMode) => void;
}

export const ReasoningModeToggle: React.FC<ReasoningModeToggleProps> = ({
  className = '',
  compact = false,
  showLabels = true,
  onModeChange,
}) => {
  const reasoningMode = useChatModeStore((state) => state.reasoningMode);
  const setReasoningMode = useChatModeStore((state) => state.setReasoningMode);

  const handleToggle = () => {
    const newMode = reasoningMode === 'quick' ? 'deep' : 'quick';
    setReasoningMode(newMode);
    onModeChange?.(newMode);
  };

  const isDeep = reasoningMode === 'deep';

  return (
    <div className={`anima-reasoning-toggle ${className} ${compact ? 'anima-reasoning-toggle--compact' : ''}`}>
      {showLabels && !compact && (
        <span className="anima-reasoning-toggle__label">
          {isDeep ? 'Deep' : 'Quick'}
        </span>
      )}

      <button
        type="button"
        className={`anima-reasoning-toggle__button ${isDeep ? 'anima-reasoning-toggle__button--deep' : ''}`}
        onClick={handleToggle}
        title={isDeep ? 'Deep reasoning - thorough analysis' : 'Quick reasoning - fast responses'}
        aria-pressed={isDeep}
      >
        <span className="anima-reasoning-toggle__track">
          <span className="anima-reasoning-toggle__thumb">
            {isDeep ? '🧠' : '⚡'}
          </span>
        </span>
      </button>

      {showLabels && compact && (
        <span className="anima-reasoning-toggle__label-compact">
          {isDeep ? '🧠' : '⚡'}
        </span>
      )}

      <style>{`
        .anima-reasoning-toggle {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .anima-reasoning-toggle--compact {
          gap: 4px;
        }

        .anima-reasoning-toggle__label {
          font-size: 13px;
          font-weight: 500;
          color: var(--anima-text-secondary, #666);
          min-width: 40px;
        }

        .anima-reasoning-toggle__button {
          position: relative;
          width: 52px;
          height: 28px;
          border: none;
          border-radius: 14px;
          background: var(--anima-bg-tertiary, #e0e0e0);
          cursor: pointer;
          transition: all 0.3s ease;
          padding: 0;
        }

        .anima-reasoning-toggle__button:hover {
          background: var(--anima-bg-hover, #d0d0d0);
        }

        .anima-reasoning-toggle__button--deep {
          background: var(--anima-primary-color, #6366f1);
        }

        .anima-reasoning-toggle__button--deep:hover {
          background: var(--anima-primary-dark, #4f46e5);
        }

        .anima-reasoning-toggle__track {
          position: relative;
          display: block;
          width: 100%;
          height: 100%;
        }

        .anima-reasoning-toggle__thumb {
          position: absolute;
          top: 2px;
          left: 2px;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          transition: transform 0.3s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .anima-reasoning-toggle__button--deep .anima-reasoning-toggle__thumb {
          transform: translateX(24px);
        }

        .anima-reasoning-toggle__label-compact {
          font-size: 16px;
        }

        .anima-reasoning-toggle--compact .anima-reasoning-toggle__button {
          width: 44px;
          height: 24px;
        }

        .anima-reasoning-toggle--compact .anima-reasoning-toggle__thumb {
          width: 20px;
          height: 20px;
          font-size: 12px;
        }

        .anima-reasoning-toggle--compact .anima-reasoning-toggle__button--deep .anima-reasoning-toggle__thumb {
          transform: translateX(20px);
        }
      `}</style>
    </div>
  );
};

export default ReasoningModeToggle;
