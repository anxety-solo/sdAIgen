""" CivitAI API: Model Resolution, Preview & Metadata | by ANXETY """

import requests
import json
import io
import os
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from PIL import Image

# === SDAIGEN ===
from sdai.utils.logger import Logger


CIVITAI_BASE = 'https://civitai.red'
CIVITAI_API  = 'https://civitai.com/api/v1'

CIVITAI_DOMAINS = ('civitai.com', 'civitai.red', 'civitai.green')


@dataclass
class ModelData:
    """Resolved CivitAI model version metadata"""
    download_url: str
    model_id: str
    version_id: str
    model_type: str
    base_model: str
    file_name: str
    model_name: str = None
    version_name: str = None
    image_url: str = None
    image_name: str = None
    trained_words: list[str] = None
    sha256: str = None
    model_page_url: str = None


class CivitaiAPI:
    """CivitAI REST API wrapper for model discovery, download resolution and preview fetching.

    Usage:
        api  = CivitaiAPI(token=<TOKEN>)
        data = api.validate_download(url='https://civitai.red/models/...')
        meta = api.get_model_data(url='https://civitai.red/models/...')
    """

    SUPPORTED_TYPES = {'Checkpoint', 'TextualInversion', 'LORA'}    # For Save Preview
    IS_KAGGLE       = 'KAGGLE_URL_BASE' in os.environ

    def __init__(self, token: str = None, verbose=True, debug=False):
        self.token  = (token or '').strip()
        self.logger = Logger(enabled=verbose, debug=debug)


    # ~~ CORE HELPERS ~~

    def _get_data(self, path: str) -> dict | None:
        """GET request to API endpoint and return parsed JSON or None"""
        url = f"{CIVITAI_API}/{path}"
        headers = {'Authorization': f"Bearer {self.token}"} if self.token else {}
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            self.logger.error(f"GET {url} — {exc}")
            return None

    def _get_primary_file(self, version: dict) -> dict | None:
        """Return first primary file from a version dict"""
        files = version.get('files', [])
        for file in files:
            if file.get('primary') is True:
                return file
        return files[0] if files else None

    def _get_download_url(self, version: dict) -> str | None:
        """Return download URL from primary file or version fallback"""
        file = self._get_primary_file(version)
        if file and file.get('downloadUrl'):
            return file['downloadUrl']
        return version.get('downloadUrl')

    def _pick_preview(self, images: list[dict], stem: str, width=512) -> tuple[str | None, str | None]:
        """Return (url, filename) for the first usable preview image or (None, None)"""
        for img in images:
            url = img.get('url', '')

            if self.IS_KAGGLE and img.get('nsfwLevel', 0) >= 12:
                continue
            if any(url.lower().endswith(ext) for ext in ('.gif', '.mp4', '.webm')):
                continue

            ext = url.split('.')[-1].split('?')[0]

            if 'original=true' in url:
                url = url.replace('original=true', f"width={width}")
            else:
                url = re.sub(r'/width=[^/]+', f"/width={width}", url)
            return url, f"{stem}.preview.{ext}"
        return None, None

    def _preview_by_sha256(self, sha256: str, stem: str) -> tuple[str | None, str | None]:
        """Look up preview on CivitAI by SHA256 hash, returns (None, None) silently on miss"""
        ver = self.find_by_sha256(sha256)
        if ver:
            return self._pick_preview(ver.get('images', []), stem)
        return None, None

    def _check_early_access(self, ver: dict) -> bool:
        """Return True if version requires Early Access payment"""
        is_ea = ver.get('availability') == 'EarlyAccess' or bool(ver.get('earlyAccessEndsAt'))
        if not is_ea:
            return False

        model_id = ver.get('modelId')
        ver_id   = ver.get('id')
        ver_url  = f"{CIVITAI_BASE}/models/{model_id}?modelVersionId={ver_id}"

        # With a valid token, check whether the user purchased the model
        if self.token and len(self.token) == 32:
            download_url = self._get_download_url(ver)
            if download_url:
                try:
                    resp = requests.head(
                        download_url,
                        headers={'Authorization': f"Bearer {self.token}"},
                        allow_redirects=True,
                        timeout=15
                    )
                    if resp.status_code < 400:
                        self.logger.debug(f"Early Access confirmed purchased: {ver_url}")
                        return False    # User owns it — not blocked
                except Exception:
                    pass

        self.logger.warning(f"Early Access (skipping): {ver_url}")
        return True

    def _resolve_version_from_url(self, url: str) -> dict | None:
        """
        Resolve any CivitAI URL to a full version data dict.
        For model-page URLs iterates all versions and skips unpurchased Early Access ones.
        Requested modelVersionId is tried first when present in URL.
        """
        def resolve_version(ver_id: str) -> dict | None:
            ver = self._get_data(f"model-versions/{ver_id}")
            if not ver or self._check_early_access(ver):
                return None
            if not self._get_primary_file(ver):
                return None
            return ver

        # /api/download/models/VER_ID
        if '/api/download/models/' in url:
            ver_id = url.split('/api/download/models/')[1].split('?')[0].split('/')[0]
            return resolve_version(ver_id)

        # /models/MODEL_ID
        for domain in CIVITAI_DOMAINS:
            if f"{domain}/models/" in url:
                model_id   = url.split('/models/')[1].split('/')[0].split('?')[0]
                req_ver_id = (
                    url.split('modelVersionId=')[1].split('&')[0]
                    if 'modelVersionId=' in url else None
                )

                model = self._get_data(f"models/{model_id}")
                if not model:
                    self.logger.error(f"Cannot fetch model {model_id}")
                    return None

                versions = model.get('modelVersions', [])
                if req_ver_id:
                    versions.sort(key=lambda ver: str(ver.get('id')) != str(req_ver_id))

                for ver in versions:
                    full_ver = resolve_version(str(ver['id']))
                    if full_ver:
                        primary = self._get_primary_file(full_ver)
                        self.logger.debug(f"Used version {ver['id']} with primary file: {primary.get('name')}")
                        return full_ver

                self.logger.error(f"No downloadable version found for model {model_id}")
                return None

        # ?modelVersionId= only (no /models/ segment)
        if 'modelVersionId=' in url:
            ver_id = url.split('modelVersionId=')[1].split('&')[0]
            return resolve_version(ver_id)

        self.logger.error(f"Unsupported CivitAI URL format (use a model page, /api/download/ link or modelVersionId): {url}")
        return None


    # ~~ MODEL RESOLUTION ~~

    def _build_model_data(self, ver: dict, file_name: str, download_url: str) -> ModelData | None:
        """Construct ModelData from a resolved version API dict"""
        model_id   = str(ver.get('modelId'))
        ver_id     = str(ver.get('id'))
        model_type = ver['model']['type']
        sha256     = self.get_sha256(ver)
        stem       = Path(file_name).stem

        image_url, image_name = None, None
        if model_type in self.SUPPORTED_TYPES:
            image_url, image_name = self._pick_preview(ver.get('images', []), stem)
            if not image_url and sha256:
                image_url, image_name = self._preview_by_sha256(sha256, stem)

        return ModelData(
            download_url=download_url,
            model_id=model_id,
            version_id=ver_id,
            model_type=model_type,
            base_model=ver.get('baseModel'),
            file_name=file_name,
            model_name=ver['model'].get('name'),
            version_name=ver.get('name'),
            image_url=image_url,
            image_name=image_name,
            trained_words=ver.get('trainedWords'),
            sha256=sha256,
            model_page_url=f"{CIVITAI_BASE}/models/{model_id}?modelVersionId={ver_id}",
        )

    def validate_download(self, url: str, file_name: str = None) -> ModelData | None:
        """Resolve a CivitAI URL to ModelData, iterating versions to skip unowned Early Access"""
        ver = self._resolve_version_from_url(url)
        if not ver:
            return None

        download_url = self._get_download_url(ver)
        if not download_url:
            self.logger.error(f"No downloadUrl in version data for: {url}")
            return None

        if not file_name:
            selected_file = self._get_primary_file(ver)
            if selected_file:
                file_name = selected_file.get('name')

        return self._build_model_data(ver, file_name, download_url)


    # ~~ GENERAL ~~

    def get_model_data(self, url: str) -> dict[str, Any] | None:
        """Fetch full version metadata dict from CivitAI by any supported URL"""
        return self._resolve_version_from_url(url)

    def get_model_versions(self, model_id: str) -> list[dict] | None:
        """Return all version dicts for a model by ID"""
        data = self._get_data(f"models/{model_id}")
        return data.get('modelVersions') if data else None

    def get_sha256(self, ver: dict = None, version_id: str = None) -> str | None:
        """Extract SHA256 from version data dict, or fetch by version_id if dict not provided"""
        if ver is None and version_id:
            ver = self._get_data(f"model-versions/{version_id}")
        return ver.get('files', [{}])[0].get('hashes', {}).get('SHA256') if ver else None

    def find_by_sha256(self, sha256: str) -> dict | None:
        """Find version data by file SHA256 hash, returns None silently on miss"""
        return self._get_data(f"model-versions/by-hash/{sha256}")

    def _save_image(self, image_url: str, save_dir: Path, image_name: str, resize=False) -> bool:
        """Download and save an image; skips if already present, returns True on success"""
        file_path = save_dir / image_name
        if file_path.exists():
            return True
        try:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            data = self._resize_image(resp.content) if resize else io.BytesIO(resp.content)
            file_path.write_bytes(data.read())
            self.logger.success(f"Saved preview: {file_path}")
            return True
        except Exception as exc:
            self.logger.warning(f"Failed to download preview: {exc}")
            return False

    def preview_by_sha256(self, sha256: str, save_path: str | Path, stem: str):
        """Fetch and save a CivitAI preview image found via SHA256 hash lookup.

        Intended for models downloaded from non-CivitAI sources (HuggingFace, etc)
        """
        image_url, image_name = self._preview_by_sha256(sha256, stem)
        if not image_url or not image_name:
            self.logger.debug(f"No CivitAI preview found for sha256={sha256[:8]}...")
            return

        save_dir = Path(save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        self._save_image(image_url, save_dir, image_name)

    def download_preview_image(self, model_data: ModelData, save_path: str | Path = None, resize=True):
        """Download and save a preview image from a ModelData object"""
        if not model_data:
            self.logger.warning('ModelData is None — skipping download_preview_image')
            return
        if not model_data.image_url:
            self.logger.warning('No preview image URL available')
            return

        save_dir = Path(save_path) if save_path else Path.cwd()
        save_dir.mkdir(parents=True, exist_ok=True)
        self._save_image(model_data.image_url, save_dir, model_data.image_name, resize=resize)

    def _resize_image(self, raw: bytes, size=512) -> io.BytesIO:
        """Resize image bytes to target max side while preserving aspect ratio"""
        try:
            img  = Image.open(io.BytesIO(raw))
            w, h = img.size
            new_w, new_h = (size, int(h * size / w)) if w > h else (int(w * size / h), size)
            buf = io.BytesIO()
            img.resize((new_w, new_h), Image.Resampling.LANCZOS).save(buf, format='PNG')
            buf.seek(0)
            return buf
        except Exception as exc:
            self.logger.warning(f"Resize failed: {exc}")
            return io.BytesIO(raw)

    def save_model_info(self, model_data: ModelData, save_path: str | Path = None):
        """Save model metadata as a .json sidecar file next to the model"""
        if not model_data:
            self.logger.warning('ModelData is None — skipping save_model_info')
            return

        save_dir = Path(save_path) if save_path else Path.cwd()
        save_dir.mkdir(parents=True, exist_ok=True)
        info_path = save_dir / f"{Path(model_data.file_name).stem}.json"
        if info_path.exists():
            return

        info = {
            'modelName':    model_data.model_name,
            'versionName':  model_data.version_name,
            'modelId':      model_data.model_id,
            'versionId':    model_data.version_id,
            'contentType':  model_data.model_type,
            'baseModel':    model_data.base_model,
            'trainedTags':  ', '.join(model_data.trained_words or []),
            'modelPageURL': model_data.model_page_url,
            'sha256':       model_data.sha256,
        }
        try:
            info_path.write_text(json.dumps(info, indent=4), encoding='utf-8')
            self.logger.success(f"Saved model info: {info_path}")
        except Exception as exc:
            self.logger.error(f"Failed to save info: {exc}")
