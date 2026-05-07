/**
 * Server C Orchestrator — Pure Utility Functions
 *
 * No database access here. Data arrives from the backend in the request body.
 * These helpers just transform / analyze the SessionData in memory.
 */

import { SessionData } from './types';

// ── Parse final code files ─────────────────────────────────────────────────────

export function parseFinalCode(finalCode?: string): Record<string, string> {
  if (!finalCode) return {};
  try {
    const parsed = JSON.parse(finalCode);
    if (typeof parsed === 'object' && parsed !== null) return parsed;
    return { main: finalCode };
  } catch {
    return { main: finalCode };
  }
}

// ── Build timeline segments ────────────────────────────────────────────────────

export function buildTimeline(data: SessionData) {
  if (!data.startedAt) return [];
  const startMs = data.startedAt.getTime();
  const endMs = data.submittedAt?.getTime() ?? startMs + data.timeLimit * 1000;
  const totalMin = Math.round((endMs - startMs) / 60000);
  const segmentSize = Math.max(10, Math.round(totalMin / 4));
  const segments: Array<{ startMin: number; endMin: number; events: string[] }> = [];

  for (let start = 0; start < totalMin; start += segmentSize) {
    const segStart = startMs + start * 60000;
    const segEnd = startMs + Math.min(start + segmentSize, totalMin) * 60000;
    const segEvents = data.events
      .filter((e) => { const t = e.timestamp.getTime(); return t >= segStart && t < segEnd; })
      .map((e) => e.eventType);
    segments.push({ startMin: start, endMin: Math.min(start + segmentSize, totalMin), events: segEvents });
  }
  return segments;
}

// ── AI interaction summary ─────────────────────────────────────────────────────

export function summarizeAiInteractions(data: SessionData) {
  const interactions = data.aiInteractions;
  // Paste/apply/copy events live in aiInteractions, not events
  const pasteEvents = data.aiInteractions.filter((e) =>
    e.eventType.toLowerCase().includes('paste') ||
    e.eventType === 'code_applied_from_ai' ||
    e.eventType === 'code_applied' ||
    e.eventType === 'code_copied_from_ai' ||
    e.eventType === 'code_pasted_from_ai'
  );
  const tabSwitches = data.events.filter((e) =>
    e.eventType.toLowerCase().includes('tab_switch') ||
    e.eventType.toLowerCase().includes('tab_blur') ||
    e.eventType === 'assessment_tab_switched'
  );
  const promptsSent = interactions.filter((i) => i.eventType === 'prompt_sent').length;
  const responsesReceived = interactions.filter((i) => i.eventType === 'response_received').length;
  const copies = interactions.filter((i) =>
    i.eventType === 'code_copied_from_ai' || i.eventType === 'copy'
  ).length;
  const applies = interactions.filter((i) =>
    i.eventType === 'code_applied_from_ai' || i.eventType === 'code_applied' || i.eventType === 'apply'
  ).length;

  let suspiciousPastes = 0;
  for (const paste of pasteEvents) {
    const pasteTime = paste.timestamp.getTime();
    const recent = interactions.find(
      (i) => i.eventType === 'response_received' &&
        pasteTime - i.timestamp.getTime() >= 0 &&
        pasteTime - i.timestamp.getTime() <= 30000
    );
    if (recent) suspiciousPastes++;
  }

  const codeModifiedEvents = data.events.filter((e) =>
    e.eventType.toLowerCase().includes('code_modified') ||
    e.eventType.toLowerCase().includes('manual_edit') ||
    e.eventType.toLowerCase().includes('keystroke')
  );

  return {
    totalInteractions: interactions.length, promptsSent, responsesReceived,
    copies, applies, totalPastes: pasteEvents.length, suspiciousPastes,
    tabSwitches: tabSwitches.length,
    codeModified: codeModifiedEvents.length,
    aiUsageIntensity: promptsSent === 0 ? 'none' : promptsSent <= 3 ? 'low' : promptsSent <= 8 ? 'medium' : 'high',
  };
}

// ── Code metrics ───────────────────────────────────────────────────────────────

export function analyzeCodeMetrics(files: Record<string, string>) {
  let totalLines = 0, commentLines = 0, emptyLines = 0;
  let hasTests = false, hasErrorHandling = false;
  const fileMetrics: Record<string, any> = {};

  for (const [filename, code] of Object.entries(files)) {
    const lines = code.split('\n');
    const fileComments = lines.filter((l) => l.trim().startsWith('//') || l.trim().startsWith('#') || l.trim().startsWith('*')).length;
    const fileEmpty = lines.filter((l) => l.trim() === '').length;
    totalLines += lines.length; commentLines += fileComments; emptyLines += fileEmpty;
    if (filename.includes('test') || filename.includes('spec')) hasTests = true;
    if (code.includes('try') || code.includes('catch') || code.includes('except')) hasErrorHandling = true;
    fileMetrics[filename] = { lines: lines.length, comments: fileComments, empty: fileEmpty };
  }

  return {
    totalFiles: Object.keys(files).length, totalLines, commentLines, emptyLines,
    commentRatio: totalLines > 0 ? commentLines / totalLines : 0,
    hasTests, hasErrorHandling, fileMetrics,
  };
}

// ── Timing analysis ────────────────────────────────────────────────────────────

export function analyzeTimingBehavior(data: SessionData) {
  if (!data.startedAt) return { totalMinutes: 0, idlePeriods: [], burstPeriods: [], pacing: 'unknown' };
  const startMs = data.startedAt.getTime();
  const endMs = data.submittedAt?.getTime() ?? startMs + data.timeLimit * 1000;
  const totalMinutes = Math.round((endMs - startMs) / 60000);
  const bucketSize = 5 * 60 * 1000;
  const buckets: Record<number, number> = {};

  for (const ev of data.events) {
    const bucket = Math.floor((ev.timestamp.getTime() - startMs) / bucketSize);
    buckets[bucket] = (buckets[bucket] ?? 0) + 1;
  }

  const idlePeriods: string[] = [], burstPeriods: string[] = [];
  for (let b = 0; b * bucketSize < endMs - startMs; b++) {
    const count = buckets[b] ?? 0;
    const s = b * 5, e = s + 5;
    if (count === 0) idlePeriods.push(`${s}–${e}min`);
    if (count > 20) burstPeriods.push(`${s}–${e}min (${count} events)`);
  }

  const bucketCounts = Object.values(buckets);
  const avg = bucketCounts.reduce((a, b) => a + b, 0) / Math.max(bucketCounts.length, 1);
  const lastBuckets = Object.entries(buckets)
    .filter(([k]) => parseInt(k) >= Math.floor((endMs - startMs) / bucketSize) - 2)
    .map(([, v]) => v);
  const lastAvg = lastBuckets.reduce((a, b) => a + b, 0) / Math.max(lastBuckets.length, 1);
  const idleThreshold = Math.max(1, Math.floor(totalMinutes / 15));
  const pacing = idlePeriods.length > idleThreshold ? 'slow_start' : lastAvg > avg * 1.8 ? 'rushed_ending' : 'steady';

  return { totalMinutes, idlePeriods, burstPeriods, pacing };
}
