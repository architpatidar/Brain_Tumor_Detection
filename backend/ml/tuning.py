"""Simple hyperparameter search utilities."""

from __future__ import annotations

from dataclasses import replace
from itertools import product

from .config import TrainingConfig


def grid_search_configs(base_config: TrainingConfig) -> list[TrainingConfig]:
    """Generate a modest hyperparameter grid for experimentation."""
    learning_rates = [1e-3, 3e-4, 1e-4]
    dropout_rates = [0.2, 0.3, 0.4]
    backbones = ["efficientnetb0", "resnet50"]

    configs: list[TrainingConfig] = []
    for learning_rate, dropout_rate, backbone in product(learning_rates, dropout_rates, backbones):
        configs.append(
            replace(
                base_config,
                learning_rate=learning_rate,
                dropout_rate=dropout_rate,
                base_model=backbone,
            )
        )
    return configs
