/**
 * Agent: Bug Fix Quality
 * Reasoning loop: reads final code + manifest bugs → assesses fix quality
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { parseFinalCode } from '../tools';

const SYSTEM_PROMPT = `You are a senior engineer assessing how well a candidate fixed intentional bugs in a codebase.

Your job is to reason about:
- Which bugs appear to have been fixed correctly
- Which bugs were partially fixed or introduced new issues
- Which bugs were missed entirely
- Whether fixes are clean or just workarounds
- Whether the candidate introduced any new bugs in the process

Be specific about what you observe in the code.
Return a JSON object with: score (0-100), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runBugFixAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const files = parseFinalCode(data.finalCode);

  // Extract manifest bugs from the assessment template if available
  const template = data.assessment?.template as any;
  const intentionalBugs =
    template?.templateSpec?.intentionalIssues ||
    template?.intentionalIssues ||
    [];

  const bugList =
    intentionalBugs.length > 0
      ? intentionalBugs
          .map((b: any) => `- [${b.id}] ${b.description}`)
          .join('\n')
      : 'No manifest available — infer bugs from code patterns';

  const codeSample = Object.entries(files)
    .slice(0, 5)
    .map(([name, code]) => `=== ${name} ===\n${code.split('\n').slice(0, 150).join('\n')}`)
    .join('\n\n');

  const userPrompt = `
Role: ${data.assessment?.role ?? 'Software Engineer'} (${data.assessment?.level ?? 'unknown'} level)

Intentional bugs that were planted in the assessment:
${bugList}

Candidate's final code:
${codeSample || 'No code submitted'}

Analyze which bugs were fixed, which were missed, and how well the fixes were done.
If no manifest is available, look for common bug fix patterns (null checks, error handling, race conditions, etc.).
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
    agentName: 'Bug Fix Quality',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? intentionalBugs.length > 0 ? 0.8 : 0.4)),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: [
      { key: 'bugsInManifest', value: intentionalBugs.length, label: 'Bugs in manifest' },
      ...(raw.signals ?? []),
    ],
    rawNotes: raw.rawNotes,
  };
}
