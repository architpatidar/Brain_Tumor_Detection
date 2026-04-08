"""Model builders for brain tumor classification."""

from __future__ import annotations

import tensorflow as tf


BACKBONES = {
    "efficientnetb0": (
        tf.keras.applications.EfficientNetB0,
        tf.keras.applications.efficientnet.preprocess_input,
    ),
    "resnet50": (
        tf.keras.applications.ResNet50,
        tf.keras.applications.resnet50.preprocess_input,
    ),
    "densenet121": (
        tf.keras.applications.DenseNet121,
        tf.keras.applications.densenet.preprocess_input,
    ),
}


def build_classifier(
    image_size: tuple[int, int],
    num_classes: int,
    backbone_name: str = "efficientnetb0",
    dropout_rate: float = 0.3,
) -> tuple[tf.keras.Model, tf.keras.Model]:
    """Build a transfer-learning classifier."""
    backbone_cls, preprocess_input = BACKBONES[backbone_name.lower()]

    inputs = tf.keras.Input(shape=(*image_size, 3), name="input_image")
    x = tf.keras.layers.Lambda(preprocess_input, name="backbone_preprocess")(inputs)
    backbone = backbone_cls(include_top=False, weights="imagenet", input_tensor=x)
    backbone.trainable = False

    x = tf.keras.layers.GlobalAveragePooling2D(name="global_pool")(backbone.output)
    x = tf.keras.layers.BatchNormalization(name="global_pool_bn")(x)
    x = tf.keras.layers.Dropout(dropout_rate, name="dropout")(x)
    x = tf.keras.layers.Dense(
        256,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(1e-4),
        name="dense_features",
    )(x)
    x = tf.keras.layers.BatchNormalization(name="dense_features_bn")(x)
    x = tf.keras.layers.Dropout(dropout_rate / 2, name="dense_dropout")(x)

    if num_classes == 2:
        outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="prediction")(x)
    else:
        outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="prediction")(x)

    return tf.keras.Model(inputs=inputs, outputs=outputs, name=f"{backbone_name}_brain_tumor"), backbone
