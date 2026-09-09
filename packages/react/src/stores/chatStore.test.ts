/**
 * Tests for ChatStore - Zustand store for chat state management
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatStore';
import type { Message, ChatResponse } from '../types';

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset the store before each test
    useChatStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have empty messages array', () => {
      const { messages } = useChatStore.getState();
      expect(messages).toEqual([]);
    });

    it('should have disconnected connection status', () => {
      const { connectionStatus } = useChatStore.getState();
      expect(connectionStatus).toBe('disconnected');
    });

    it('should have idle pipeline stage', () => {
      const { pipelineStage } = useChatStore.getState();
      expect(pipelineStage).toBe('idle');
    });

    it('should not be loading', () => {
      const { isLoading } = useChatStore.getState();
      expect(isLoading).toBe(false);
    });

    it('should have no error', () => {
      const { error } = useChatStore.getState();
      expect(error).toBeNull();
    });
  });

  describe('Message Management', () => {
    it('should add a message', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      useChatStore.getState().addMessage(message);

      const { messages } = useChatStore.getState();
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('Hello');
    });

    it('should add multiple messages', () => {
      const messages: Message[] = [
        { id: 'msg-1', role: 'user', content: 'Hello', timestamp: new Date() },
        { id: 'msg-2', role: 'assistant', content: 'Hi there!', timestamp: new Date() },
      ];

      messages.forEach((msg) => useChatStore.getState().addMessage(msg));

      const { messages: storeMessages } = useChatStore.getState();
      expect(storeMessages).toHaveLength(2);
    });

    it('should update a message', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().updateMessage('msg-1', { content: 'Updated Hello' });

      const { messages } = useChatStore.getState();
      expect(messages[0].content).toBe('Updated Hello');
    });

    it('should not update non-existent message', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().updateMessage('msg-2', { content: 'Updated' });

      const { messages } = useChatStore.getState();
      expect(messages[0].content).toBe('Hello');
    });

    it('should append to a message', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'assistant',
        content: 'Hello',
        timestamp: new Date(),
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().appendToMessage('msg-1', ' World');

      const { messages } = useChatStore.getState();
      expect(messages[0].content).toBe('Hello World');
    });

    it('should clear all messages', () => {
      const messages: Message[] = [
        { id: 'msg-1', role: 'user', content: 'Hello', timestamp: new Date() },
        { id: 'msg-2', role: 'assistant', content: 'Hi there!', timestamp: new Date() },
      ];

      messages.forEach((msg) => useChatStore.getState().addMessage(msg));
      useChatStore.getState().clearMessages();

      const { messages: storeMessages } = useChatStore.getState();
      expect(storeMessages).toHaveLength(0);
    });
  });

  describe('Connection State', () => {
    it('should update connection status', () => {
      useChatStore.getState().setConnectionStatus('connecting');
      expect(useChatStore.getState().connectionStatus).toBe('connecting');

      useChatStore.getState().setConnectionStatus('connected');
      expect(useChatStore.getState().connectionStatus).toBe('connected');
    });

    it('should update pipeline stage', () => {
      useChatStore.getState().setPipelineStage('analyzing');
      expect(useChatStore.getState().pipelineStage).toBe('analyzing');

      useChatStore.getState().setPipelineStage('generating');
      expect(useChatStore.getState().pipelineStage).toBe('generating');
    });

    it('should update loading state', () => {
      useChatStore.getState().setLoading(true);
      expect(useChatStore.getState().isLoading).toBe(true);

      useChatStore.getState().setLoading(false);
      expect(useChatStore.getState().isLoading).toBe(false);
    });

    it('should update error state', () => {
      useChatStore.getState().setError('Connection failed');
      expect(useChatStore.getState().error).toBe('Connection failed');

      useChatStore.getState().setError(null);
      expect(useChatStore.getState().error).toBeNull();
    });
  });

  describe('Streaming Support', () => {
    it('should start streaming for a message', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: false,
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().startStreaming('msg-1');

      const { messages } = useChatStore.getState();
      expect(messages[0].isStreaming).toBe(true);
    });

    it('should end streaming with final content', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'assistant',
        content: 'Partial',
        timestamp: new Date(),
        isStreaming: true,
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().endStreaming('msg-1', 'Final content');

      const { messages, pipelineStage, isLoading } = useChatStore.getState();
      expect(messages[0].content).toBe('Final content');
      expect(messages[0].isStreaming).toBe(false);
      expect(pipelineStage).toBe('idle');
      expect(isLoading).toBe(false);
    });

    it('should end streaming with response data', () => {
      const message: Message = {
        id: 'msg-1',
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      const response: ChatResponse = {
        content: 'Final content',
        emotions: { dominant: 'joy', intensity: 0.8 },
        goalsDetected: [{ title: 'Learn TypeScript' }],
        beliefsDetected: [],
        wonderIndex: 0.7,
        breakthroughDetected: true,
      };

      useChatStore.getState().addMessage(message);
      useChatStore.getState().endStreaming('msg-1', response.content, response);

      const { messages } = useChatStore.getState();
      expect(messages[0].emotions).toEqual(response.emotions);
      expect(messages[0].metadata?.wonderIndex).toBe(0.7);
      expect(messages[0].metadata?.breakthroughDetected).toBe(true);
    });
  });

  describe('Reset', () => {
    it('should reset to initial state', () => {
      // Modify state
      useChatStore.getState().addMessage({
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      });
      useChatStore.getState().setConnectionStatus('connected');
      useChatStore.getState().setLoading(true);
      useChatStore.getState().setError('Some error');

      // Reset
      useChatStore.getState().reset();

      // Verify initial state
      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
      expect(state.connectionStatus).toBe('disconnected');
      expect(state.pipelineStage).toBe('idle');
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });
});
