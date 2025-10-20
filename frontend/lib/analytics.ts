interface PromptAnalyticsPayload {
  prompt: string;
  scenarioCount: number;
  timestamp: string;
}

export async function logPromptUsage(prompt: string, scenarioCount: number): Promise<void> {
  const payload: PromptAnalyticsPayload = {
    prompt,
    scenarioCount,
    timestamp: new Date().toISOString()
  };

  try {
    await fetch('/api/analytics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (error) {
    console.warn('Failed to send analytics payload', error);
  }
}
