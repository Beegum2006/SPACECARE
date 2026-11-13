"""Backward-compatible import path for the SPACECARE anomaly detector.

The implementation lives in anomaly_detector.py so the project has one
canonical model class rather than two competing implementations.
"""

from src.ml.anomaly_detector import AstronautAnomalyDetector

__all__ = ["AstronautAnomalyDetector"]
