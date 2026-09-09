/**
 * Reasoning text preprocessing utilities.
 *
 * Handles formatting of reasoning/thinking text from the LLM,
 * including stripping <think> tags and formatting step markers.
 */

/**
 * Preprocess reasoning text for display.
 * Strips <think> tags and bolds step/phase markers.
 */
export function preprocessReasoning(text: string): string {
  if (!text) return '';

  let processed = text;

  // Strip <think> tags if present
  processed = processed.replace(/<think>/gi, '');
  processed = processed.replace(/<\/think>/gi, '');

  // Bold step/phase/stage markers: "Step 1:" → "**Step 1:**"
  processed = processed.replace(
    /^((?:Step|Phase|Stage)\s+\d+)\s*:/gim,
    '**$1:**'
  );

  // Bold section headers from structured reasoning
  processed = processed.replace(
    /^(SYNAPSE|NEXUS|CORE|Response Strategy)\s*[-–—]?\s*/gim,
    '**$1** — '
  );

  // Bold numbered list headers: "1. UNDERSTANDING" → "**1. UNDERSTANDING**"
  processed = processed.replace(
    /^(\d+)\.\s+(UNDERSTANDING|EMOTIONAL ALIGNMENT|CONTEXTUAL CONNECTIONS|RESPONSE APPROACH|DELIVERY STRATEGY)/gim,
    '**$1. $2**'
  );

  return processed.trim();
}

/**
 * Extract reasoning from content that may contain <think> tags.
 * Falls back to this if the LLM puts reasoning in the content field
 * instead of the dedicated reasoning field.
 *
 * @returns Object with separated content and reasoning
 */
export function extractReasoningFromContent(content: string): {
  content: string;
  reasoning: string | null;
} {
  if (!content) return { content: '', reasoning: null };

  const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/i);

  if (thinkMatch) {
    const reasoning = thinkMatch[1].trim();
    const cleanContent = content.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    return { content: cleanContent, reasoning };
  }

  return { content, reasoning: null };
}
