/**
 * Synapse ANIMA Agent React SDK - Type Definitions
 *
 * These types mirror the Python SDK types for full compatibility.
 */

// =============================================================================
// Message Types
// =============================================================================

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  emotions?: EmotionAnalysis;
  isStreaming?: boolean;
  reasoning?: string;
  llmUsage?: {
    reasoning_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  contextMetadata?: {
    active_goals?: unknown[];
    beliefs?: unknown[];
    memories?: unknown[];
    emotional_state?: unknown;
    reasoning_chain?: string | null;
  };
}

// =============================================================================
// Emotion Types
// =============================================================================

export interface EmotionAnalysis {
  category: string;
  intensity: number;
  raw: Record<string, number>;
  complexity?: 'simple' | 'moderate' | 'complex';
  wonderIndex?: number;
}

export interface EmotionalContext {
  love: number;
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  surprise: number;
  trust: number;
  anticipation: number;
  dominant: string;
  intensity: number;
  complexity: 'simple' | 'moderate' | 'complex';
  wonderIndex: number;
}

export interface EmotionalTrajectoryPoint {
  emotion: string;
  intensity: number;
  complexity: number;
  timestamp: Date;
  wonderIndex: number;
  discoveryLevel: 'routine' | 'unusual' | 'breakthrough';
}

// =============================================================================
// Goal Types
// =============================================================================

export type GoalStatus = 'not_started' | 'in_progress' | 'completed' | 'on_hold';
export type GoalCategory = 'health' | 'career' | 'learning' | 'relationships' | 'finance' | 'personal' | 'creative' | 'other';

export interface SubGoal {
  id: string;
  title: string;
  status: GoalStatus;
  progress: number;
}

export interface Milestone {
  id: string;
  title: string;
  description?: string;
  targetDate?: Date;
  completedDate?: Date;
  isCompleted: boolean;
}

export interface Obstacle {
  id: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  mitigation?: string;
  isResolved: boolean;
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  category: GoalCategory;
  priority: 1 | 2 | 3 | 4 | 5;
  status: GoalStatus;
  progress: number;
  deadline?: Date;
  wonderIndex: number;
  emotionalIntensity: number;
  subGoals: SubGoal[];
  milestones: Milestone[];
  obstacles: Obstacle[];
  relatedMemories: string[];
  createdAt: Date;
  updatedAt: Date;
}

// =============================================================================
// Belief Types
// =============================================================================

export type BeliefCategory =
  | 'values'
  | 'identity'
  | 'relationships'
  | 'work'
  | 'growth'
  | 'purpose'
  | 'ethics'
  | 'world_view';

export interface Belief {
  id: string;
  statement: string;
  category: BeliefCategory;
  strength: number; // 0.0 - 1.0
  establishedDate: Date;
  userConfirmed: boolean;
  linkedGoals: string[];
  supportingMemories: string[];
}

// =============================================================================
// Memory Types
// =============================================================================

export type MemoryType = 'goal' | 'breakthrough' | 'emotional_pattern' | 'identity' | 'belief' | 'insight' | 'interest';
export type MemoryScope = 'core' | 'chat' | 'transient';

export interface Memory {
  id: string;
  content: string;
  type: MemoryType;
  scope: MemoryScope;
  timestamp: Date;
  wonderIndex: number;
  emotionalSignature?: EmotionAnalysis;
  relatedMemories: string[];
  metadata?: Record<string, unknown>;
}

export interface Breakthrough {
  id: string;
  type: string;
  significance: number;
  timestamp: Date;
  description: string;
  relatedGoals: string[];
}

// =============================================================================
// Chat Response Types
// =============================================================================

