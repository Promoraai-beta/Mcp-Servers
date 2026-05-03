/**
 * Agent: Code Quality
 * Reasoning loop: reads code → runs metrics → reasons about quality → finding
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { parseFinalCode, analyzeCodeMetrics } from '../tools';

const SYSTEM_PROMPT = `You are a senior code reviewer specializing in assessing candidate code quality.
You will be given code metrics and file contents from a technical assessment.

Your job is to reason about:
- Code structure and organization
- Naming conventions and readability
- Error handling presence
- Test coverage
- Comment quality and documentation
- Overall engineering discipline

Be honest and specific. Reference actual filenames and patterns you observe.
Return a JSON object with: score (0-100), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runCodeQualityAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const files = parseFinalCode(data.finalCode);
  const metrics = analyzeCodeMetrics(files);

  // Build a concise code sample (first 200 lines of each file, capped)
  const codeSample = Object.entries(files)
    .slice(0, 5)
    .map(([name, code]) => `=== ${name} ===\n${code.split('\n').slice(0, 200).join('\n')}`)
    .join('\n\n');

  const userPrompt = `
Assessment: ${data.assessment?.jobTitle ?? 'Technical Assessment'} (${data.assessment?.level ?? 'unknown'} level)
Role: ${data.assessment?.role ?? 'unknown'}

Code Metrics:
- Total files: ${metrics.totalFiles}
- Total lines: ${metrics.totalLines}
- Comment ratio: ${(metrics.commentRatio * 100).toFixed(1)}%
- Has tests: ${metrics.hasTests}
- Has error handling: ${metrics.hasErrorHandling}

Code submitted:
${codeSample || 'No code submitted'}

Reason step by step through the code quality. Consider the role and level when calibrating your score.
Then return your finding as JSON.`;

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
    agentName: 'Code Quality',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? 0.5)),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: raw.signals ?? [],
    rawNotes: raw.rawNotes,
  };
}
