"""Dataset download and organization helpers."""

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

from kaggle.api.kaggle_api_extended import KaggleApi
import requests


def ensure_directory(path: Path) -> Path:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def directory_has_files(path: Path) -> bool:
    """Return True when a directory contains at least one file."""
    path = Path(path)
    if not path.exists():
        return False
    return any(item.is_file() for item in path.rglob("*"))


def download_kaggle_dataset(
    dataset_slug: str,
    output_dir: Path,
    unzip: bool = True,
    force_download: bool = False,
) -> Path:
    """Download a Kaggle dataset using local Kaggle credentials."""
    output_dir = ensure_directory(output_dir)
    if directory_has_files(output_dir) and not force_download:
        print(f"Using cached Kaggle dataset at {output_dir}")
        return output_dir

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(dataset_slug, path=str(output_dir), unzip=unzip, quiet=False)
    return output_dir


def download_http_archive(
    url: str,
    output_dir: Path,
    archive_name: str = "dataset.zip",
    force_download: bool = False,
) -> Path:
    """Download a public archive from an HTTP endpoint."""
    output_dir = ensure_directory(output_dir)
    archive_path = output_dir / archive_name
    if directory_has_files(output_dir) and not force_download:
        print(f"Using cached archive contents at {output_dir}")
        return output_dir

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with archive_path.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file_obj.write(chunk)

    if archive_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(output_dir)

    return output_dir


def organize_classification_dataset(
    source_dir: Path,
    target_dir: Path,
    class_aliases: dict[str, str] | None = None,
    copy_files: bool = True,
    force_rebuild: bool = False,
) -> Path:
    """Normalize a downloaded dataset into class-based folders."""
    source_dir = Path(source_dir)
    target_dir = ensure_directory(Path(target_dir))
    if directory_has_files(target_dir) and not force_rebuild:
        print(f"Using cached organized dataset at {target_dir}")
        return target_dir

    class_aliases = class_aliases or {}
    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".dcm"}

    for class_dir in source_dir.iterdir():
        if not class_dir.is_dir():
            continue

        class_name = class_aliases.get(class_dir.name.lower(), class_dir.name.lower())
        destination = ensure_directory(target_dir / class_name)

        for file_path in class_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in valid_extensions:
                continue

            target_path = destination / file_path.name
            if copy_files:
                shutil.copy2(file_path, target_path)
            else:
                shutil.move(file_path, target_path)

    return target_dir
