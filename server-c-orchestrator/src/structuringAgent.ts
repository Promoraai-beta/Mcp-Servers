/**
 * Agent: Structuring Agent
 * Takes all 6 raw findings + timeline → produces a clean coherent brief for the Judge
 * Runs BEFORE the Judge so the Judge focuses purely on verdict, not organization
 *
 * NOTE: dimensionFindings are built directly from agent findings (no LLM override needed).
 * The LLM is used only for conflict detection and signal ranking.
 */

import OpenAI from 'openai';
import { AgentFinding, SessionData, StructuredBrief, ConflictItem, RankedSignal } from './types';
import { buildTimeline } from './tools';

const SYSTEM_PROMPT = `You are a senior technical assessment coordinator. Your job is to analyze findings from 6 specialist analysts and identify:
1. Any conflicts between dimensions (e.g. clean code but suspicious AI usage)
2. A ranked list of the most important signals for the judge

Return JSON with ONLY: conflicts, rankedSignals, overallDataQuality.
Do NOT return timelineSummary or dimensionFindings — those are built separately.`;

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

  // Build dimensionFindings directly from agent findings — LLM override would lose typed data
  const dimensionFindings: Record<string, AgentFinding> = {};
  for (const f of findings) {
    dimensionFindings[f.agentName] = f;
  }

  const findingsSummary = findings
    .map(
      (f) =>
        `${f.agentName}: score=${f.score}/100, confidence=${f.confidence.toFixed(2)}\n` +
        `  Summary: ${f.summary}\n` +
        `  Key evidence: ${f.evidence.slice(0, 3).map((e) => `[${e.severity}] ${e.description}`).join(' | ')}`
    )
    .join('\n\n');

  // Include video analysis in structuring prompt so LLM can detect conflicts
  // e.g. "AI Usage score=80 (clean) but video shows candidate googling solutions"
  const videoContext = data.videoAnalysis
    ? `\n=== SCREENSHARE VIDEO ANALYSIS ===\nVerdict: ${data.videoAnalysis.verdict} | Risk: ${data.videoAnalysis.overallRisk} | Confidence: ${(data.videoAnalysis.confidence * 100).toFixed(0)}%\nSuspicious activities: ${data.videoAnalysis.suspiciousActivities.join(', ') || 'none detected'}\n`
    : '';

  const userPrompt = `
Candidate: ${data.candidateName ?? 'Unknown'}
Assessment: ${data.assessment?.jobTitle ?? 'Technical Assessment'} (${data.assessment?.level ?? 'unknown'} level)

=== RAW FINDINGS FROM 6 ANALYSTS ===
${findingsSummary}
${videoContext}
Identify:
1. Conflicts between dimensions (e.g. high code quality score but high AI usage risk — which matters more?)
   IMPORTANT: If video analysis shows suspicious behavior, flag conflicts with agent scores that appear too clean.
2. Rank the top 5 signals by importance for the judge (include video risk if present)
3. Overall data quality (0.0–1.0) based on how complete/reliable the findings are

Return as JSON:
{
  "conflicts": [{ "dimensions": [], "description": "", "severity": "high|medium|low" }],
  "rankedSignals": [{ "rank": 1, "signal": "", "dimension": "", "weight": 0.0 }],
  "overallDataQuality": 0.0
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

  return {
    sessionId: data.sessionId,
    candidateName: data.candidateName,
    timelineSummary,
    dimensionFindings,
    conflicts: (raw.conflicts ?? []) as ConflictItem[],
    rankedSignals: (raw.rankedSignals ?? []) as RankedSignal[],
    overallDataQuality: Math.min(1, Math.max(0, raw.overallDataQuality ?? 0.7)),
    videoAnalysis: data.videoAnalysis,
  };
}
