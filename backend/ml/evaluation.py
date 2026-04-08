"""Model evaluation helpers."""

from __future__ import annotations

from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def find_best_binary_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    metric: str = "f1",
) -> tuple[float, float]:
    """Select a binary decision threshold on validation data."""
    best_threshold = 0.5
    best_score = -1.0
    for threshold in np.linspace(0.2, 0.8, 25):
        y_pred = (probabilities >= threshold).astype(int)
        if metric == "balanced_accuracy":
            conf_matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
            specificity = compute_specificity(conf_matrix)
            sensitivity = recall_score(y_true, y_pred, zero_division=0)
            score = (specificity + sensitivity) / 2.0
        else:
            score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_score:
            best_threshold = float(threshold)
            best_score = float(score)
    return best_threshold, best_score


def compute_specificity(conf_matrix: np.ndarray) -> float:
    """Compute binary specificity from a confusion matrix."""
    if conf_matrix.shape != (2, 2):
        return float("nan")
    tn, fp, _, _ = conf_matrix.ravel()
    return float(tn / max(tn + fp, 1))


def evaluate_predictions(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    class_names: list[str],
    threshold: float = 0.5,
) -> dict:
    """Compute classification metrics."""
    binary = len(class_names) == 2
    if binary:
        y_pred = (probabilities[:, 0] >= threshold).astype(int)
        roc_auc = roc_auc_score(y_true, probabilities[:, 0])
    else:
        y_pred = np.argmax(probabilities, axis=1)
        roc_auc = roc_auc_score(y_true, probabilities, multi_class="ovr", average="macro")

    conf_matrix = confusion_matrix(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="binary" if binary else "macro", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="binary" if binary else "macro", zero_division=0)),
        "specificity": compute_specificity(conf_matrix),
        "f1_score": float(f1_score(y_true, y_pred, average="binary" if binary else "macro", zero_division=0)),
        "roc_auc": float(roc_auc),
        "decision_threshold": float(threshold),
        "confusion_matrix": conf_matrix.tolist(),
        "class_names": class_names,
    }


def save_confusion_matrix(conf_matrix: np.ndarray, class_names: list[str], output_path: Path) -> Path:
    """Save a confusion matrix figure."""
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.imshow(conf_matrix, cmap="Blues")
    axis.set_xticks(range(len(class_names)))
    axis.set_xticklabels(class_names, rotation=45, ha="right")
    axis.set_yticks(range(len(class_names)))
    axis.set_yticklabels(class_names)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")

    for row_index in range(conf_matrix.shape[0]):
        for col_index in range(conf_matrix.shape[1]):
            axis.text(col_index, row_index, conf_matrix[row_index, col_index], ha="center", va="center")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
    return output_path


def save_report(report: dict, output_path: Path) -> Path:
    """Persist a JSON evaluation report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(report, file_obj, indent=2)
    return output_path
