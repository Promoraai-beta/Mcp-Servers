/**
 * Server C Orchestrator — HTTP Entry Point
 *
 * The backend calls:
 *   POST http://localhost:3002/analyze  { sessionId, sessionData }
 *
 * sessionData is the full session payload (dates serialized as ISO strings).
 * Returns the ServerCInsight JSON — backend writes it to DB.
 * Server C never touches the database.
 */

import express from 'express';
import { runOrchestrator } from './orchestrator';
import { SessionData } from './types';

const app = express();
app.use(express.json({ limit: '50mb' }));

const PORT = process.env.SERVER_C_PORT ?? 3002;

// Health check
app.get('/health', (_, res) => res.json({ status: 'ok', server: 'server-c-orchestrator' }));

// Main analysis endpoint
app.post('/analyze', async (req, res) => {
  const { sessionId, sessionData } = req.body;

  if (!sessionId) {
    return res.status(400).json({ success: false, error: 'sessionId is required' });
  }
  if (!sessionData) {
    return res.status(400).json({ success: false, error: 'sessionData is required' });
  }

  // Rehydrate Date objects — JSON serialization converts them to ISO strings
  const data: SessionData = {
    ...sessionData,
    startedAt: sessionData.startedAt ? new Date(sessionData.startedAt) : undefined,
    submittedAt: sessionData.submittedAt ? new Date(sessionData.submittedAt) : undefined,
    aiInteractions: (sessionData.aiInteractions ?? []).map((ai: any) => ({
      ...ai,
      timestamp: new Date(ai.timestamp),
    })),
    codeSnapshots: (sessionData.codeSnapshots ?? []).map((snap: any) => ({
      ...snap,
      timestamp: new Date(snap.timestamp),
    })),
    events: (sessionData.events ?? []).map((ev: any) => ({
      ...ev,
      timestamp: new Date(ev.timestamp),
    })),
  };

  try {
    const insight = await runOrchestrator(sessionId, data);
    res.json({ success: true, data: insight });
  } catch (error: any) {
    console.error('[Server C] Analysis failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`[Server C Orchestrator] Running on port ${PORT}`);
});
