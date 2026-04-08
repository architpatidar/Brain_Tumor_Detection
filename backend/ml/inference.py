"""Inference integration for the Flask backend."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pydicom
import tensorflow as tf

from .config import InferenceConfig
from .explainability import make_gradcam_heatmap, save_gradcam


class ModelNotReadyError(RuntimeError):
    """Raised when inference is requested before a model exists."""


class BrainTumorPredictor:
    """Lazy-loading predictor for project integration."""

    def __init__(self, config: InferenceConfig | None = None) -> None:
        self.config = config or InferenceConfig()
        self._model: tf.keras.Model | None = None
        self._metadata_loaded = False

    @property
    def model(self) -> tf.keras.Model:
        """Load model lazily."""
        if self._model is None:
            if not self.config.model_path.exists():
                raise ModelNotReadyError(
                    f"Trained model not found at {self.config.model_path}. Run backend/ml/train.py first."
                )
            self._model = tf.keras.models.load_model(self.config.model_path)
            self._load_metadata()
        return self._model

    def _load_metadata(self) -> None:
        """Load calibration metadata saved during training."""
        if self._metadata_loaded:
            return
        if self.config.metadata_path.exists():
            payload = json.loads(self.config.metadata_path.read_text(encoding="utf-8"))
            if payload.get("class_names"):
                self.config.class_names = tuple(payload["class_names"])
            if payload.get("image_size"):
                self.config.image_size = tuple(payload["image_size"])
            if payload.get("decision_threshold") is not None:
                self.config.confidence_threshold = float(payload["decision_threshold"])
        self._metadata_loaded = True

    def _read_image(self, image_path: str | Path) -> np.ndarray:
        """Read standard image or DICOM image."""
        image_path = Path(image_path)
        if image_path.suffix.lower() == ".dcm":
            dataset = pydicom.dcmread(str(image_path))
            pixels = dataset.pixel_array.astype(np.float32)
            pixels -= pixels.min()
            pixels /= max(pixels.max(), 1.0)
            image = np.stack([pixels, pixels, pixels], axis=-1)
            image = (image * 255).astype(np.uint8)
        else:
            image = np.array(Image.open(image_path).convert("RGB"))
        return image

    def preprocess(self, image_path: str | Path) -> tuple[np.ndarray, np.ndarray]:
        """Prepare input batch for the classifier."""
        original = self._read_image(image_path)
        resized = tf.image.resize(original, self.config.image_size).numpy().astype("float32") / 255.0
        batch = np.expand_dims(resized, axis=0)
        return original, batch

    def predict_probabilities(self, batch: np.ndarray) -> np.ndarray:
        """Run model prediction with optional lightweight test-time augmentation."""
        predictions = [self.model.predict(batch, verbose=0)]
        if self.config.use_tta:
            flipped_lr = np.flip(batch, axis=2)
            flipped_ud = np.flip(batch, axis=1)
            predictions.append(self.model.predict(flipped_lr, verbose=0))
            predictions.append(self.model.predict(flipped_ud, verbose=0))
        return np.mean(predictions, axis=0)

    def predict(self, image_path: str | Path) -> dict:
        """Run a prediction and return the existing app response shape."""
        original, batch = self.preprocess(image_path)
        probabilities = self.predict_probabilities(batch)

        if probabilities.shape[-1] == 1:
            tumor_probability = float(probabilities[0][0])
            detected = tumor_probability >= self.config.confidence_threshold
            tumor_type = "Tumor" if detected else None
        else:
            class_index = int(np.argmax(probabilities[0]))
            class_name = self.config.class_names[class_index]
            tumor_probability = float(probabilities[0][class_index])
            detected = class_name != "no_tumor"
            tumor_type = class_name.replace("_", " ").title() if detected else None

        confidence = round(tumor_probability * 100, 2)
        severity = "None" if not detected else ("Severe" if confidence >= 90 else "Moderate" if confidence >= 75 else "Mild")
        recommendation = (
            "No tumor detected. Regular follow-up advised."
            if not detected
            else "Tumor indicators detected. Please review with a qualified radiologist or neurologist."
        )

        heatmap = make_gradcam_heatmap(batch, self.model)
        explainability_path = save_gradcam(
            original,
            heatmap,
            Path(image_path).with_name(f"{Path(image_path).stem}_gradcam.png"),
        )

        return {
            "detected": detected,
            "confidence": confidence,
            "severity": severity,
            "tumor_type": tumor_type,
            "recommendation": recommendation,
            "explainability_image": str(explainability_path),
        }


def ensemble_probabilities(models: list[tf.keras.Model], batch: np.ndarray) -> np.ndarray:
    """Average probabilities across multiple trained models."""
    predictions = [model.predict(batch, verbose=0) for model in models]
    return np.mean(predictions, axis=0)
