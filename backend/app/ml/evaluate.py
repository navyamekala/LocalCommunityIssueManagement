"""
Model Evaluation Utilities.
Loads evaluation metrics and allows running tests on custom test datasets.
"""

import os
import json
from typing import Dict, Any


def get_evaluation_metrics(metrics_dir: str = None) -> Dict[str, Any]:
    """Retrieves the saved genuine test evaluation metrics and training report."""
    if metrics_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        metrics_dir = os.path.join(base_dir, "ml_artifacts", "metrics")
        report_dir = os.path.join(base_dir, "ml_artifacts", "training_reports")

    metrics_file = os.path.join(metrics_dir, "test_metrics.json")
    report_file = os.path.join(report_dir, "training_report.json")

    metrics_data = {}
    report_data = {}

    if os.path.exists(metrics_file):
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)

    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            report_data = json.load(f)

    return {
        "metrics": metrics_data,
        "training_report": report_data
    }
