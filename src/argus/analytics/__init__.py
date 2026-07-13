"""M4 — Analytics Engine: Criticality metrics and vulnerability analysis."""

from argus.analytics.analyzer import (
    AnalyticsConfig,
    CriticalityAnalyzerImpl,
    load_analytics_config_from_yaml,
)
from argus.analytics.report import generate_report

__all__ = [
    "CriticalityAnalyzerImpl",
    "AnalyticsConfig",
    "load_analytics_config_from_yaml",
    "generate_report",
]
