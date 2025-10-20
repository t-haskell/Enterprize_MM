export function HelpContent() {
  return (
    <section aria-labelledby="help-heading" className="help-section">
      <div className="container">
        <h2 id="help-heading">Need a hand?</h2>
        <p>Explore the questions below or hover the ℹ️ icons throughout the UI for contextual hints.</p>
        <div className="grid" style={{ marginTop: '1.5rem' }}>
          <details>
            <summary>How are scenarios ranked?</summary>
            <p>
              We normalise the prompt, match scenario keywords, and compute a deterministic cosine score.
              LLM reranking metadata is displayed when available.
            </p>
          </details>
          <details>
            <summary>What happens after I run a scenario?</summary>
            <p>
              The orchestrator schedules a job, streams live state changes, and persists final artefacts once the
              modeling engine completes execution. Watch the run dashboard for updates.
            </p>
          </details>
          <details>
            <summary>Where does the data originate?</summary>
            <p>
              Market, fundamental, macroeconomic, and sentiment signals feed each scenario via the ingestion service.
              Synthetic data is used locally until vendor credentials are configured.
            </p>
          </details>
        </div>
      </div>
    </section>
  );
}
