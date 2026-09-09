/**
 * React Components for Synapse ANIMA Agent
 * (showcase excerpt: chat UI + mode selectors only — see README)
 */

// Chat components
export { ChatMessages } from './ChatMessages';
export { MessageInput } from './MessageInput';
export { ThinkingIndicator } from './ThinkingIndicator';

// Content block renderers
export {
  StructuredMessage,
  ParagraphRenderer,
  HeadingRenderer,
  ListRenderer,
  CodeBlockRenderer,
  QuoteRenderer,
  CalloutRenderer,
  TableRenderer,
} from './content-blocks';

// Mode selector components
export { ChatModeSelector, ConversationStyleSelector, ReasoningModeToggle } from './modes';
