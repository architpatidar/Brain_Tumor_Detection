"""Grad-CAM explainability utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib.cm as cm
import numpy as np
from PIL import Image
import tensorflow as tf


def find_last_conv_layer(model: tf.keras.Model) -> str:
    """Find the last convolutional layer name."""
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    raise ValueError("No convolutional layer found for Grad-CAM.")


def make_gradcam_heatmap(
    image_tensor: tf.Tensor,
    model: tf.keras.Model,
    last_conv_layer_name: str | None = None,
) -> np.ndarray:
    """Create a Grad-CAM heatmap for a single image tensor."""
    last_conv_layer_name = last_conv_layer_name or find_last_conv_layer(model)
    grad_model = tf.keras.Model(
        inputs=model.inputs,
        outputs=[model.get_layer(last_conv_layer_name).output, model.output],
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(image_tensor)
        if predictions.shape[-1] == 1:
            target = predictions[:, 0]
        else:
            class_index = tf.argmax(predictions[0])
            target = predictions[:, class_index]

    gradients = tape.gradient(target, conv_outputs)
    pooled_gradients = tf.reduce_mean(gradients, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_gradients[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()


def overlay_heatmap(image: np.ndarray, heatmap: np.ndarray, alpha: float = 0.35) -> Image.Image:
    """Overlay a heatmap on top of an image."""
    heatmap = np.uint8(255 * heatmap)
    jet = cm.get_cmap("jet")
    jet_colors = jet(np.arange(256))[:, :3]
    colored_heatmap = jet_colors[heatmap]
    colored_heatmap = tf.keras.utils.array_to_img(colored_heatmap)
    colored_heatmap = colored_heatmap.resize((image.shape[1], image.shape[0]))
    colored_heatmap = tf.keras.utils.img_to_array(colored_heatmap)

    overlay = colored_heatmap * alpha + image
    return tf.keras.utils.array_to_img(overlay)


def save_gradcam(image: np.ndarray, heatmap: np.ndarray, output_path: Path) -> Path:
    """Save a Grad-CAM overlay image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_heatmap(image, heatmap).save(output_path)
    return output_path
