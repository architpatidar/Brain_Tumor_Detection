"""End-to-end training pipeline for brain tumor classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

try:
    from .config import DatasetConfig, TrainingConfig
    from .datasets import download_http_archive, download_kaggle_dataset, organize_classification_dataset
    from .evaluation import evaluate_predictions, find_best_binary_threshold, save_confusion_matrix, save_report
    from .explainability import make_gradcam_heatmap, save_gradcam
    from .modeling import build_classifier
    from .preprocessing import (
        collect_labeled_files,
        compute_balanced_class_weights,
        create_dataset,
        save_preview_grid,
        split_dataset,
    )
except ImportError:  # pragma: no cover - allows `python backend/ml/train.py`
    from backend.ml.config import DatasetConfig, TrainingConfig
    from backend.ml.datasets import download_http_archive, download_kaggle_dataset, organize_classification_dataset
    from backend.ml.evaluation import evaluate_predictions, find_best_binary_threshold, save_confusion_matrix, save_report
    from backend.ml.explainability import make_gradcam_heatmap, save_gradcam
    from backend.ml.modeling import build_classifier
    from backend.ml.preprocessing import (
        collect_labeled_files,
        compute_balanced_class_weights,
        create_dataset,
        save_preview_grid,
        split_dataset,
    )


def parse_args() -> argparse.Namespace:
    """CLI arguments."""
    parser = argparse.ArgumentParser(description="Train a brain tumor classifier.")
    parser.add_argument("--dataset-dir", type=Path, help="Organized dataset path with class folders.")
    parser.add_argument("--kaggle-dataset", type=str, help="Optional Kaggle dataset slug to download.")
    parser.add_argument("--http-archive", type=str, help="Optional public archive URL to download.")
    parser.add_argument("--base-model", type=str, default="efficientnetb0", choices=["efficientnetb0", "resnet50", "densenet121"])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--fine-tune-epochs", type=int, default=10)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--fine-tune-learning-rate", type=float, default=1e-5)
    parser.add_argument("--dropout-rate", type=float, default=0.3)
    parser.add_argument("--organized-output", type=Path, default=Path("backend/data/organized/brain_tumor"))
    parser.add_argument("--raw-output", type=Path, default=Path("backend/data/raw/brain_tumor"))
    parser.add_argument("--force-download", action="store_true", help="Redownload and reorganize dataset even if cached.")
    return parser.parse_args()


def resolve_dataset(args: argparse.Namespace) -> Path:
    """Download and organize a dataset when requested."""
    project_root = Path(__file__).resolve().parents[2]
    organized_output = (project_root / args.organized_output).resolve() if not args.organized_output.is_absolute() else args.organized_output
    raw_output = (project_root / args.raw_output).resolve() if not args.raw_output.is_absolute() else args.raw_output

    if args.kaggle_dataset:
        raw_dir = download_kaggle_dataset(
            args.kaggle_dataset,
            raw_output,
            force_download=args.force_download,
        )
        return organize_classification_dataset(
            raw_dir,
            organized_output,
            force_rebuild=args.force_download,
        )
    if args.http_archive:
        raw_dir = download_http_archive(
            args.http_archive,
            raw_output,
            force_download=args.force_download,
        )
        return organize_classification_dataset(
            raw_dir,
            organized_output,
            force_rebuild=args.force_download,
        )
    if args.dataset_dir:
        return (project_root / args.dataset_dir).resolve() if not args.dataset_dir.is_absolute() else args.dataset_dir
    raise ValueError("Provide --dataset-dir, --kaggle-dataset, or --http-archive.")


def compile_model(
    model: tf.keras.Model,
    num_classes: int,
    learning_rate: float,
    label_smoothing: float,
) -> None:
    """Compile model with binary or multiclass losses."""
    loss = (
        tf.keras.losses.BinaryCrossentropy(label_smoothing=label_smoothing)
        if num_classes == 2
        else tf.keras.losses.SparseCategoricalCrossentropy(label_smoothing=label_smoothing)
    )
    metrics = [
        tf.keras.metrics.BinaryAccuracy(name="accuracy") if num_classes == 2 else tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy"),
        tf.keras.metrics.Precision(name="precision"),
        tf.keras.metrics.Recall(name="recall"),
        tf.keras.metrics.AUC(name="auc"),
    ]
    model.compile(optimizer=tf.keras.optimizers.AdamW(learning_rate=learning_rate, weight_decay=1e-4), loss=loss, metrics=metrics)


def generate_gradcam_examples(model: tf.keras.Model, file_paths: list[str], image_size: tuple[int, int], output_dir: Path) -> None:
    """Save a few Grad-CAM overlays from held-out samples."""
    for file_path in file_paths[:5]:
        image = tf.keras.utils.load_img(file_path, target_size=image_size)
        image_array = tf.keras.utils.img_to_array(image)
        batch = np.expand_dims(image_array.astype("float32") / 255.0, axis=0)
        heatmap = make_gradcam_heatmap(batch, model)
        save_gradcam(image_array.astype("uint8"), heatmap, output_dir / f"{Path(file_path).stem}_gradcam.png")


def main() -> None:
    """Run training."""
    args = parse_args()
    dataset_dir = resolve_dataset(args)

    dataset_config = DatasetConfig(
        organized_dir=dataset_dir,
        image_size=(args.image_size, args.image_size),
        batch_size=args.batch_size,
    )
    training_config = TrainingConfig(
        base_model=args.base_model,
        epochs=args.epochs,
        fine_tune_epochs=args.fine_tune_epochs,
        learning_rate=args.learning_rate,
        fine_tune_learning_rate=args.fine_tune_learning_rate,
        dropout_rate=args.dropout_rate,
    )

    file_paths, labels, class_names = collect_labeled_files(dataset_config.organized_dir)
    splits = split_dataset(file_paths, labels, dataset_config.val_split, dataset_config.test_split, dataset_config.seed)

    train_dataset = create_dataset(*splits["train"], dataset_config.image_size, dataset_config.batch_size, shuffle=True, augment=True)
    val_dataset = create_dataset(*splits["val"], dataset_config.image_size, dataset_config.batch_size, shuffle=False)
    test_dataset = create_dataset(*splits["test"], dataset_config.image_size, dataset_config.batch_size, shuffle=False)

    save_preview_grid(train_dataset, training_config.output_dir / "preview.png")

    model, backbone = build_classifier(
        image_size=dataset_config.image_size,
        num_classes=len(class_names),
        backbone_name=training_config.base_model,
        dropout_rate=training_config.dropout_rate,
    )
    compile_model(
        model,
        len(class_names),
        training_config.learning_rate,
        training_config.label_smoothing,
    )

    checkpoint_path = training_config.output_dir / "best_model.keras"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
        tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path, monitor="val_loss", save_best_only=True),
    ]

    class_weights = compute_balanced_class_weights(splits["train"][1])
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=training_config.epochs,
        callbacks=callbacks,
        class_weight=class_weights,
    )

    backbone.trainable = True
    for layer in backbone.layers[:-40]:
        layer.trainable = False
    compile_model(
        model,
        len(class_names),
        training_config.fine_tune_learning_rate,
        training_config.label_smoothing / 2,
    )
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=training_config.fine_tune_epochs,
        callbacks=callbacks,
        class_weight=class_weights,
    )

    model = tf.keras.models.load_model(checkpoint_path)
    model.save(training_config.model_export_path)

    val_probabilities = model.predict(val_dataset, verbose=0)
    if val_probabilities.ndim == 1:
        val_probabilities = val_probabilities[:, None]
    val_y_true = np.concatenate([labels.numpy() for _, labels in val_dataset], axis=0)
    decision_threshold = 0.5
    threshold_score = None
    if len(class_names) == 2:
        decision_threshold, threshold_score = find_best_binary_threshold(
            val_y_true,
            val_probabilities[:, 0],
            metric="balanced_accuracy",
        )

    probabilities = model.predict(test_dataset, verbose=0)
    if probabilities.ndim == 1:
        probabilities = probabilities[:, None]

    y_true = np.concatenate([labels.numpy() for _, labels in test_dataset], axis=0)
    report = evaluate_predictions(y_true, probabilities, class_names, threshold=decision_threshold)
    report["validation_threshold_score"] = threshold_score
    save_report(report, training_config.report_path)
    save_confusion_matrix(np.array(report["confusion_matrix"]), class_names, training_config.output_dir / "confusion_matrix.png")
    generate_gradcam_examples(model, splits["test"][0], dataset_config.image_size, training_config.gradcam_dir)

    metadata = {
        "class_names": class_names,
        "image_size": list(dataset_config.image_size),
        "decision_threshold": decision_threshold,
        "base_model": training_config.base_model,
    }
    training_config.model_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    training_config.model_metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Training finished. Exported model to {training_config.model_export_path}")
    print(f"Evaluation report saved to {training_config.report_path}")


if __name__ == "__main__":
    main()
