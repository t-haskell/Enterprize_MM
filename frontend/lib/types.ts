export interface ScenarioOption {
  scenario_id: string;
  title: string;
  short_description: string;
  rationale: string;
  inputs: string[];
  methodology: string[];
  deliverables: string[];
  score: number;
}

export interface SuggestionResponse {
  prompt: string;
  options: ScenarioOption[];
  metadata: Record<string, unknown>;
}

export interface RunState {
  run_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  message: string;
  scenario_id: string;
  parameters: Record<string, unknown>;
  timestamp?: string;
  result?: unknown;
  [key: string]: unknown;
}
