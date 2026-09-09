/**
 * Content Block Renderers
 *
 * Renders structured content from agent responses with proper formatting.
 */

import React from 'react';
import { clsx } from 'clsx';

// =============================================================================
// Types
// =============================================================================

export type ContentBlockType =
  | 'paragraph'
  | 'heading'
  | 'list'
  | 'code'
  | 'quote'
  | 'callout'
  | 'table';

export interface ContentBlock {
  type: ContentBlockType;
  content: string;
  metadata?: Record<string, unknown>;
}

interface BaseRendererProps {
  className?: string;
}

// =============================================================================
// Paragraph Renderer
// =============================================================================

interface ParagraphRendererProps extends BaseRendererProps {
  content: string;
}

export function ParagraphRenderer({ content, className }: ParagraphRendererProps) {
  return (
    <p className={clsx('anima-paragraph', className)}>
      {content}
    </p>
  );
}

// =============================================================================
// Heading Renderer
// =============================================================================

interface HeadingRendererProps extends BaseRendererProps {
  content: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

export function HeadingRenderer({ content, level = 2, className }: HeadingRendererProps) {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;

  return (
    <Tag className={clsx('anima-heading', `anima-heading-${level}`, className)}>
      {content}
    </Tag>
  );
}

// =============================================================================
// List Renderer
// =============================================================================

interface ListRendererProps extends BaseRendererProps {
  items: string[];
  ordered?: boolean;
}

export function ListRenderer({ items, ordered = false, className }: ListRendererProps) {
  const Tag = ordered ? 'ol' : 'ul';

  return (
    <Tag className={clsx('anima-list', ordered ? 'anima-list-ordered' : 'anima-list-unordered', className)}>
      {items.map((item, index) => (
        <li key={index} className="anima-list-item">
          {item}
        </li>
      ))}
    </Tag>
  );
}

// =============================================================================
// Code Block Renderer
// =============================================================================

interface CodeBlockRendererProps extends BaseRendererProps {
  content: string;
  language?: string;
  inline?: boolean;
}

export function CodeBlockRenderer({ content, language, inline = false, className }: CodeBlockRendererProps) {
  if (inline) {
    return (
      <code className={clsx('anima-code-inline', className)}>
        {content}
      </code>
    );
  }

  return (
    <pre className={clsx('anima-code-block', className)}>
      <code className={language ? `language-${language}` : undefined}>
        {content}
      </code>
    </pre>
  );
}

// =============================================================================
// Quote Renderer
// =============================================================================

interface QuoteRendererProps extends BaseRendererProps {
  content: string;
  author?: string;
}

export function QuoteRenderer({ content, author, className }: QuoteRendererProps) {
  return (
    <blockquote className={clsx('anima-quote', className)}>
      <p>{content}</p>
      {author && <cite className="anima-quote-author">— {author}</cite>}
    </blockquote>
  );
}

// =============================================================================
// Callout Renderer
// =============================================================================

type CalloutType = 'info' | 'warning' | 'success' | 'error' | 'insight';

interface CalloutRendererProps extends BaseRendererProps {
  content: string;
  type?: CalloutType;
  title?: string;
}

const calloutIcons: Record<CalloutType, string> = {
  info: 'ℹ️',
  warning: '⚠️',
  success: '✅',
  error: '❌',
  insight: '💡',
};

export function CalloutRenderer({ content, type = 'info', title, className }: CalloutRendererProps) {
  return (
    <div className={clsx('anima-callout', `anima-callout-${type}`, className)}>
      <div className="anima-callout-header">
        <span className="anima-callout-icon">{calloutIcons[type]}</span>
        {title && <span className="anima-callout-title">{title}</span>}
      </div>
      <div className="anima-callout-content">{content}</div>
    </div>
  );
}

// =============================================================================
// Table Renderer
// =============================================================================

interface TableRendererProps extends BaseRendererProps {
  headers: string[];
  rows: string[][];
}

export function TableRenderer({ headers, rows, className }: TableRendererProps) {
  return (
    <div className={clsx('anima-table-wrapper', className)}>
      <table className="anima-table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// Structured Message Renderer
// =============================================================================

interface StructuredMessageProps extends BaseRendererProps {
  content: string;
}

/**
 * Renders message content with automatic detection of structured elements.
 * Parses markdown-like syntax for headings, lists, code blocks, etc.
 */
export function StructuredMessage({ content, className }: StructuredMessageProps) {
  // Simple markdown parsing for common patterns
  const blocks = parseContentBlocks(content);

  return (
    <div className={clsx('anima-structured-message', className)}>
      {blocks.map((block, index) => {
        switch (block.type) {
          case 'heading':
            return (
              <HeadingRenderer
                key={index}
                content={block.content}
                level={(block.metadata?.level as 1 | 2 | 3 | 4 | 5 | 6) || 2}
              />
            );
          case 'list':
            return (
              <ListRenderer
                key={index}
                items={block.metadata?.items as string[] || [block.content]}
                ordered={block.metadata?.ordered as boolean}
              />
            );
          case 'code':
            return (
              <CodeBlockRenderer
                key={index}
                content={block.content}
                language={block.metadata?.language as string}
              />
            );
          case 'quote':
            return <QuoteRenderer key={index} content={block.content} />;
          case 'callout':
            return (
              <CalloutRenderer
                key={index}
                content={block.content}
                type={block.metadata?.calloutType as CalloutType}
                title={block.metadata?.title as string}
              />
            );
          case 'paragraph':
          default:
            return <ParagraphRenderer key={index} content={block.content} />;
        }
      })}
    </div>
  );
}

// =============================================================================
// Content Block Parser
// =============================================================================

function parseContentBlocks(content: string): ContentBlock[] {
  const blocks: ContentBlock[] = [];
  const lines = content.split('\n');
  let currentParagraph: string[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let codeLanguage = '';

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      blocks.push({
        type: 'paragraph',
        content: currentParagraph.join(' ').trim(),
      });
      currentParagraph = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block detection
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        blocks.push({
          type: 'code',
          content: codeBlockContent.join('\n'),
          metadata: { language: codeLanguage },
        });
        codeBlockContent = [];
        codeLanguage = '';
        inCodeBlock = false;
      } else {
        flushParagraph();
        inCodeBlock = true;
        codeLanguage = line.slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Heading detection
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      blocks.push({
        type: 'heading',
        content: headingMatch[2],
        metadata: { level: headingMatch[1].length },
      });
      continue;
    }

    // List detection
    const listMatch = line.match(/^(\s*)[-*]\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      // Collect consecutive list items
      const items: string[] = [listMatch[2]];
      while (i + 1 < lines.length) {
        const nextLine = lines[i + 1];
        const nextMatch = nextLine.match(/^(\s*)[-*]\s+(.+)$/);
        if (nextMatch) {
          items.push(nextMatch[2]);
          i++;
        } else {
          break;
        }
      }
      blocks.push({
        type: 'list',
        content: items.join(', '),
        metadata: { items, ordered: false },
      });
      continue;
    }

    // Quote detection
    if (line.startsWith('>')) {
      flushParagraph();
      const quoteContent = line.slice(1).trim();
      blocks.push({
        type: 'quote',
        content: quoteContent,
      });
      continue;
    }

    // Empty line = paragraph break
    if (line.trim() === '') {
      flushParagraph();
      continue;
    }

    // Regular text
    currentParagraph.push(line);
  }

  // Flush remaining paragraph
  flushParagraph();

  return blocks;
}
