'use client';

import { ScenarioOption } from '../lib/types';
import { Tooltip } from './Tooltip';

interface ScenarioCardProps {
  scenario: ScenarioOption;
  rank: number;
  onRun: (scenario: ScenarioOption) => void;
}

export function ScenarioCard({ scenario, rank, onRun }: ScenarioCardProps) {
  return (
    <article className="card" aria-label={`Scenario ${scenario.title}`}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="tag" aria-hidden>
            Top #{rank}
          </div>
          <h3>{scenario.title}</h3>
        </div>
        <Tooltip label="Scores are deterministic keyword matches today; LLM ranking swaps in once the provider is wired up.">
          <span aria-hidden>ℹ️</span>
        </Tooltip>
      </header>
      <p>{scenario.short_description}</p>
      <p>
        <strong>Rationale:</strong> {scenario.rationale}
      </p>
      <p>
        <strong>Inputs:</strong> {scenario.inputs.join(', ')}
      </p>
      <ul>
        {scenario.deliverables.map((deliverable) => (
          <li key={deliverable}>{deliverable}</li>
        ))}
      </ul>
      <p aria-label={`Relevance score ${scenario.score}`}>Score: {scenario.score.toFixed(2)}</p>
      <button className="primary" type="button" onClick={() => onRun(scenario)}>
        Run Scenario
      </button>
    </article>
  );
}
