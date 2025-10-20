'use client';

import Link from 'next/link';
import { FormEvent, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { logPromptUsage } from '../lib/analytics';
import { runScenario, suggestScenarios } from '../lib/api';
import { ScenarioOption, SuggestionResponse } from '../lib/types';
import { HelpContent } from '../components/HelpContent';
import { ScenarioCard } from '../components/ScenarioCard';

const MAX_SCENARIOS = 5;
const DEMO_SCENARIOS: ScenarioOption[] = [
  {
    scenario_id: 'quant_factor',
    title: 'Quant Factor Screen (Value/Quality/Momentum)',
    short_description: 'Composite factor scoring with optional ML ranking',
    rationale: 'Blend valuation, quality, and momentum for robust alpha sourcing.',
    inputs: ['universe', 'lookback', 'weights'],
    methodology: [],
    deliverables: ['Top-N tickers', 'Factor attribution', 'Backtest KPIs'],
    score: 0.92
  },
  {
    scenario_id: 'trend_strength',
    title: 'Trend & Relative Strength',
    short_description: 'Trend filters with relative strength overlays',
    rationale: 'Identify leaders by combining trend confirmation with RS rankings.',
    inputs: ['universe', 'ma_windows', 'rs_window'],
    methodology: [],
    deliverables: ['Trend-qualified tickers', 'RS leaderboard', 'Position size guidance'],
    score: 0.87
  },
  {
    scenario_id: 'earnings_momentum',
    title: 'Earnings Momentum & Revisions',
    short_description: 'Capture post-earnings drift and analyst revisions',
    rationale: 'Earnings-related signals have persistent short-term alpha.',
    inputs: ['earnings_window', 'revision_thresholds'],
    methodology: [],
    deliverables: ['Pre/post earnings watchlist', 'Signal diagnostics', 'Event calendar'],
    score: 0.81
  },
  {
    scenario_id: 'lightweight_dcf',
    title: 'Lightweight DCF & Margin-of-Safety',
    short_description: 'Scenario-based discounted cash-flow valuation',
    rationale: 'Monte Carlo on growth/WACC bands to estimate fair value distribution.',
    inputs: ['revenue_growth', 'fcf_growth', 'wacc', 'terminal'],
    methodology: [],
    deliverables: ['Margin-of-safety vs price', 'Sensitivity tornado', 'Undervalued list'],
    score: 0.78
  }
];

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [suggestions, setSuggestions] = useState<ScenarioOption[]>(DEMO_SCENARIOS);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>({ demo: true });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('Showing example ranking');

  const helperCopy = useMemo(() => {
    if (!metadata) return 'Submit a prompt to explore recommended scenarios.';
    if (metadata['demo']) {
      return 'These example scenarios illustrate the ranking output—submit your own prompt to refresh them.';
    }
    if (metadata['llm']) return String(metadata['llm']);
    return 'Scenario order is based on keyword affinity while the LLM bridge is stubbed.';
  }, [metadata]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim()) {
      setError('Enter a prompt to get ranked scenarios.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setStatusMessage('Ranking scenarios…');

    try {
      const response: SuggestionResponse = await suggestScenarios(prompt.trim(), MAX_SCENARIOS);
      setSuggestions(response.options.slice(0, MAX_SCENARIOS));
      setMetadata(response.metadata);
      setStatusMessage(`Showing ${response.options.length} scenarios`);
      await logPromptUsage(prompt.trim(), response.options.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch scenarios.');
      setSuggestions(DEMO_SCENARIOS);
      setMetadata({ demo: true });
      setStatusMessage('Showing example ranking');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRun(scenario: ScenarioOption) {
    setStatusMessage(`Dispatching ${scenario.title}…`);
    try {
      const run = await runScenario(scenario.scenario_id, {});
      if (typeof window !== 'undefined') {
        const existing = window.localStorage.getItem('runHistory');
        const history = existing ? JSON.parse(existing) : [];
        history.unshift({
          runId: run.run_id,
          scenarioName: scenario.title,
          timestamp: new Date().toISOString()
        });
        window.localStorage.setItem('runHistory', JSON.stringify(history.slice(0, 10)));
      }
      router.push(`/runs/dashboard?id=${run.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to schedule scenario.');
      setStatusMessage('');
    }
  }

  return (
    <div className="container">
      <header>
        <h1 style={{ fontSize: '2.75rem', marginBottom: '0.5rem' }}>Prompt-to-Insight Orchestration</h1>
        <p style={{ maxWidth: '640px', lineHeight: 1.6 }}>
          Compose your investment research intent and we will orchestrate the most relevant multi-modal scenarios—
          streaming status updates from ingestion through modeling so you can act on insights faster.
        </p>
        <p id="helper-copy" style={{ marginTop: '1rem', color: 'rgba(148, 163, 184, 0.9)' }}>
          {helperCopy}
        </p>
      </header>

      <section aria-labelledby="prompt-section">
        <h2 id="prompt-section" className="visually-hidden">
          Prompt input
        </h2>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem', marginTop: '2rem' }} aria-describedby="helper-copy">
          <label className="visually-hidden" htmlFor="prompt-input">
            Prompt text
          </label>
          <input
            id="prompt-input"
            className="prompt"
            type="text"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="e.g. Identify underpriced earnings revisions in US tech"
            aria-required="true"
          />
          <button className="primary" type="submit" disabled={isLoading}>
            {isLoading ? 'Ranking…' : 'Find Scenarios'}
          </button>
        </form>
        <div role="status" aria-live="polite" style={{ minHeight: '1.5rem', marginTop: '0.5rem' }}>
          {statusMessage}
        </div>
        {error && (
          <div role="alert" style={{ color: '#fca5a5', marginTop: '0.5rem' }}>
            {error}
          </div>
        )}
      </section>

      {suggestions.length > 0 && (
        <section aria-labelledby="scenario-section" style={{ marginTop: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
            <h2 id="scenario-section" style={{ margin: 0 }}>
              Ranked scenarios
            </h2>
            <Link href="/runs" className="secondary" aria-label="View historical runs">
              Historical runs
            </Link>
          </div>
          <p style={{ color: 'rgba(148, 163, 184, 0.9)' }}>Select a scenario to open a live dashboard.</p>
          <div className="grid cards-grid" role="list">
            {suggestions.slice(0, MAX_SCENARIOS).map((scenario, index) => (
              <ScenarioCard
                key={scenario.scenario_id}
                scenario={scenario}
                rank={index + 1}
                onRun={handleRun}
              />
            ))}
          </div>
        </section>
      )}

      <HelpContent />
    </div>
  );
}
