/**
 * Agent: Communication & Docs
 * Reasoning loop: reads comments, docs files → assesses communication quality
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { parseFinalCode, analyzeCodeMetrics } from '../tools';

const SYSTEM_PROMPT = `You are a technical communication specialist assessing how well a candidate documents and communicates their work.

Your job is to reason about:
- Quality and clarity of code comments
- Presence and quality of any written documentation (README, design docs, runbooks)
- Whether comments explain WHY not just WHAT
- Naming conventions that aid readability
- Any written explanations in chat or docs component responses

Good communication is a strong signal of a collaborative, senior-minded engineer.
Return a JSON object with: score (0-100), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runCommDocsAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const files = parseFinalCode(data.finalCode);
  const metrics = analyzeCodeMetrics(files);

  // Extract doc files specifically
  const docFiles = Object.entries(files)
    .filter(([name]) =>
      name.endsWith('.md') ||
      name.endsWith('.txt') ||
      name.toLowerCase().includes('readme') ||
      name.toLowerCase().includes('doc')
    )
    .map(([name, content]) => `=== ${name} ===\n${content.slice(0, 500)}`)
    .join('\n\n');

  // Extract inline comments from code
  const inlineComments = Object.entries(files)
    .slice(0, 3)
    .map(([name, code]) => {
      const commentLines = code
        .split('\n')
        .filter((l) => l.trim().startsWith('//') || l.trim().startsWith('#'))
        .slice(0, 10)
        .join('\n');
      return commentLines ? `=== ${name} comments ===\n${commentLines}` : '';
    })
    .filter(Boolean)
    .join('\n\n');

  const userPrompt = `
Role: ${data.assessment?.role ?? 'unknown'} (${data.assessment?.level ?? 'unknown'} level)

Code metrics:
- Comment ratio: ${(metrics.commentRatio * 100).toFixed(1)}%
- Total comment lines: ${metrics.commentLines}
- Total files: ${metrics.totalFiles}

Documentation files found:
${docFiles || 'None'}

Inline comment samples:
${inlineComments || 'No inline comments found'}

Assess the quality of communication and documentation.
Consider the role level — a senior engineer should have better docs habits than a junior.
Return your finding as JSON.`;

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.3,
  });

  const raw = JSON.parse(response.choices[0].message.content ?? '{}');

  return {
    agentName: 'Comm & Docs',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? 0.6)),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: [
      { key: 'commentRatio', value: `${(metrics.commentRatio * 100).toFixed(1)}%`, label: 'Comment ratio' },
      { key: 'hasDocFiles', value: docFiles.length > 0, label: 'Has doc files' },
      ...(raw.signals ?? []),
    ],
    rawNotes: raw.rawNotes,
  };
}
