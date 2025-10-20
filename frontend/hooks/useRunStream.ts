'use client';

import { useEffect, useState } from 'react';
import { buildStreamUrl, fetchRun } from '../lib/api';
import { RunState } from '../lib/types';

const TERMINAL_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);

export function useRunStream(runId: string | undefined) {
  const [events, setEvents] = useState<RunState[]>([]);
  const [latest, setLatest] = useState<RunState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      return undefined;
    }

    let isCancelled = false;
    let eventSource: EventSource | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let hasOpened = false;

    setEvents([]);
    setLatest(null);
    setError(null);

    const applyUpdate = (data: RunState) => {
      if (isCancelled) return;
      setEvents((prev) => {
        const last = prev[prev.length - 1];
        if (
          last &&
          last.status === data.status &&
          last.timestamp === data.timestamp &&
          last.message === data.message
        ) {
          return prev;
        }
        return [...prev, data];
      });
      setLatest(data);
      setError(null);
      if (TERMINAL_STATUSES.has(data.status)) {
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
      }
    };

    const runPoll = async () => {
      try {
        const snapshot = await fetchRun(runId);
        applyUpdate(snapshot);
        setError(null);
      } catch (err) {
        if (isCancelled) return;
        const message = err instanceof Error ? err.message : 'Unable to refresh run status.';
        setError(message);
      }
    };

    const startPolling = () => {
      if (pollTimer) return;
      pollTimer = setInterval(runPoll, 3000);
      void runPoll();
    };

    fetchRun(runId)
      .then((initial) => {
        applyUpdate(initial);
      })
      .catch((err) => {
        if (isCancelled) return;
        setError(err instanceof Error ? err.message : 'Unable to load run state.');
      });

    if (typeof window !== 'undefined' && 'EventSource' in window) {
      const streamUrl = buildStreamUrl(runId);
      eventSource = new EventSource(streamUrl);

      eventSource.onopen = () => {
        hasOpened = true;
        setError(null);
      };

      eventSource.onmessage = (event) => {
        if (isCancelled) return;
        try {
          const data: RunState = JSON.parse(event.data);
          applyUpdate(data);
        } catch (err) {
          console.warn('Failed to parse event payload', err);
        }
      };

      eventSource.onerror = () => {
        if (isCancelled) return;
        if (!hasOpened) {
          setError('Streaming unavailable. Falling back to periodic refresh.');
          eventSource?.close();
          eventSource = null;
          startPolling();
        } else {
          setError('Connection interrupted. Attempting to reconnect…');
        }
      };
    } else {
      startPolling();
    }

    return () => {
      isCancelled = true;
      if (eventSource) {
        eventSource.close();
      }
      if (pollTimer) {
        clearInterval(pollTimer);
      }
    };
  }, [runId]);

  return { events, latest, error } as const;
}
