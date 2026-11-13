
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from src.ml.anomaly_detector import AstronautAnomalyDetector
from src.simulation.vitals_generator import generate_vitals_series


# Make the experiment reproducible
np.random.seed(42)


# Astronaut baseline information
astronaut = {
    "id": 1,
    "name": "Test Astronaut",
    "baseline_hr": 70.0,
    "baseline_spo2": 98.0,
    "baseline_bp_sys": 118.0,
    "baseline_bp_dia": 76.0,
    "baseline_temp": 36.8,
    "baseline_rr": 14.0,
    "baseline_hrv": 55.0
}


# --------------------------------------------------
# STEP 1: GENERATE NOMINAL TRAINING DATA
# --------------------------------------------------

print("Generating nominal training data...")

training_data = generate_vitals_series(
    astronaut=astronaut,
    count=200,
    interval_seconds=10,
    anomaly_mode="NOMINAL"
)

print("Training samples:", len(training_data))


# --------------------------------------------------
# STEP 2: TRAIN ISOLATION FOREST MODEL
# --------------------------------------------------

print("\nTraining Isolation Forest model...")

detector = AstronautAnomalyDetector(
    contamination=0.05,
    random_state=42
)

trained = detector.train(training_data)

if not trained:
    print("Model training failed!")
    raise SystemExit

print("Model trained successfully!")
print("Training samples:", detector.training_sample_count)


# --------------------------------------------------
# STEP 3: GENERATE NOMINAL TEST DATA
# --------------------------------------------------

print("\nGenerating nominal test data...")

nominal_test_data = generate_vitals_series(
    astronaut=astronaut,
    count=100,
    interval_seconds=10,
    anomaly_mode="NOMINAL"
)

print("Nominal test samples:", len(nominal_test_data))


# --------------------------------------------------
# STEP 4: GENERATE SCENARIO TEST DATA
# --------------------------------------------------

scenarios = [
    "HYPOXIA",
    "TACHYCARDIA_ARRHYTHMIA",
    "HEAT_STRESS",
    "EVA_EXERTION"
]

test_datasets = {}

print("\nGenerating scenario test data...")

for scenario in scenarios:

    test_data = generate_vitals_series(
        astronaut=astronaut,
        count=100,
        interval_seconds=10,
        anomaly_mode=scenario
    )

    test_datasets[scenario] = test_data

    print(scenario, ":", len(test_data), "readings generated")


# --------------------------------------------------
# STEP 5: EVALUATE EACH SCENARIO
# --------------------------------------------------

print("\n========== SCENARIO EVALUATION ==========")

for scenario, test_data in test_datasets.items():

    # Combine nominal readings with scenario readings
    combined_test_data = nominal_test_data + test_data

    # Get model predictions
    predictions = detector.predict_series(combined_test_data)

    # Actual labels
    y_true = [
        int(reading.get("anomaly_flag", 0))
        for reading in combined_test_data
    ]

    # Predicted labels
    y_pred = [
        int(reading["ml_is_anomaly"])
        for reading in predictions
    ]

    # Calculate evaluation metrics
    accuracy = accuracy_score(y_true, y_pred)

    precision = precision_score(
        y_true, y_pred, zero_division=0
    )

    recall = recall_score(
        y_true, y_pred, zero_division=0
    )

    f1 = f1_score(
        y_true, y_pred, zero_division=0
    )

    # Confusion matrix
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    )

    tn, fp, fn, tp = matrix.ravel()

    # Calculate specificity and false positive rate
    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0 else 0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0 else 0
    )

    # Display results
    print("\nScenario:", scenario)

    print("Accuracy:", round(accuracy * 100, 2), "%")
    print("Precision:", round(precision * 100, 2), "%")
    print("Recall:", round(recall * 100, 2), "%")
    print("F1-score:", round(f1 * 100, 2), "%")

    print("Specificity:", round(specificity * 100, 2), "%")
    print(
        "False Positive Rate:",
        round(false_positive_rate * 100, 2),
        "%"
    )

    print("Confusion Matrix:")
    print(matrix)

    # EVA has no actual anomaly-positive samples
    if sum(y_true) == 0:
        print(
            "Note: This scenario contains no labelled anomalies. "
            "Precision, recall and F1 are not meaningful "
            "as emergency-detection metrics here."
        )

    print("----------------------------------------")


print("\nScenario evaluation completed!")
