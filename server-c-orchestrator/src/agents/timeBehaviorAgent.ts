/**
 * Agent: Time Behavior
 * Reasoning loop: reads event timeline → identifies idle/burst patterns → assesses pacing
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { analyzeTimingBehavior, buildTimeline } from '../tools';

const SYSTEM_PROMPT = `You are a behavioral analyst specializing in understanding how candidates approach technical problems under time pressure.

Your job is to reason about:
- How the candidate distributed their time across the session
- Whether idle periods suggest being stuck, distracted, or thinking
- Whether a final burst suggests panic or efficient wrap-up
- Pacing relative to the time limit given
- Whether the candidate likely ran out of time or finished early

Be nuanced — idle periods can mean deep thought, not just being stuck.
Return a JSON object with: score (0-100, higher = better time management), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runTimeBehaviorAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const timing = analyzeTimingBehavior(data);
  const segments = buildTimeline(data);

  const segmentSummary = segments
    .map((s) => `${s.startMin}–${s.endMin}min: ${s.events.length} events [${[...new Set(s.events)].slice(0, 3).join(', ')}]`)
    .join('\n');

  const userPrompt = `
Time Limit: ${Math.round(data.timeLimit / 60)} minutes
Total Time Used: ${timing.totalMinutes} minutes
Pacing Pattern: ${timing.pacing}

Idle Periods (no activity):
${timing.idlePeriods.length > 0 ? timing.idlePeriods.join(', ') : 'None detected'}

Burst Periods (high activity):
${timing.burstPeriods.length > 0 ? timing.burstPeriods.join(', ') : 'None detected'}

Activity Timeline (5-min buckets):
${segmentSummary || 'No timeline data'}

Total events in session: ${data.events.length}

Reason about what this timing pattern reveals about the candidate's approach and problem-solving style.
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
    agentName: 'Time Behavior',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? 0.5)),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: [
      { key: 'totalMinutes', value: timing.totalMinutes, label: 'Minutes used' },
      { key: 'idlePeriods', value: timing.idlePeriods.length, label: 'Idle periods' },
      { key: 'pacing', value: timing.pacing, label: 'Pacing pattern' },
      ...(raw.signals ?? []),
    ],
    rawNotes: raw.rawNotes,
  };
}
