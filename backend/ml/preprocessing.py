"""Data loading, augmentation, and class balancing helpers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import random

import numpy as np
from PIL import Image
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight


VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".dcm"}


def collect_labeled_files(dataset_dir: Path) -> tuple[list[str], list[int], list[str]]:
    """Collect image paths and labels from class-named directories."""
    dataset_dir = Path(dataset_dir)
    class_names = sorted([item.name for item in dataset_dir.iterdir() if item.is_dir()])

    file_paths: list[str] = []
    labels: list[int] = []
    for index, class_name in enumerate(class_names):
        class_dir = dataset_dir / class_name
        for file_path in class_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
                file_paths.append(str(file_path))
                labels.append(index)

    return file_paths, labels, class_names


def split_dataset(
    file_paths: list[str],
    labels: list[int],
    val_split: float,
    test_split: float,
    seed: int,
) -> dict[str, tuple[list[str], list[int]]]:
    """Create stratified train/val/test splits."""
    train_paths, test_paths, train_labels, test_labels = train_test_split(
        file_paths,
        labels,
        test_size=test_split,
        stratify=labels,
        random_state=seed,
    )

    adjusted_val_split = val_split / (1.0 - test_split)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_paths,
        train_labels,
        test_size=adjusted_val_split,
        stratify=train_labels,
        random_state=seed,
    )

    return {
        "train": (train_paths, train_labels),
        "val": (val_paths, val_labels),
        "test": (test_paths, test_labels),
    }


def load_image(path: tf.Tensor, image_size: tuple[int, int]) -> tf.Tensor:
    """Read and normalize image data."""
    image = tf.io.read_file(path)
    image = tf.io.decode_image(image, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, image_size)
    image = tf.cast(image, tf.float32) / 255.0
    return image


def build_augmentation() -> tf.keras.Sequential:
    """Augmentation pipeline for medical images."""
    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal_and_vertical"),
            tf.keras.layers.RandomRotation(0.12),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomTranslation(0.05, 0.05),
            tf.keras.layers.RandomContrast(0.15),
        ],
        name="medical_augmentation",
    )


def create_dataset(
    file_paths: list[str],
    labels: list[int],
    image_size: tuple[int, int],
    batch_size: int,
    shuffle: bool,
    augment: bool = False,
) -> tf.data.Dataset:
    """Create a TensorFlow dataset from file paths."""
    dataset = tf.data.Dataset.from_tensor_slices((file_paths, labels))
    if shuffle:
        dataset = dataset.shuffle(buffer_size=len(file_paths), reshuffle_each_iteration=True)

    dataset = dataset.map(
        lambda path, label: (load_image(path, image_size), tf.cast(label, tf.int32)),
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    if augment:
        augmenter = build_augmentation()
        dataset = dataset.map(
            lambda image, label: (augmenter(image, training=True), label),
            num_parallel_calls=tf.data.AUTOTUNE,
        )

    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def compute_balanced_class_weights(labels: list[int]) -> dict[int, float]:
    """Compute balanced class weights for imbalanced datasets."""
    unique_labels = np.array(sorted(set(labels)))
    weights = compute_class_weight(class_weight="balanced", classes=unique_labels, y=np.array(labels))
    return {int(label): float(weight) for label, weight in zip(unique_labels, weights)}


def save_preview_grid(dataset: tf.data.Dataset, output_path: Path, max_images: int = 9) -> None:
    """Persist a quick visual sanity-check grid."""
    import matplotlib.pyplot as plt

    images, labels = next(iter(dataset.take(1)))
    figure = plt.figure(figsize=(8, 8))
    for index in range(min(max_images, len(images))):
        axis = figure.add_subplot(3, 3, index + 1)
        axis.imshow(images[index].numpy())
        axis.set_title(str(labels[index].numpy()))
        axis.axis("off")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)
