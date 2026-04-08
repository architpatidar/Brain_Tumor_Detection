"""Shared configuration for the brain tumor ML pipeline."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
ML_DIR = ROOT_DIR / "ml"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"


@dataclass(slots=True)
class DatasetConfig:
    """Dataset and preprocessing settings."""

    dataset_name: str = "brain_tumor"
    raw_dir: Path = field(default_factory=lambda: DATA_DIR / "raw")
    organized_dir: Path = field(default_factory=lambda: DATA_DIR / "organized")
    image_size: Tuple[int, int] = (224, 224)
    batch_size: int = 16
    seed: int = 42
    val_split: float = 0.15
    test_split: float = 0.15


@dataclass(slots=True)
class TrainingConfig:
    """Training and optimization settings."""

    base_model: str = "efficientnetb0"
    epochs: int = 20
    fine_tune_epochs: int = 10
    learning_rate: float = 3e-4
    fine_tune_learning_rate: float = 1e-5
    dropout_rate: float = 0.3
    label_smoothing: float = 0.05
    mixed_precision: bool = False
    output_dir: Path = field(default_factory=lambda: ARTIFACTS_DIR / "training_runs")
    model_export_path: Path = field(default_factory=lambda: MODELS_DIR / "brain_tumor_classifier.keras")
    model_metadata_path: Path = field(default_factory=lambda: MODELS_DIR / "brain_tumor_classifier.metadata.json")
    report_path: Path = field(default_factory=lambda: ARTIFACTS_DIR / "latest_report.json")
    gradcam_dir: Path = field(default_factory=lambda: ARTIFACTS_DIR / "gradcam")


@dataclass(slots=True)
class InferenceConfig:
    """Inference-time settings."""

    model_path: Path = field(
        default_factory=lambda: Path(os.environ.get("MODEL_PATH", MODELS_DIR / "brain_tumor_classifier.keras"))
    )
    metadata_path: Path = field(
        default_factory=lambda: Path(os.environ.get("MODEL_METADATA_PATH", MODELS_DIR / "brain_tumor_classifier.metadata.json"))
    )
    class_names: Tuple[str, ...] = field(
        default_factory=lambda: tuple(
            part.strip() for part in os.environ.get("MODEL_CLASSES", "no_tumor,tumor").split(",")
        )
    )
    image_size: Tuple[int, int] = (224, 224)
    confidence_threshold: float = 0.5
    use_tta: bool = True
