/**
 * Server C Agent System — Shared Types
 *
 * All agents in the Server C pipeline use these types.
 * Nothing here touches existing code.
 */

// ── Raw data fed into the pipeline ────────────────────────────────────────────

export interface SessionData {
  sessionId: string;
  candidateName?: string;
  candidateEmail?: string;
  startedAt?: Date;
  submittedAt?: Date;
  timeLimit: number; // seconds
  finalCode?: string; // JSON string of { [filename]: code }
  aiInteractions: AiInteractionRecord[];
  codeSnapshots: CodeSnapshotRecord[];
  events: EventRecord[];
  assessment?: {
    jobTitle?: string;
    role?: string;
    level?: string;
    techStack?: any;
    template?: any;
  };
}

export interface AiInteractionRecord {
  id: string;
  eventType: string;
  prompt?: string;
  response?: string;
  model?: string;
  promptTokens?: number;
  completionTokens?: number;
  latencyMs?: number;
  timestamp: Date;
  tabId?: string;
  conversationTurn?: number;
}

export interface CodeSnapshotRecord {
  id: string;
  timestamp: Date;
  code?: string;      // raw code string from DB
  linesOfCode?: number;
}

export interface EventRecord {
  id: string;
  eventType: string;
  timestamp: Date;
  metadata?: any;
  codeSnippet?: string;
  codeBefore?: string;
  codeAfter?: string;
}

// ── Per-agent finding ──────────────────────────────────────────────────────────

export interface AgentFinding {
  agentName: string;
  score: number;        // 0–100
  confidence: number;   // 0–1
  summary: string;
  evidence: EvidenceItem[];
  signals: Signal[];
  rawNotes?: string;    // agent's internal reasoning notes
}

export interface EvidenceItem {
  type: string;
  description: string;
  severity: 'high' | 'medium' | 'low' | 'info';
  timestamp?: string;
  data?: any;
}

export interface Signal {
  key: string;
  value: string | number | boolean;
  label: string;
}

// ── Structuring agent output (the brief for Judge) ────────────────────────────

export interface StructuredBrief {
  sessionId: string;
  candidateName?: string;
  timelineSummary: TimelineSegment[];
  dimensionFindings: Record<string, AgentFinding>;
  conflicts: ConflictItem[];
  rankedSignals: RankedSignal[];
  overallDataQuality: number; // 0–1, how much data was available
}

export interface TimelineSegment {
  startMin: number;
  endMin: number;
  label: string;
  keyEvents: string[];
}

export interface ConflictItem {
  dimensions: string[];
  description: string;
  severity: 'high' | 'medium' | 'low';
}

export interface RankedSignal {
  rank: number;
  signal: string;
  dimension: string;
  weight: number;
}

// ── Judge verdict ──────────────────────────────────────────────────────────────

export interface JudgeVerdict {
  overallScore: number;           // 0–100
  tier: 'strong' | 'average' | 'weak';
  confidence: number;             // 0–1
  strengths: string[];
  redFlags: string[];
  aiUsageRisk: 'low' | 'medium' | 'high';
  recommendation: string;
  dimensionScores: Record<string, number>;
  conflictResolution: string;     // how judge resolved conflicts
  reasoning: string;              // judge's reasoning narrative
}

// ── Final output written to AgentInsight.judge ────────────────────────────────

export interface ServerCInsight {
  version: string;
  computedAt: string;
  sessionId: string;
  pipeline: 'multi-agent-v1';

  // The structured brief (pre-judge)
  brief: StructuredBrief;

  // The verdict
  verdict: JudgeVerdict;

  // Per-dimension scores for easy dashboard access
  scores: {
    overall: number;
    codeQuality: number;
    bugFixQuality: number;
    timeBehavior: number;
    aiUsage: number;
    taskDifficulty: number;
    commDocs: number;
  };

  // Surface-level fields (backward compat with existing dashboard reads)
  overallScore: number;
  strengths: string[];
  weaknesses: string[];
  confidence: number;
  explanation: string;
}
