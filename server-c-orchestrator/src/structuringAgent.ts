/**
 * Agent: Structuring Agent
 * Takes all 6 raw findings + timeline → produces a clean coherent brief for the Judge
 * Runs BEFORE the Judge so the Judge focuses purely on verdict, not organization
 */

import OpenAI from 'openai';
import { AgentFinding, SessionData, StructuredBrief, ConflictItem, RankedSignal } from './types';
import { buildTimeline } from './tools';

const SYSTEM_PROMPT = `You are a senior technical assessment coordinator. Your job is to take raw findings from 6 specialist analysts and organize them into a clear, chronological brief for a judge to review.

You do NOT make the verdict. You organize and surface:
1. A timeline of what happened during the session
2. What each dimension found (with scores and key evidence)
3. Any conflicts between dimensions (e.g. clean code but suspicious AI usage)
4. A ranked list of the most important signals

Your output must be clean, structured JSON that gives the judge everything they need to make a fair verdict.
Return JSON with: timelineSummary, dimensionFindings, conflicts, rankedSignals, overallDataQuality.`;

export async function runStructuringAgent(
  findings: AgentFinding[],
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<StructuredBrief> {
  const segments = buildTimeline(data);

  const timelineSummary = segments.map((s) => ({
    startMin: s.startMin,
    endMin: s.endMin,
    label: `${s.startMin}–${s.endMin}min`,
    keyEvents: [...new Set(s.events)].slice(0, 5),
  }));

  const findingsSummary = findings
    .map(
      (f) =>
        `${f.agentName}: score=${f.score}/100, confidence=${f.confidence.toFixed(2)}\n` +
        `  Summary: ${f.summary}\n` +
        `  Key evidence: ${f.evidence.slice(0, 3).map((e) => `[${e.severity}] ${e.description}`).join(' | ')}`
    )
    .join('\n\n');

  const userPrompt = `
Candidate: ${data.candidateName ?? 'Unknown'}
Assessment: ${data.assessment?.jobTitle ?? 'Technical Assessment'} (${data.assessment?.level ?? 'unknown'} level)
Session duration: ${Math.round(data.timeLimit / 60)} min limit

=== RAW FINDINGS FROM 6 ANALYSTS ===
${findingsSummary}

=== TIMELINE ===
${timelineSummary.map((s) => `${s.label}: ${s.keyEvents.join(', ') || 'quiet'}`).join('\n')}

Organize this into a structured brief:
1. Summarize the timeline with meaningful labels
2. Capture each dimension's key finding
3. Identify conflicts (e.g. high code quality score but high AI usage risk)
4. Rank the top 5 signals by importance for the judge

Return as JSON matching this shape:
{
  "timelineSummary": [{ "startMin", "endMin", "label", "keyEvents" }],
  "dimensionFindings": { "<agentName>": { finding object } },
  "conflicts": [{ "dimensions": [], "description", "severity" }],
  "rankedSignals": [{ "rank", "signal", "dimension", "weight" }],
  "overallDataQuality": 0.0-1.0
}`;

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.2,
  });

  const raw = JSON.parse(response.choices[0].message.content ?? '{}');

  // Build dimensionFindings map from raw findings, enriched by LLM organization
  const dimensionFindings: Record<string, AgentFinding> = {};
  for (const f of findings) {
    dimensionFindings[f.agentName] = f;
  }

  return {
    sessionId: data.sessionId,
    candidateName: data.candidateName,
    timelineSummary: raw.timelineSummary ?? timelineSummary,
    dimensionFindings,
    conflicts: (raw.conflicts ?? []) as ConflictItem[],
    rankedSignals: (raw.rankedSignals ?? []) as RankedSignal[],
    overallDataQuality: Math.min(1, Math.max(0, raw.overallDataQuality ?? 0.7)),
  };
}
