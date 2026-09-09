/**
 * Synapse ANIMA Agent React SDK
 *
 * Emotionally intelligent chat components for React applications.
 *
 * @packageDocumentation
 */

// =============================================================================
// Main Components
// =============================================================================

export { AnimaChat } from './AnimaChat';
export { AnimaProvider, useAnima, useAnimaConnection, useAnimaMessages, useAnimaEmotions } from './AnimaProvider';

// =============================================================================
// Hooks
// =============================================================================

export { useAnimaChat } from './hooks/useAnimaChat';
export { useAnimaPreferences } from './hooks/useAnimaPreferences';
export { useAnimaMemory } from './hooks/useAnimaMemory';

// =============================================================================
// Stores
// =============================================================================

export {
  useChatStore,
  useMessages,
  useConnectionStatus,
  usePipelineStage,
  useIsLoading,
  useChatError,
  useCurrentReasoning,
  useIsReasoningStreaming,
} from './stores/chatStore';

export {
  useMemoryStore,
  useMemories,
  useBreakthroughs,
  useEmotionalTrajectory,
  useMemoryViewMode,
  useMemoryFilters,
  useFilteredMemories,
} from './stores/memoryStore';

export {
  usePreferencesStore,
  usePreferences,
  usePersonalitySettings,
  useContextSettings,
} from './stores/preferencesStore';

export {
  useChatModeStore,
  useChatMode,
  useConversationStyle,
  usePersonalityMode,
  useReasoningMode,
  useAllModes,
} from './stores/chatModeStore';

export {
  useEmotionAnalyticsStore,
  useEmotionTrends,
  useEmotionSummary,
  useEmotionAnalyticsLoading,
  useEmotionAnalyticsError,
  useDominantEmotion,
  useRecentEmotionTrend,
  useAverageWonderIndex,
} from './stores/emotionAnalyticsStore';

export {
  useBeliefStore,
  useBeliefs,
  useBeliefsByCategory,
  useConfirmedBeliefs,
  useBeliefViewMode,
  useBeliefLoading,
  useBeliefError,
  useBeliefCategoryStats,
} from './stores/beliefStore';

export {
  useGoalStore,
  useGoals,
  useGoalsByStatus,
  useGoalsByCategory,
  useGoalStatistics,
  useGoalViewMode,
  useGoalLoading,
  useGoalError,
  useActiveGoals,
  useCompletedGoals,
  useHighPriorityGoals,
} from './stores/goalStore';

export {
  useInterestStore,
  useInterests,
  useInterestLoading,
  useInterestError,
  useInterestStatistics,
  useInterestsByDomain,
  useTopInterests,
  type Interest,
  type InterestDomain,
  type ProficiencyLevel,
  type InterestStatistics,
} from './stores/interestStore';

// =============================================================================
// UI Components
// =============================================================================

// Chat
export { ChatMessages } from './components/ChatMessages';
export { MessageInput } from './components/MessageInput';
export { ThinkingIndicator } from './components/ThinkingIndicator';
export { ReasoningChain } from './components/ReasoningChain';
export type { ReasoningChainProps } from './components/ReasoningChain';

// Content Blocks
export {
  StructuredMessage,
  ParagraphRenderer,
  HeadingRenderer,
  ListRenderer,
  CodeBlockRenderer,
  QuoteRenderer,
  CalloutRenderer,
  TableRenderer,
} from './components/content-blocks';

// Memory
export {
  MemoryExplorer,
  MemoryTimeline,
  MemoryAnalytics,
} from './components/memory';

// Goals
export {
  GoalCard,
  MilestoneGrid,
  ObstaclesList,
  RecentGoals,
} from './components/goals';

// Mode Selectors
export {
  ChatModeSelector,
  ConversationStyleSelector,
  ReasoningModeToggle,
} from './components/modes';

// Emotion Components
export {
  EmotionalTrendChart,
} from './components/emotions';

// Beliefs Components
export {
  BeliefCard,
  BeliefStrengthMeter,
  BeliefStrengthCircle,
  BeliefCategoryGrid,
} from './components/beliefs';

// Interests Components
export {
  InterestCard,
  InterestList,
} from './components/interests';

// =============================================================================
// Utilities
// =============================================================================

export { preprocessReasoning, extractReasoningFromContent } from './utils/reasoning';

// =============================================================================
// Types
// =============================================================================

export type {
  // Message types
  MessageRole,
  Message,

  // Chat mode types
  ChatMode,
  ConversationStyle,
  PersonalityMode,
  ReasoningMode,
  ChatModeState,

  // Emotion types
  EmotionAnalysis,
  EmotionalContext,
  EmotionalTrajectoryPoint,
  EmotionTrendPoint,
  EmotionDistribution,
  EmotionSummary,
  EmotionAnalyticsState,

  // Goal types
  GoalStatus,
  GoalCategory,
  SubGoal,
  Milestone,
  Obstacle,
  Goal,

  // Belief types
  BeliefCategory,
  Belief,

  // Memory types
  MemoryType,
  MemoryScope,
  Memory,
  Breakthrough,

  // Chat types
  ChatResponse,
  ChatRequest,

  // Preference types
  CommunicationStyle,
  ResponseVerbosity,
  EnergyLevel,
  EmojiUsage,
  MemoryInclusion,
  GoalVisibility,
  BeliefInjection,
  EmotionalTracking,
  PersonalitySettings,
  ContextSettings,
  UserPreferences,

  // WebSocket types
  ConnectionStatus,
  PipelineStage,
  WebSocketMessage,

  // Component props
  AnimaChatProps,
  AnimaProviderProps,

  // Store types
  ChatState,
  MemoryState,
  PreferencesState,
} from './types';
