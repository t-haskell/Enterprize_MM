import { RunState, SuggestionResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function suggestScenarios(prompt: string, maxScenarios = 5): Promise<SuggestionResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, max_scenarios: maxScenarios })
  });
  return handleResponse<SuggestionResponse>(response);
}

export async function runScenario(
  scenarioId: string,
  parameters: Record<string, unknown> = {}
): Promise<RunState> {
  const response = await fetch(`${API_BASE_URL}/analysis/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id: scenarioId, parameters })
  });
  return handleResponse<RunState>(response);
}

export async function fetchRun(runId: string): Promise<RunState> {
  const response = await fetch(`${API_BASE_URL}/analysis/runs/${runId}`);
  return handleResponse<RunState>(response);
}

export function buildStreamUrl(runId: string): string {
  const url = new URL(`${API_BASE_URL}/analysis/runs/${runId}/stream`);
  url.searchParams.set('client', 'frontend');
  return url.toString();
}
