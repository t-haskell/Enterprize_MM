'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { RunTimeline } from '../../../components/RunTimeline';
import { useRunStream } from '../../../hooks/useRunStream';

export default function RunDashboardPage() {
  const params = useParams<{ id?: string | string[] }>();
  const router = useRouter();
  const runId = Array.isArray(params?.id) ? params?.id?.[0] : params?.id;
  const { events, latest, error } = useRunStream(runId);

  useEffect(() => {
    if (!runId) {
      router.replace('/');
    }
  }, [runId, router]);

  if (!runId) {
    return null;
  }

  return (
    <div className="container">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.5rem' }}>Run dashboard</h1>
          <p style={{ margin: 0, color: 'rgba(148, 163, 184, 0.9)' }}>Monitoring orchestration lifecycle for run {runId}</p>
        </div>
        <Link href="/" className="secondary">
          New prompt
        </Link>
      </header>

      <section style={{ marginTop: '2rem' }} className="run-grid">
        <article className="card">
          <h2>Status</h2>
          <p>
            Current state:{' '}
            <span className={`status-badge ${latest?.status ?? 'queued'}`}>
              {latest?.status ?? 'queued'}
            </span>
          </p>
          <p>Message: {latest?.message ?? 'Waiting for updates from orchestrator…'}</p>
          {error && (
            <p role="alert" style={{ color: '#fca5a5' }}>
              {error}
            </p>
          )}
        </article>

        <article className="card">
          <h2>Scenario metadata</h2>
          <div className="table-list">
            <dl>
              <dt>Scenario</dt>
              <dd>{latest?.scenario_id ?? '—'}</dd>
            </dl>
            <dl>
              <dt>Parameters</dt>
              <dd>
                <pre className="result-block" aria-label="Scenario parameters">
                  {JSON.stringify(latest?.parameters ?? {}, null, 2)}
                </pre>
              </dd>
            </dl>
          </div>
        </article>

        <article className="card" style={{ gridColumn: '1 / -1' }}>
          <h2>Result payload</h2>
          {latest?.result ? (
            <pre className="result-block" aria-label="Scenario result">
              {JSON.stringify(latest.result, null, 2)}
            </pre>
          ) : (
            <p>No result yet. Results appear once the modeling service returns payloads.</p>
          )}
        </article>
      </section>

      <section style={{ marginTop: '2rem' }}>
        <RunTimeline events={events} />
      </section>
    </div>
  );
}
