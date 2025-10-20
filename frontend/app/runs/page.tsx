'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

interface RunHistoryEntry {
  runId: string;
  scenarioName: string;
  timestamp: string;
}

export default function RunsLandingPage() {
  const [history, setHistory] = useState<RunHistoryEntry[]>([]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const existing = window.localStorage.getItem('runHistory');
    if (!existing) return;
    try {
      const parsed = JSON.parse(existing) as RunHistoryEntry[];
      setHistory(parsed);
    } catch (error) {
      console.warn('Unable to parse run history', error);
    }
  }, []);

  return (
    <div className="container">
      <h1>Recent runs</h1>
      <p>Jump back into an orchestration dashboard or launch a fresh prompt.</p>
      {history.length === 0 ? (
        <p>No local run history yet. Start from the <Link href="/">landing page</Link> to schedule one.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, marginTop: '2rem', display: 'grid', gap: '1rem' }}>
          {history.map((item) => (
            <li
              key={item.runId}
              className="card"
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <h3 style={{ margin: 0 }}>{item.scenarioName}</h3>
                <p style={{ margin: '0.5rem 0 0' }}>{new Date(item.timestamp).toLocaleString()}</p>
              </div>
              <Link
                href={{ pathname: '/runs/dashboard', query: { id: item.runId } }}
                className="primary"
                style={{ textDecoration: 'none' }}
              >
                View dashboard
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
