""" CivitAi API Module (V2) | by ANXETY """

from typing import Optional, Union, Tuple, Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import requests
import json
import os
import re
import io


# === Logger Utility ===
class APILogger:
    """Colored logger for API events"""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, msg: str, level: str = "info"):
        if not self.verbose and level != "error":
            return
        colors = {"error": 31, "success": 32, "warning": 33, "info": 34}
        print(f"\033[{colors[level]}m[API {level.title()}]:\033[0m {msg}")


# === Model Data ===
@dataclass
class ModelData:
    download_url: str
    clean_url: str
    model_name: str
    model_type: str
    version_id: str
    model_id: str
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    early_access: bool = False
    base_model: Optional[str] = None
    trained_words: Optional[List[str]] = None
    sha256: Optional[str] = None


# === Main API ===
class CivitAiAPI:
    """
    Usage Example:
        api = CivitAiAPI(token=token)
        result = api.validate_download(
            url='https://civitai.com/models/...',
            file_name='model.safetensors'
        )

        full_data = api.get_model_data(url='https://civitai.com/models/...')
    """

    BASE_URL = 'https://civitai.com/api/v1'
    SUPPORTED_TYPES = {'Checkpoint', 'TextualInversion', 'LORA'}    # For Save Preview
    IS_KAGGLE = 'KAGGLE_URL_BASE' in os.environ

    def __init__(self, token: Optional[str] = None, log: bool = True):
        self.token = token or '65b66176dcf284b266579de57fbdc024'    # FAKE
        self.logger = APILogger(verbose=log)

    # === Core Helpers ===
    def _build_url(self, endpoint: str) -> str:
        """Construct full API URL for given endpoint"""
        return f"{self.BASE_URL}/{endpoint}"

    def _get(self, url: str) -> Optional[Dict]:
        """Perform GET request and return JSON or None"""
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            self.logger.log(f"{url} failed: {e}", "error")
            return None

    def _extract_version_id(self, url: str) -> Optional[str]:
        """Extract version ID from various CivitAI URL formats"""
        if not url.startswith(('http://', 'https://')):
            self.logger.log("Invalid URL format", "error")
            return None

        if 'modelVersionId=' in url:
            return url.split('modelVersionId=')[1].split('&')[0]

        if 'civitai.com/models/' in url:
            model_id = url.split('/models/')[1].split('/')[0].split('?')[0]
            if model_id.isdigit():
                model_data = self._get(self._build_url(f"models/{model_id}"))
                return model_data.get('modelVersions', [{}])[0].get('id') if model_data else None

        if '/api/download/models/' in url:
            return url.split('/api/download/models/')[1].split('?')[0]

        self.logger.log(f"Unsupported URL format: {url}", "error")
        return None

    def _process_url(self, download_url: str) -> Tuple[str, str]:
        """Sanitize and sign download URL"""
        parsed = urlparse(download_url)
        query = parse_qs(parsed.query)
        query.pop('token', None)
        clean_url = parsed._replace(query=urlencode(query, doseq=True)).geturl()
        final_url = f"{clean_url}?token={self.token}" if self.token else clean_url
        return clean_url, final_url

    def _get_preview(self, images: List[Dict], name: str, resize: Optional[int] = 512) -> Tuple[Optional[str], Optional[str]]:
        """Extract a valid preview image URL and filename, with optional resizing via width in URL"""
        for img in images:
            url = img.get('url', '')
            ## Images are now downloaded via [Civitai-Extension]
            # if self.IS_KAGGLE and img.get('nsfwLevel', 0) >= 4:
            #     continue
            if any(url.lower().endswith(ext) for ext in ['.gif', '.mp4', '.webm']):
                continue
            ext = url.split('.')[-1].split('?')[0]
            if resize is not None:
                # Replace /width=XXXX/ with /width=resize/ if present
                url = re.sub(r"/width=\d+/", f"/width={resize}/", url)
            return url, f"{Path(name).stem}.preview.{ext}"
        return None, None

    def _parse_model_name(self, data: Dict, filename: Optional[str]) -> Tuple[str, str]:
        """Generate final model filename from metadata"""
        name = data['files'][0]['name']
        ext = name.split('.')[-1]
        if filename and '.' not in filename:
            filename += f".{ext}"
        return data['model']['type'], filename or name

    def _early_access_check(self, data: Dict) -> bool:
        """Check if model is gated behind Early Access"""
        ea = data.get('availability') == 'EarlyAccess' # or data.get('earlyAccessEndsAt')
        if ea:
            model_id = data.get('modelId')
            version_id = data.get('id')
            self.logger.log(f"Requires Early Access: https://civitai.com/models/{model_id}?modelVersionId={version_id}", "warning")
        return ea

    def get_sha256(self, data: Optional[dict] = None, version_id: Optional[str] = None) -> Optional[str]:
        """
        Get the model's sha256 hash from version data or by version_id.
        If data is not provided, it will be loaded using version_id.
        """
        if data is None and version_id is not None:
            data = self._get(self._build_url(f"model-versions/{version_id}"))
        if not data:
            return None
        return data.get("files", [{}])[0].get("hashes", {}).get("SHA256")

    # === sdAIgen ===
    def validate_download(self, url: str, file_name: Optional[str] = None) -> Optional[ModelData]:
        version_id = self._extract_version_id(url)
        if not version_id:
            return None

        data = self._get(self._build_url(f"model-versions/{version_id}"))
        if not data:
            return None

        if self._early_access_check(data):
            return None

        model_type, name = self._parse_model_name(data, file_name)
        clean_url, full_url = self._process_url(data['downloadUrl'])

        preview_url, preview_name = (None, None)
        if model_type in self.SUPPORTED_TYPES:
            preview_url, preview_name = self._get_preview(data.get('images', []), name)

        return ModelData(
            download_url=full_url,
            clean_url=clean_url,
            model_name=name,
            model_type=model_type,
            version_id=data['id'],
            model_id=data['modelId'],
            early_access=False,
            image_url=preview_url,
            image_name=preview_name,
            base_model=data.get("baseModel"),
            trained_words=data.get("trainedWords"),
            sha256=self.get_sha256(data)
        )

    # === General ===
    def get_model_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch full model version metadata from CivitAI by URL"""
        version_id = self._extract_version_id(url)
        if not version_id:
            self.logger.log(f"Cannot get model data — failed to extract version ID from URL: {url}", "error")
            return None

        data = self._get(self._build_url(f"model-versions/{version_id}"))
        if not data:
            self.logger.log(f"Failed to retrieve model version data for ID: {version_id}", "error")

        return data

    def get_model_versions(self, model_id: str) -> Optional[List[Dict]]:
        """Get all available versions of a model by ID"""
        data = self._get(self._build_url(f"models/{model_id}"))
        return data.get("modelVersions") if data else None

    def find_by_sha256(self, sha256: str) -> Optional[Dict]:
        """Find model version data by SHA256 hash"""
        return self._get(self._build_url(f"model-versions/by-hash/{sha256}"))

    def download_preview_image(self, model_data: ModelData, save_path: Optional[Union[str, Path]] = None, resize: bool = False):
        """
        Download and save model preview image.

        Args:
            model_data: ModelData object with preview metadata
            save_path: Directory path (str or Path) where image will be saved. Defaults to current directory.
            resize: If True, resize image to 512px max (default: False)
        """
        if model_data is None:
            self.logger.log("ModelData is None — skipping download_preview_image", "warning")
            return

        if not model_data.image_url:
            self.logger.log("No preview image URL available", "warning")
            return

        save_dir = Path(save_path) if save_path else Path.cwd()
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / model_data.image_name

        if file_path.exists():
            return

        try:
            res = requests.get(model_data.image_url, timeout=30)
            res.raise_for_status()
            img_data = self._resize_image(res.content) if resize else io.BytesIO(res.content)
            file_path.write_bytes(img_data.read())
            self.logger.log(f"Saved preview: {file_path}", "success")
        except Exception as e:
            self.logger.log(f"Failed to download preview: {e}", "error")

    def _resize_image(self, raw: bytes, size: int = 512) -> io.BytesIO:
        """Resize image to target size while preserving aspect ratio"""
        try:
            img = Image.open(io.BytesIO(raw))
            w, h = img.size
            new_size = (size, int(h * size / w)) if w > h else (int(w * size / h), size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            return output
        except Exception as e:
            self.logger.log(f"Resize failed: {e}", "warning")
            return io.BytesIO(raw)

    def save_model_info(self, model_data: ModelData, save_path: Optional[Union[str, Path]] = None):
        """
        Save model metadata to a JSON file.

        Args:
            model_data: ModelData object
            save_path: Directory path (str or Path) to save metadata. Defaults to current directory.
        """
        if model_data is None:
            self.logger.log("ModelData is None — skipping save_model_info", "warning")
            return

        save_dir = Path(save_path) if save_path else Path.cwd()
        save_dir.mkdir(parents=True, exist_ok=True)
        info_file = save_dir / f"{Path(model_data.model_name).stem}.json"

        if info_file.exists():
            return

        base_mapping = {
            'SD 1': 'SD1', 'SD 1.5': 'SD1', 'SD 2': 'SD2', 'SD 3': 'SD3',
            'SDXL': 'SDXL', 'Pony': 'SDXL', 'Illustrious': 'SDXL',
        }
        info = {
            "model_type": model_data.model_type,
            "sd_version": next((v for k, v in base_mapping.items() if k in (model_data.base_model or '')), ''),
            "modelId": model_data.model_id,
            "modelVersionId": model_data.version_id,
            "activation_text": ', '.join(model_data.trained_words or []),
            "sha256": model_data.sha256
        }

        try:
            info_file.write_text(json.dumps(info, indent=4))
            self.logger.log(f"Saved model info: {info_file}", "success")
        except Exception as e:
            self.logger.log(f"Failed to save info: {e}", "error")