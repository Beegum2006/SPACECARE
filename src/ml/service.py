"""Database-backed ML workflow used by the SPACECARE dashboard."""

from typing import Any, Dict, List, Optional

from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
from sklearn.model_selection import train_test_split

from src.database.queries import get_vitals_history
from src.ml.anomaly_detector import AstronautAnomalyDetector
from src.simulation.vitals_generator import generate_vitals_series, generate_vitals_snapshot

MIN_TRAINING_SAMPLES = 10


def _is_labeled_anomaly(reading: Dict[str, Any]) -> bool:
    try:
        return int(reading.get("anomaly_flag", 0)) == 1
    except (TypeError, ValueError):
        return False


def evaluate_detector(
    readings: List[Dict[str, Any]],
    contamination: float = 0.05,
    random_state: int = 42,
) -> Optional[Dict[str, Any]]:
    """Evaluate on held-out nominal rows plus labeled anomaly rows.

    The model is trained only on a split of nominal rows. Anomaly labels are
    used only for evaluation, never as model input features.
    """
    nominal = [row for row in readings if not _is_labeled_anomaly(row)]
    anomalies = [row for row in readings if _is_labeled_anomaly(row)]
    if len(nominal) < MIN_TRAINING_SAMPLES or not anomalies:
        return None

    train_rows, held_out_nominal = train_test_split(
        nominal,
        test_size=0.30,
        random_state=random_state,
    )
    evaluator = AstronautAnomalyDetector(
        contamination=contamination,
        random_state=random_state,
    )
    if not evaluator.train(train_rows):
        return None

    evaluation_rows = held_out_nominal + anomalies
    predictions = evaluator.predict_series(evaluation_rows)
    y_true = [1 if _is_labeled_anomaly(row) else 0 for row in evaluation_rows]
    y_pred = [row["ml_is_anomaly"] for row in predictions]
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])

    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "true_negative": int(matrix[0, 0]),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
        "true_positive": int(matrix[1, 1]),
        "training_samples": len(train_rows),
        "test_samples": len(evaluation_rows),
        "test_anomalies": len(anomalies),
    }


def analyze_astronaut(
    astronaut: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
    contamination: float = 0.05,
) -> Dict[str, Any]:
    """Train on nominal telemetry and predict the astronaut's latest reading."""
    if history is None:
        history = get_vitals_history(astronaut["id"], limit=5000)

    nominal_rows = [row for row in history if not _is_labeled_anomaly(row)]
    evaluation = evaluate_detector(history, contamination=contamination)

    detector = AstronautAnomalyDetector(contamination=contamination)
    if len(nominal_rows) >= MIN_TRAINING_SAMPLES:
        training_rows = nominal_rows
        training_source = "SQLite nominal telemetry"
    else:
        training_rows = generate_vitals_series(
            astronaut=astronaut,
            count=100,
            interval_seconds=10,
            anomaly_mode="NOMINAL",
        )
        training_source = "Synthetic nominal baseline (cold start)"

    trained = detector.train(training_rows)
    if not trained:
        raise RuntimeError("Unable to train the Isolation Forest model with available baseline data.")

    if history:
        latest_reading = history[-1]
        latest_source = "SQLite telemetry"
    else:
        latest_reading = generate_vitals_snapshot(astronaut, anomaly_mode="NOMINAL")
        latest_source = "Synthetic sample (no database telemetry yet)"

    prediction = detector.predict(latest_reading)
    return {
        "detector": detector,
        "prediction": prediction,
        "latest_reading": latest_reading,
        "latest_source": latest_source,
        "training_source": training_source,
        "training_samples": len(training_rows),
        "history": history,
        "evaluation": evaluation,
    }
