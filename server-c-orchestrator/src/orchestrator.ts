/**
 * Server C Orchestrator — Multi-Agent Pipeline
 *
 * Flow:
 *   1. Receive session data from the backend (no DB access here)
 *   2. Run 6 analyzer agents IN PARALLEL
 *   3. Structuring agent organizes findings + timeline into a brief
 *   4. Judge agent reads the brief → makes verdict
 *   5. Return insight to backend — backend writes to DB
 */

import OpenAI from 'openai';
import { runCodeQualityAgent } from './agents/codeQualityAgent';
import { runAiUsageAgent } from './agents/aiUsageAgent';
import { runTimeBehaviorAgent } from './agents/timeBehaviorAgent';
import { runBugFixAgent } from './agents/bugFixAgent';
import { runTaskDifficultyAgent } from './agents/taskDifficultyAgent';
import { runCommDocsAgent } from './agents/commDocsAgent';
import { runStructuringAgent } from './structuringAgent';
import { runJudgeAgent } from './judgeAgent';
import { AgentFinding, SessionData, ServerCInsight } from './types';

// ── OpenAI client ──────────────────────────────────────────────────────────────

function makeClient(): { client: OpenAI; model: string; strongModel: string } {
  const azureEndpoint = process.env.AZURE_OPENAI_ENDPOINT?.trim();
  const apiKey = process.env.OPENAI_API_KEY ?? '';

  if (azureEndpoint) {
    const client = new OpenAI({
      apiKey,
      baseURL: `${azureEndpoint}/openai/deployments`,
      defaultQuery: { 'api-version': process.env.AZURE_OPENAI_API_VERSION ?? '2024-12-01-preview' },
      defaultHeaders: { 'api-key': apiKey },
    });
    const model = process.env.AZURE_OPENAI_DEPLOYMENT ?? 'gpt-4.1';
    return { client, model, strongModel: model };
  }

  const client = new OpenAI({ apiKey });
  return {
    client,
    model: process.env.OPENAI_MODEL ?? 'gpt-4o-mini',
    strongModel: process.env.OPENAI_STRONG_MODEL ?? 'gpt-4o',
  };
}

// ── Main pipeline ──────────────────────────────────────────────────────────────

export async function runOrchestrator(sessionId: string, data: SessionData): Promise<ServerCInsight> {
  console.log(`[Orchestrator] Starting pipeline for session ${sessionId} — ${data.events.length} events, ${data.aiInteractions.length} AI interactions`);
  const start = Date.now();
  const { client, model, strongModel } = makeClient();

  // Step 1 — 6 analyzers in parallel
  console.log('[Orchestrator] Running 6 analyzers in parallel...');
  const settled = await Promise.allSettled([
    runCodeQualityAgent(data, client, model),
    runAiUsageAgent(data, client, model),
    runTimeBehaviorAgent(data, client, model),
    runBugFixAgent(data, client, model),
    runTaskDifficultyAgent(data, client, model),
    runCommDocsAgent(data, client, model),
  ]);

  const findings: AgentFinding[] = [
    unwrap(settled[0], 'Code Quality'),
    unwrap(settled[1], 'AI Usage'),
    unwrap(settled[2], 'Time Behavior'),
    unwrap(settled[3], 'Bug Fix Quality'),
    unwrap(settled[4], 'Task Difficulty'),
    unwrap(settled[5], 'Comm & Docs'),
  ];

  console.log(`[Orchestrator] Analyzers done: ${findings.map((f) => `${f.agentName}=${f.score}`).join(', ')}`);

  // Step 3 — Structuring agent (before judge)
  console.log('[Orchestrator] Structuring findings into brief...');
  const brief = await runStructuringAgent(findings, data, client, model);

  // Step 4 — Judge reads the brief, makes verdict
  console.log('[Orchestrator] Running judge...');
  const verdict = await runJudgeAgent(brief, client, strongModel);
  console.log(`[Orchestrator] Verdict: score=${verdict.overallScore}, tier=${verdict.tier}`);

  // Step 5 — Build insight object
  const findingByName = (name: string) => findings.find((f) => f.agentName === name);

  const insight: ServerCInsight = {
    version: '1.0',
    computedAt: new Date().toISOString(),
    sessionId,
    pipeline: 'multi-agent-v1',
    brief,
    verdict,
    scores: {
      overall: verdict.overallScore,
      codeQuality: findingByName('Code Quality')?.score ?? 50,
      bugFixQuality: findingByName('Bug Fix Quality')?.score ?? 50,
      timeBehavior: findingByName('Time Behavior')?.score ?? 50,
      aiUsage: findingByName('AI Usage')?.score ?? 50,
      taskDifficulty: findingByName('Task Difficulty')?.score ?? 50,
      commDocs: findingByName('Comm & Docs')?.score ?? 50,
    },
    overallScore: verdict.overallScore,
    strengths: verdict.strengths,
    weaknesses: verdict.redFlags,
    confidence: verdict.confidence,
    explanation: verdict.reasoning,
  };

  console.log(`[Orchestrator] Done in ${((Date.now() - start) / 1000).toFixed(1)}s — returning insight to backend`);
  return insight;
}

// ── Helper ─────────────────────────────────────────────────────────────────────

function unwrap(result: PromiseSettledResult<AgentFinding>, agentName: string): AgentFinding {
  if (result.status === 'fulfilled') return result.value;
  console.error(`[Orchestrator] Agent "${agentName}" failed:`, result.reason?.message);
  return { agentName, score: 50, confidence: 0, summary: `Agent failed: ${result.reason?.message ?? 'unknown'}`, evidence: [], signals: [] };
}