export interface ChatResponse {
  content: string;
  emotions: EmotionAnalysis;
  reasoning?: string;
  goalsDetected: Goal[];
  beliefsDetected: Belief[];
  wonderIndex: number;
  breakthroughDetected: boolean;
  crisisDetected: boolean;
  metadata: Record<string, unknown>;
  contextMetadata?: {
    active_goals?: unknown[];
    beliefs?: unknown[];
    memories?: unknown[];
    emotional_state?: unknown;
    reasoning_chain?: string | null;
  };
  llmUsage?: {
    reasoning_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

// =============================================================================
// Preferences Types
// =============================================================================

export type CommunicationStyle = 'formal' | 'casual' | 'technical' | 'supportive';
export type ResponseVerbosity = 'concise' | 'balanced' | 'detailed' | 'comprehensive';
export type EnergyLevel = 'low' | 'medium' | 'high';
export type EmojiUsage = 'never' | 'minimal' | 'moderate' | 'frequent';

export interface PersonalitySettings {
  communicationStyle: CommunicationStyle;
  responseVerbosity: ResponseVerbosity;
  energyLevel: EnergyLevel;
  emojiUsage: EmojiUsage;
}

export type MemoryInclusion = 'minimal' | 'relevant' | 'comprehensive';
export type GoalVisibility = 'hide' | 'summary' | 'detailed';
export type BeliefInjection = 'disabled' | 'light' | 'full';
export type EmotionalTracking = 'disabled' | 'subtle' | 'explicit';

export interface ContextSettings {
  memoryInclusion: MemoryInclusion;
  goalVisibility: GoalVisibility;
  beliefInjection: BeliefInjection;
  emotionalTracking: EmotionalTracking;
}

export interface UserPreferences {
  personality: PersonalitySettings;
  context: ContextSettings;
}

// =============================================================================
// Chat Mode Types
// =============================================================================

/** Chat modes that determine the focus of the conversation */
export type ChatMode = 'ask_advice' | 'set_goals' | 'explore';

/** Conversation styles that affect the tone and approach */
export type ConversationStyle = 'balanced' | 'therapeutic' | 'crisis' | 'coaching' | 'casual' | 'analytical';

/** Personality modes for the agent */
export type PersonalityMode = 'balanced' | 'analytical' | 'creative' | 'supportive';

/** Reasoning modes - quick for fast responses, deep for thorough analysis */
export type ReasoningMode = 'quick' | 'deep';

export interface ChatModeState {
  chatMode: ChatMode | null;
  conversationStyle: ConversationStyle | null;
  personalityMode: PersonalityMode;
  reasoningMode: ReasoningMode;
}

// =============================================================================
// Emotion Analytics Types
// =============================================================================

export interface EmotionTrendPoint {
  emotion: string;
  intensity: number;
  complexity: number;
  timestamp: Date;
  wonderIndex: number;
  discoveryLevel: 'routine' | 'unusual' | 'breakthrough';
}

export interface EmotionDistribution {
  [emotion: string]: {
    count: number;
    percentage: number;
  };
}

export interface EmotionSummary {
  totalInteractions: number;
  dominantEmotion: string;
  averageIntensity: number;
  averageWonderIndex: number;
  emotionDistribution: EmotionDistribution;
  recentTrend: 'increasing' | 'decreasing' | 'stable';
}

export interface EmotionAnalyticsState {
  trends: EmotionTrendPoint[];
  summary: EmotionSummary | null;
  isLoading: boolean;
  error: string | null;
}

// =============================================================================
// WebSocket Types
// =============================================================================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export type PipelineStage =
  | 'idle'
  | 'analyzing_emotions'
  | 'building_context'
  | 'reviewing_goals'
  | 'connecting_beliefs'
  | 'reasoning'
  | 'generating_response'
  | 'enriching';

export interface WebSocketMessage {
  type: 'chat' | 'status' | 'error' | 'stream_start' | 'stream_chunk' | 'stream_end' | 'reasoning_stream';
  payload: unknown;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  userId: string;
  sessionId?: string;
  chatMode?: ChatMode;
  conversationStyle?: ConversationStyle;
  personalityMode?: PersonalityMode;
  reasoningMode?: ReasoningMode;
}

// =============================================================================
// Component Props Types
// =============================================================================

export interface AnimaChatProps {
  /** WebSocket endpoint URL */
  endpoint: string;
  /** User identifier */
  userId: string;
  /** Optional session identifier */
  sessionId?: string;
  /** Custom class name */
  className?: string;
  /** Theme variant */
  theme?: 'light' | 'dark' | 'system';
  /** Initial messages to display */
  initialMessages?: Message[];
  /** Callback when a message is sent */
  onMessageSent?: (message: Message) => void;
  /** Callback when a response is received */
  onResponseReceived?: (response: ChatResponse) => void;
  /** Callback on connection status change */
  onConnectionChange?: (status: ConnectionStatus) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Show memory explorer button */
  showMemoryExplorer?: boolean;
  /** Show goals panel */
  showGoals?: boolean;
  /** Show settings panel */
  showSettings?: boolean;
  /** Custom placeholder text */
  placeholder?: string;
  /** Disable input */
  disabled?: boolean;
}

export interface AnimaProviderProps {
  /** WebSocket endpoint URL */
  endpoint: string;
  /** User identifier */
  userId: string;
  /** Optional session identifier */
  sessionId?: string;
  /** Children components */
  children: React.ReactNode;
}

// =============================================================================
// Store Types
// =============================================================================

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  connectionStatus: ConnectionStatus;
  pipelineStage: PipelineStage;
  error: string | null;
  currentReasoning: string | null;
  isReasoningStreaming: boolean;
}

export interface MemoryState {
  memories: Memory[];
  breakthroughs: Breakthrough[];
  emotionalTrajectory: EmotionalTrajectoryPoint[];
  isLoading: boolean;
  viewMode: 'timeline' | 'graph' | 'analytics';
  filters: {
    type?: MemoryType;
    scope?: MemoryScope;
    dateRange?: [Date, Date];
  };
}

export interface PreferencesState {
  preferences: UserPreferences;
  isLoading: boolean;
}
