/**
 * Agent: Task Difficulty
 * Reasoning loop: reads task list + code → assesses difficulty vs performance
 */

import OpenAI from 'openai';
import { SessionData, AgentFinding } from '../types';
import { parseFinalCode } from '../tools';

const SYSTEM_PROMPT = `You are a technical assessment calibration expert who understands how task difficulty maps to candidate performance.

Your job is to reason about:
- What difficulty level the tasks were (easy/medium/hard)
- Whether the candidate attempted all tasks or skipped hard ones
- Whether performance on easy vs hard tasks reveals anything about skill ceiling
- Whether the time spent aligns with difficulty expectations
- The overall skill signal considering difficulty context

Return a JSON object with: score (0-100), confidence (0-1), summary (string),
evidence (array of {type, description, severity}), signals (array of {key, value, label}), rawNotes (string).`;

export async function runTaskDifficultyAgent(
  data: SessionData,
  client: OpenAI,
  model: string
): Promise<AgentFinding> {
  const files = parseFinalCode(data.finalCode);
  const fileCount = Object.keys(files).length;

  // Extract task list from template
  const template = data.assessment?.template as any;
  const tasks =
    template?.templateSpec?.tasks ||
    template?.tasks ||
    template?.suggestedAssessments ||
    [];

  const taskList =
    tasks.length > 0
      ? tasks
          .map((t: any) => `- [${t.difficulty ?? 'unknown'}] ${t.title ?? t.description ?? 'Task'}`)
          .join('\n')
      : 'No task manifest available';

  const userPrompt = `
Assessment Role: ${data.assessment?.role ?? 'unknown'} (${data.assessment?.level ?? 'unknown'} level)
Time Limit: ${Math.round(data.timeLimit / 60)} minutes

Tasks in assessment:
${taskList}

Code submitted: ${fileCount} files, ${Object.values(files).join('\n').split('\n').length} total lines

Analyze the difficulty of the tasks relative to the candidate's level,
and assess how well they performed considering the difficulty.
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
    agentName: 'Task Difficulty',
    score: Math.min(100, Math.max(0, raw.score ?? 50)),
    confidence: Math.min(1, Math.max(0, raw.confidence ?? (tasks.length > 0 ? 0.7 : 0.3))),
    summary: raw.summary ?? 'No summary',
    evidence: raw.evidence ?? [],
    signals: [
      { key: 'taskCount', value: tasks.length, label: 'Tasks in assessment' },
      { key: 'filesSubmitted', value: fileCount, label: 'Files submitted' },
      ...(raw.signals ?? []),
    ],
    rawNotes: raw.rawNotes,
  };
}
