/**
 * Agent: Judge LLM
 * Reads the structured brief → makes the final verdict
 * Runs AFTER structuringAgent — receives a clean, organized brief
 */

import OpenAI from 'openai';
import { StructuredBrief, JudgeVerdict } from './types';

const SYSTEM_PROMPT = `You are a senior engineering hiring manager making a final assessment verdict.

You have been given a structured brief containing findings from 6 specialist analysts, organized by a coordinator.
Your job is to:
1. Read the brief carefully
2. Weigh the evidence — not all dimensions are equal
3. Resolve conflicts (e.g. great code but suspicious AI usage — which matters more?)
4. Make a fair, calibrated verdict

Weighting guidance:
- Code Quality: 25%
- Bug Fix Quality: 30% (most directly measures the task)
- AI Usage (integrity): 20%
- Time Behavior: 10%
- Task Difficulty: 10%
- Comm & Docs: 5%

Be honest. A strong candidate scores 75+. Average is 50–74. Below 50 is weak.
Do not be harsh without evidence. Do not be lenient when there are clear red flags.

Return JSON with: overallScore (0-100), tier (strong/average/weak), confidence (0-1),
strengths (string[]), redFlags (string[]), aiUsageRisk (low/medium/high),
recommendation (string), dimensionScores ({agentName: score}),
conflictResolution (string), reasoning (string).`;

export async function runJudgeAgent(
  brief: StructuredBrief,
  client: OpenAI,
  model: string
): Promise<JudgeVerdict> {
  // Build a readable brief for the judge
  const dimensionSummary = Object.entries(brief.dimensionFindings)
    .map(([name, f]) => `${name}: ${f.score}/100 (confidence: ${f.confidence.toFixed(2)})\n  ${f.summary}`)
    .join('\n\n');

  const conflictSummary =
    brief.conflicts.length > 0
      ? brief.conflicts.map((c) => `[${c.severity.toUpperCase()}] ${c.description}`).join('\n')
      : 'No conflicts detected';

  const topSignals = brief.rankedSignals
    .slice(0, 5)
    .map((s) => `#${s.rank} [${s.dimension}] ${s.signal}`)
    .join('\n');

  const userPrompt = `
=== ASSESSMENT BRIEF ===
Candidate: ${brief.candidateName ?? 'Unknown'}
Data Quality: ${(brief.overallDataQuality * 100).toFixed(0)}%

=== DIMENSION FINDINGS ===
${dimensionSummary}

=== CONFLICTS TO RESOLVE ===
${conflictSummary}

=== TOP SIGNALS ===
${topSignals || 'None ranked'}

=== TIMELINE SUMMARY ===
${brief.timelineSummary.map((s) => `${s.label}: ${s.keyEvents.join(', ') || 'quiet'}`).join('\n')}

Based on this brief, make your final verdict.
Explain how you resolved any conflicts.
Return as JSON.`;

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.2,
    max_tokens: 1500,
  });

  const raw = JSON.parse(response.choices[0].message.content ?? '{}');

  const score = Math.min(100, Math.max(0, raw.overallScore ?? 50));
  const tier: JudgeVerdict['tier'] =
    raw.tier === 'strong' || score >= 75
      ? 'strong'
      : raw.tier === 'weak' || score < 50
      ? 'weak'
      : 'average';

  return {
    overallScore: score,
    tier,
    confidence: Math.min(1, Math.max(0, raw.confidence ?? 0.7)),
    strengths: raw.strengths ?? [],
    redFlags: raw.redFlags ?? [],
    aiUsageRisk: raw.aiUsageRisk ?? 'low',
    recommendation: raw.recommendation ?? '',
    dimensionScores: raw.dimensionScores ?? {},
    conflictResolution: raw.conflictResolution ?? '',
    reasoning: raw.reasoning ?? '',
  };
}
