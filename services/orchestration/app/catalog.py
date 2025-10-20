"""Scenario catalog metadata used for ranking and presentation."""
from __future__ import annotations

from typing import Dict, List

from .embeddings import get_embedder
from .models import ScenarioSpec

_EMBEDDER = get_embedder()


def _spec(**kwargs) -> ScenarioSpec:
    keywords = kwargs["keywords"]
    narrative = " ".join(
        [
            kwargs["title"],
            kwargs["short_description"],
            kwargs["rationale"],
            " ".join(kwargs.get("methodology", [])),
            " ".join(kwargs.get("deliverables", [])),
            " ".join(keywords),
        ]
    )
    embedding = _EMBEDDER.embed_text(narrative)
    return ScenarioSpec(embedding=embedding, **kwargs)


SCENARIO_CATALOG: Dict[str, ScenarioSpec] = {
    "quant_factor": _spec(
        scenario_id="quant_factor",
        title="Quant Factor Screen (Value/Quality/Momentum)",
        short_description="Composite factor scoring with optional ML ranking",
        rationale="Blend valuation, quality, and momentum for robust alpha sourcing.",
        inputs=["universe", "lookback", "weights"],
        methodology=[
            "Normalize EV/EBITDA, FCF yield, ROIC, accruals, and momentum via z-scores",
            "Combine using configurable weights and optional XGBoost ranker",
            "Generate composite ranks and backtest metrics",
        ],
        deliverables=["Top-N tickers", "Factor attribution", "Backtest KPIs (CAGR, Sharpe, max drawdown)"],
        keywords=["value", "quality", "momentum", "factors", "quant", "z-score", "backtest"],
        tags=["equities", "systematic", "fundamental"],
        eligibility_tags=["suitable_long_only"],
    ),
    "trend_strength": _spec(
        scenario_id="trend_strength",
        title="Trend & Relative Strength",
        short_description="Trend filters with relative strength overlays",
        rationale="Identify leaders by combining trend confirmation with RS rankings.",
        inputs=["universe", "ma_windows", "rs_window"],
        methodology=[
            "Apply SMA(50/200) or configurable moving averages",
            "Compute relative strength percentile versus universe",
            "Incorporate volatility scaling and Kelly fraction guardrails",
        ],
        deliverables=["Trend-qualified tickers", "RS leaderboard", "Position size guidance"],
        keywords=["trend", "momentum", "relative strength", "moving average", "kelly"],
        tags=["equities", "technical", "momentum"],
        eligibility_tags=["suitable_long_only"],
    ),
    "earnings_momentum": _spec(
        scenario_id="earnings_momentum",
        title="Earnings Momentum & Revisions",
        short_description="Capture post-earnings drift and analyst revisions",
        rationale="Earnings-related signals have persistent short-term alpha.",
        inputs=["earnings_window", "revision_thresholds"],
        methodology=[
            "Filter tickers with upcoming or recent earnings",
            "Score analyst revisions and surprises",
            "Apply logistic beat/raise model for probability weighting",
        ],
        deliverables=["Pre/post earnings watchlist", "Signal diagnostics", "Event calendar"],
        keywords=["earnings", "revisions", "post-earnings drift", "logistic"],
        tags=["equities", "event", "fundamental"],
        eligibility_tags=["suitable_long_only"],
    ),
    "lightweight_dcf": _spec(
        scenario_id="lightweight_dcf",
        title="Lightweight DCF & Margin-of-Safety",
        short_description="Scenario-based discounted cash-flow valuation",
        rationale="Monte Carlo on growth/WACC bands to estimate fair value distribution.",
        inputs=["revenue_growth", "fcf_growth", "wacc", "terminal"],
        methodology=[
            "Model base/bull/bear cash-flow growth paths",
            "Discount using WACC bands and terminal multiples",
            "Generate fair value distribution via Monte Carlo",
        ],
        deliverables=["Margin-of-safety vs price", "Sensitivity tornado", "Undervalued list"],
        keywords=["dcf", "valuation", "margin of safety", "monte carlo"],
        tags=["equities", "valuation", "fundamental"],
        eligibility_tags=["suitable_long_only"],
    ),
    "dividend_growth": _spec(
        scenario_id="dividend_growth",
        title="Dividend-Growth Defensives",
        short_description="Screen for durable dividend growers",
        rationale="Balance income stability with balance-sheet strength.",
        inputs=["min_years", "payout_cap", "leverage_cap"],
        methodology=[
            "Filter companies with >= min years of dividend raises",
            "Ensure FCF payout < cap and leverage within limits",
            "Overlay quality metrics for resilience",
        ],
        deliverables=["Dividend safety scorecard", "Durable yield candidates"],
        keywords=["dividend", "defensive", "income", "quality", "payout"],
        tags=["equities", "income", "defensive"],
        eligibility_tags=["suitable_income"],
    ),
    "macro_regime": _spec(
        scenario_id="macro_regime",
        title="Macro-Regime Tilt",
        short_description="Regime-aware allocation suggestions",
        rationale="Align exposures with probabilistic macro regimes.",
        inputs=["macro_views", "risk_budget"],
        methodology=[
            "Estimate regimes via HMM/Markov-switching",
            "Map sectors/ETFs to regimes",
            "Blend with Black-Litterman for portfolio tilt",
        ],
        deliverables=["Regime map", "Suggested tilts", "Stress tests"],
        keywords=["macro", "regime", "allocation", "black-litterman", "stress"],
        tags=["multi-asset", "macro", "allocation"],
        eligibility_tags=["portfolio_construction"],
    ),
    "nlp_sentiment": _spec(
        scenario_id="nlp_sentiment",
        title="News & Social Sentiment (NLP)",
        short_description="FinBERT-driven sentiment analytics",
        rationale="Rapidly contextualise news velocity and anomalies.",
        inputs=["sources", "decay"],
        methodology=[
            "Ingest headlines/social feeds",
            "Score sentiment via FinBERT with velocity/acceleration",
            "Flag anomalies and catalysts",
        ],
        deliverables=["Sentiment-ranked tickers", "Why-now snippets", "Risk flags"],
        keywords=["sentiment", "nlp", "finbert", "news", "social"],
        tags=["equities", "nlp", "alternative_data"],
        eligibility_tags=["suitable_long_only"],
    ),
    "insider_buybacks": _spec(
        scenario_id="insider_buybacks",
        title="Insider Buying & Buybacks",
        short_description="Blend insider activity with capital returns",
        rationale="Identify conviction via ownership and repurchase signals.",
        inputs=["net_buys", "buyback_yield"],
        methodology=[
            "Aggregate insider transactions",
            "Combine with buyback yield thresholds",
            "Run valuation sanity checks",
        ],
        deliverables=["Capital-return shortlist", "Float shrink trajectory"],
        keywords=["insider", "buybacks", "capital return"],
        tags=["equities", "capital_allocation"],
        eligibility_tags=["suitable_long_only"],
    ),
    "theme_basket": _spec(
        scenario_id="theme_basket",
        title="Secular Theme Basket",
        short_description="Curate theme baskets with HRP weighting",
        rationale="Systematically surface thematic exposures.",
        inputs=["theme_keywords", "exposure_threshold", "moat_filters"],
        methodology=[
            "Text-mine filings and transcripts for theme alignment",
            "Filter on quality/growth metrics",
            "Allocate using Hierarchical Risk Parity",
        ],
        deliverables=["Theme basket", "Holdings rationale", "Overlap map"],
        keywords=["theme", "hrp", "basket", "moat"],
        tags=["equities", "thematic", "portfolio"],
        eligibility_tags=["portfolio_construction"],
    ),
    "pair_trade": _spec(
        scenario_id="pair_trade",
        title="Hedged Single-Name (Pair Trade)",
        short_description="Construct long/short pair trades",
        rationale="Neutralise factor bets with hedge selection.",
        inputs=["target", "hedge_universe", "beta_window"],
        methodology=[
            "Estimate rolling beta and cointegration",
            "Size long/short legs to neutralise exposures",
            "Define entry/exit risk rules",
        ],
        deliverables=["Trade pair", "Hedge ratio", "Risk rules"],
        keywords=["pair trade", "hedge", "cointegration", "beta"],
        tags=["equities", "hedging", "long_short"],
        eligibility_tags=["hedging", "advanced_derivatives"],
        requires_accreditation=True,
    ),
    "smart_beta": _spec(
        scenario_id="smart_beta",
        title="Core Index + Smart-Beta Tilt",
        short_description="Blend core exposures with factor tilts",
        rationale="Target alpha within tracking-error budgets.",
        inputs=["core_etf", "factor_tilt", "max_tracking_error"],
        methodology=[
            "Optimise mean-variance with TE constraint",
            "Alternative ERC/HRP weighting options",
            "Report TE vs alpha trade-offs",
        ],
        deliverables=["Core-satellite weights", "Risk contributions", "Scenario analysis"],
        keywords=["smart beta", "tracking error", "erc", "portfolio"],
        tags=["multi-asset", "portfolio", "allocation"],
        eligibility_tags=["portfolio_construction"],
    ),
    "dca_planner": _spec(
        scenario_id="dca_planner",
        title="DCA Planner with Regime-Aware Overlays",
        short_description="Plan dollar-cost averaging with guardrails",
        rationale="Overlay valuation/volatility cues on systematic contributions.",
        inputs=["cadence", "cashflows", "drawdown_triggers"],
        methodology=[
            "Construct baseline DCA schedule",
            "Adjust contributions via valuation or volatility overlays",
            "Apply risk guardrails for drawdown triggers",
        ],
        deliverables=["Schedule", "Conditional tilts", "Risk guardrails"],
        keywords=["dca", "planner", "regime", "volatility", "valuation"],
        tags=["multi-asset", "planning", "retail"],
        eligibility_tags=["suitable_income", "portfolio_construction"],
        restricted_regions=["SG"],
    ),
}


def scenario_specs() -> List[ScenarioSpec]:
    return list(SCENARIO_CATALOG.values())
