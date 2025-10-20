'use client';

import { useEffect, useMemo, useState } from 'react';
import { RunState } from '../lib/types';

interface RunTimelineProps {
  events: RunState[];
}

export function RunTimeline({ events }: RunTimelineProps) {
  const [expanded, setExpanded] = useState(true);

  const sorted = useMemo(() => {
    return [...events].sort((a, b) => {
      const tsA = typeof a.timestamp === 'string' ? Date.parse(a.timestamp) : 0;
      const tsB = typeof b.timestamp === 'string' ? Date.parse(b.timestamp) : 0;
      return tsA - tsB;
    });
  }, [events]);

  useEffect(() => {
    setExpanded(true);
  }, [events.length]);

  if (!events.length) {
    return null;
  }

  return (
    <section aria-label="Run timeline">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Event Log</h3>
        <button type="button" className="secondary" onClick={() => setExpanded((prev) => !prev)}>
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </header>
      {expanded && (
        <ol style={{ listStyle: 'none', paddingLeft: 0, marginTop: '1rem' }}>
          {sorted.map((event, index) => (
            <li
              key={`${event.status}-${index}`}
              style={{
                borderLeft: '2px solid rgba(56, 189, 248, 0.4)',
                paddingLeft: '1rem',
                marginBottom: '1rem'
              }}
            >
              <div className={`status-badge ${event.status}`}>{event.status}</div>
              <p style={{ margin: '0.5rem 0' }}>{event.message}</p>
              {event.timestamp && (
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'rgba(148, 163, 184, 0.8)' }}>
                  {new Date(event.timestamp as string).toLocaleTimeString()}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
