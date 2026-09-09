/**
 * Chat Mode Store - Manages chat modes, conversation styles, and reasoning modes
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  ChatMode,
  ConversationStyle,
  PersonalityMode,
  ReasoningMode,
  ChatModeState,
} from '../types';

interface ChatModeActions {
  // Mode setters
  setChatMode: (mode: ChatMode | null) => void;
  setConversationStyle: (style: ConversationStyle | null) => void;
  setPersonalityMode: (mode: PersonalityMode) => void;
  setReasoningMode: (mode: ReasoningMode) => void;

  // Bulk update
  setModes: (modes: Partial<ChatModeState>) => void;

  // Reset
  reset: () => void;
}

const initialState: ChatModeState = {
  chatMode: null,
  conversationStyle: null,
  personalityMode: 'balanced',
  reasoningMode: 'quick',
};

export const useChatModeStore = create<ChatModeState & ChatModeActions>()(
  persist(
    (set) => ({
      ...initialState,

      setChatMode: (mode) =>
        set({ chatMode: mode }),

      setConversationStyle: (style) =>
        set({ conversationStyle: style }),

      setPersonalityMode: (mode) =>
        set({ personalityMode: mode }),

      setReasoningMode: (mode) =>
        set({ reasoningMode: mode }),

      setModes: (modes) =>
        set((state) => ({ ...state, ...modes })),

      reset: () => set(initialState),
    }),
    {
      name: 'anima-chat-modes',
      partialize: (state) => ({
        // Persist user preferences
        personalityMode: state.personalityMode,
        reasoningMode: state.reasoningMode,
        // Don't persist session-specific modes
      }),
    }
  )
);

// Selector hooks for optimized re-renders
export const useChatMode = () => useChatModeStore((state) => state.chatMode);
export const useConversationStyle = () => useChatModeStore((state) => state.conversationStyle);
export const usePersonalityMode = () => useChatModeStore((state) => state.personalityMode);
export const useReasoningMode = () => useChatModeStore((state) => state.reasoningMode);

// Get all modes as an object (useful for API calls)
export const useAllModes = () =>
  useChatModeStore((state) => ({
    chatMode: state.chatMode,
    conversationStyle: state.conversationStyle,
    personalityMode: state.personalityMode,
    reasoningMode: state.reasoningMode,
  }));
