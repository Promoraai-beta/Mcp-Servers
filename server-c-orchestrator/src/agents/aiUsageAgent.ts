/**
 * Agent: AI Usage
 * Reasoning loop: reads AI interaction log → detects patterns → assesses integrity risk
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { summarizeAiInteractions } from '../tools';

const SYSTEM_PROMPT = `You are an integrity analyst specializing in detecting AI-assisted cheating patterns in technical assessments.

Your job is to reason about:
- How frequently the candidate used AI assistance
- Whether pastes followed AI responses (suggests blind copy-paste)
- Tab switching patterns (suggests external resource use)
- Whether apply/copy events suggest the candidate understood AI suggestions or just pasted them
- Legitimate vs suspicious AI usage patterns

Be fair — some AI usage is acceptable and expected. The key signal is blind paste vs thoughtful adaptation.
Return a JSON object with: score (0-100, higher = more authentic), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runAiUsageAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const aiSummary = summarizeAiInteractions(data);

  // Include recent AI prompts/responses as evidence (truncated)
  const recentInteractions = data.aiInteractions
    .slice(-10)
    .map((i) => `[${i.eventType}] ${i.prompt?.slice(0, 100) ?? ''} ${i.response?.slice(0, 100) ?? ''}`)
    .join('\n');

  const userPrompt = `
AI Interaction Summary:
- Total interactions: ${aiSummary.totalInteractions}
- Prompts sent: ${aiSummary.promptsSent}
- Responses received: ${aiSummary.responsesReceived}
- Copy events: ${aiSummary.copies}
- Apply events: ${aiSummary.applies}
- Total paste events: ${aiSummary.totalPastes}
- Suspicious pastes (within 30s of AI response): ${aiSummary.suspiciousPastes}
- Tab switches: ${aiSummary.tabSwitches}
- AI usage intensity: ${aiSummary.aiUsageIntensity}

Recent interactions (last 10):
${recentInteractions || 'None'}

Reason step by step. Is this pattern indicative of authentic work, heavy AI reliance, or something in between?
Consider that some AI use is fine — the question is whether the candidate understood what they applied.
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
    agentName: 'AI Usage',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? 0.5)),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: [
      { key: 'promptsSent', value: aiSummary.promptsSent, label: 'AI prompts sent' },
      { key: 'suspiciousPastes', value: aiSummary.suspiciousPastes, label: 'Suspicious pastes' },
      { key: 'tabSwitches', value: aiSummary.tabSwitches, label: 'Tab switches' },
      ...(raw.signals ?? []),
    ],
    rawNotes: raw.rawNotes,
  };
}
