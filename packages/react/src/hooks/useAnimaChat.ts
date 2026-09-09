/**
 * useAnimaChat - WebSocket chat hook with streaming support
 *
 * Manages WebSocket connection to ANIMA backend, handles message streaming,
 * pipeline status updates, and reconnection logic.
 */

import { useCallback, useEffect, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';
import { useMemoryStore } from '../stores/memoryStore';
import type {
  Message,
  ChatRequest,
  ChatResponse,
  ConnectionStatus,
  PipelineStage,
  WebSocketMessage,
} from '../types';

interface UseAnimaChatOptions {
  /** WebSocket endpoint URL */
  endpoint: string;
  /** User identifier */
  userId: string;
  /** Optional session identifier */
  sessionId?: string;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Reconnect attempts */
  maxReconnectAttempts?: number;
  /** Reconnect interval in ms */
  reconnectInterval?: number;
  /** Callback when connected */
  onConnect?: () => void;
  /** Callback when disconnected */
  onDisconnect?: () => void;
  /** Callback on message received */
  onMessage?: (response: ChatResponse) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

interface UseAnimaChatReturn {
  /** Send a message */
  sendMessage: (content: string, options?: Partial<ChatRequest>) => Promise<void>;
  /** Connect to WebSocket */
  connect: () => void;
  /** Disconnect from WebSocket */
  disconnect: () => void;
  /** Current connection status */
  connectionStatus: ConnectionStatus;
  /** Current pipeline processing stage */
  pipelineStage: PipelineStage;
  /** Whether a message is being processed */
  isLoading: boolean;
  /** All messages */
  messages: Message[];
  /** Current error if any */
  error: string | null;
  /** Clear all messages */
  clearMessages: () => void;
  /** Current reasoning text being streamed */
  currentReasoning: string | null;
  /** Whether reasoning is actively streaming */
  isReasoningStreaming: boolean;
}

export function useAnimaChat(options: UseAnimaChatOptions): UseAnimaChatReturn {
  const {
    endpoint,
    userId,
    sessionId,
    autoConnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);
  const isConnectingRef = useRef(false);
  const isMountedRef = useRef(false);

  // Store actions
  const {
    messages,
    connectionStatus,
    pipelineStage,
    isLoading,
    error,
    currentReasoning,
    isReasoningStreaming,
    addMessage,
    appendToMessage,
    startStreaming,
    endStreaming,
    setConnectionStatus,
    setPipelineStage,
    setLoading,
    setError,
    clearMessages,
    setCurrentReasoning,
    setIsReasoningStreaming,
  } = useChatStore();

  const { addTrajectoryPoint, addBreakthrough } = useMemoryStore();

  // Generate unique message ID
  const generateMessageId = useCallback(() => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'status': {
            const status = data.payload as { stage: PipelineStage; message: string };
            setPipelineStage(status.stage);
            break;
          }

          case 'reasoning_stream': {
            const reasoningPayload = data.payload as { reasoning: string };
            setCurrentReasoning(reasoningPayload.reasoning);
            setIsReasoningStreaming(true);
            setPipelineStage('reasoning');
            break;
          }

          case 'stream_start': {
            const messageId = generateMessageId();
            currentMessageIdRef.current = messageId;

            setIsReasoningStreaming(false);

            addMessage({
              id: messageId,
              role: 'assistant',
              content: '',
              timestamp: new Date(),
              isStreaming: true,
            });
            startStreaming(messageId);
            break;
          }

          case 'stream_chunk': {
            const chunk = data.payload as { content: string };
            if (currentMessageIdRef.current) {
              appendToMessage(currentMessageIdRef.current, chunk.content);
            }
            break;
          }

          case 'stream_end': {
            const response = data.payload as ChatResponse;
            // Capture reasoning from payload if not already set via reasoning_stream
            if (response.reasoning && !currentReasoning) {
              setCurrentReasoning(response.reasoning);
            }
            if (currentMessageIdRef.current) {
              endStreaming(currentMessageIdRef.current, response.content, response);

              // Update memory store with emotional data
              if (response.emotions) {
                addTrajectoryPoint({
                  emotion: response.emotions.category,
                  intensity: response.emotions.intensity,
                  complexity: response.emotions.complexity === 'complex' ? 1 : 0.5,
                  timestamp: new Date(),
                  wonderIndex: response.wonderIndex,
                  discoveryLevel: response.breakthroughDetected ? 'breakthrough' : 'routine',
                });
              }

              // Record breakthrough if detected
              if (response.breakthroughDetected) {
                addBreakthrough({
                  id: `br-${Date.now()}`,
                  type: 'emotional_shift',
                  significance: response.wonderIndex,
                  timestamp: new Date(),
                  description: 'Breakthrough moment detected in conversation',
                  relatedGoals: response.goalsDetected?.map((g) => g.id) || [],
                });
              }

              onMessage?.(response);
            }
            currentMessageIdRef.current = null;
            setLoading(false);
            break;
          }

          case 'chat': {
            // Non-streaming response (fallback)
            const response = data.payload as ChatResponse;
            const messageId = generateMessageId();

            addMessage({
              id: messageId,
              role: 'assistant',
              content: response.content,
              timestamp: new Date(),
              emotions: response.emotions,
              metadata: {
                goalsDetected: response.goalsDetected,
                beliefsDetected: response.beliefsDetected,
                wonderIndex: response.wonderIndex,
              },
            });

            onMessage?.(response);
            setLoading(false);
            setPipelineStage('idle');
            break;
          }

          case 'error': {
            const errorPayload = data.payload as { message: string; code?: string };
            setError(errorPayload.message);
            setLoading(false);
            setPipelineStage('idle');
            onError?.(new Error(errorPayload.message));
            break;
          }
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setError('Failed to parse server response');
      }
    },
    [
      addMessage,
      appendToMessage,
      startStreaming,
      endStreaming,
      setPipelineStage,
      setLoading,
      setError,
      setCurrentReasoning,
      setIsReasoningStreaming,
      currentReasoning,
      addTrajectoryPoint,
      addBreakthrough,
      generateMessageId,
      onMessage,
      onError,
    ]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Prevent duplicate connection attempts
    if (isConnectingRef.current) {
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    isConnectingRef.current = true;
    setConnectionStatus('connecting');

    try {
      const wsUrl = new URL(endpoint);
      wsUrl.searchParams.set('userId', userId);
      if (sessionId) {
        wsUrl.searchParams.set('sessionId', sessionId);
      }

      const ws = new WebSocket(wsUrl.toString());

      ws.onopen = () => {
        isConnectingRef.current = false;
        if (!isMountedRef.current) {
          ws.close(1000, 'Component unmounted');
          return;
        }
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        setError(null);
        onConnect?.();
      };

      ws.onmessage = handleWebSocketMessage;

      ws.onclose = (event) => {
        isConnectingRef.current = false;
        if (!isMountedRef.current) return;

        setConnectionStatus('disconnected');
        onDisconnect?.();

        // Attempt reconnection if not a clean close and component is still mounted
        if (!event.wasClean && isMountedRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          setConnectionStatus('reconnecting');
          reconnectAttemptsRef.current += 1;

          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connect();
            }
          }, reconnectInterval * reconnectAttemptsRef.current);
        }
      };

      ws.onerror = () => {
        isConnectingRef.current = false;
        if (!isMountedRef.current) return;

        setConnectionStatus('error');
        setError('WebSocket connection error');
        onError?.(new Error('WebSocket connection error'));
      };

      wsRef.current = ws;
    } catch (err) {
      isConnectingRef.current = false;
      setConnectionStatus('error');
      setError('Failed to create WebSocket connection');
      onError?.(err as Error);
    }
  }, [
    endpoint,
    userId,
    sessionId,
    maxReconnectAttempts,
    reconnectInterval,
    handleWebSocketMessage,
    setConnectionStatus,
    setError,
    onConnect,
    onDisconnect,
    onError,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isConnectingRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
  }, [setConnectionStatus]);

  // Send a message
  const sendMessage = useCallback(
    async (content: string, options: Partial<ChatRequest> = {}) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('Not connected to server');
        throw new Error('Not connected to server');
      }

      // Add user message to store
      const userMessageId = generateMessageId();
      addMessage({
        id: userMessageId,
        role: 'user',
        content,
        timestamp: new Date(),
      });

      // Set loading state
      setLoading(true);
      setError(null);
      setPipelineStage('analyzing_emotions');

      // Send to server
      const request: ChatRequest = {
        message: content,
        userId,
        sessionId,
        personalityMode: options.personalityMode,
        reasoningMode: options.reasoningMode || 'quick',
      };

      wsRef.current.send(JSON.stringify({
        type: 'chat',
        payload: request,
      }));
    },
    [userId, sessionId, addMessage, setLoading, setError, setPipelineStage, generateMessageId]
  );

  // Auto-connect on mount - use separate effect for lifecycle tracking
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      disconnect();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount/unmount

  // Connect effect - separate to avoid reconnecting on callback changes
  useEffect(() => {
    if (autoConnect && isMountedRef.current) {
      // Small delay to handle React StrictMode double-mount
      const timer = setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, 50);
      return () => clearTimeout(timer);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect, endpoint, userId, sessionId]); // Only reconnect on these changes

  return {
    sendMessage,
    connect,
    disconnect,
    connectionStatus,
    pipelineStage,
    isLoading,
    messages,
    error,
    clearMessages,
    currentReasoning,
    isReasoningStreaming,
  };
}
