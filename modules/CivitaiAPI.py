''' CivitAi API | ANXETY'''

from urllib.parse import urlparse, parse_qs
import requests
import os

class CivitAiAPI:
    Kaggle = 'KAGGLE_URL_BASE' in os.environ    # to check NSFW
    SUPPORT_TYPES = {'Checkpoint', 'TextualInversion', 'LORA'}

    def __init__(self, civitai_token=None):
        self.token = civitai_token or "65b66176dcf284b266579de57fbdc024"    # FAKE
        self.base_url = "https://civitai.com/api/v1"

    def _prepare_url(self, url):
        """Prepare the URL for API requests by adding the token."""
        if not self.token:
            return url
        url = url.split('?token=')[0] if '?token=' in url else url
        if '?type=' in url:
            return url.replace('?type=', f'?token={self.token}&type=')
        return f"{url}?token={self.token}"

    def _get_model_data(self, url):
        """Retrieve model data from the API."""
        try:
            if "civitai.com/models/" in url:
                if '?modelVersionId=' in url:
                    version_id = url.split('?modelVersionId=')[1]
                else:
                    model_id = url.split('/models/')[1].split('/')[0]
                    model_data = requests.get(f"{self.base_url}/models/{model_id}").json()
                    version_id = model_data['modelVersions'][0].get('id')
            else:
                version_id = url.split('/models/')[1].split('/')[0]

            return requests.get(f"{self.base_url}/model-versions/{version_id}").json()
        except (KeyError, IndexError, requests.RequestException) as e:
            print(f"\033[31m[Error]:\033[0m {e}")
            return None

    def fetch_data(self, url):
        """Main method to fetch data from CivitAi API."""
        url = self._prepare_url(url)
        data = self._get_model_data(url)

        if not data:
            print("\033[31m[Data Info]:\033[0m Failed to retrieve data from the API.\n")
            return None

        return data

    def get_model_info(self, data, url, file_name):
        """Extract model type and name from the data."""
        model_type = data['model']['type']
        model_name = data['files'][0]['name']

        if 'type=' in url:
            url_model_type = parse_qs(urlparse(url).query).get('type', [''])[0].lower()
            if 'vae' in url_model_type:
                model_type = data['files'][1]['type']
                model_name = data['files'][1]['name']

        if file_name and '.' not in file_name:
            file_extension = model_name.split('.')[-1]
            model_name = f"{file_name}.{file_extension}"
        elif file_name:
            model_name = file_name

        return model_type, model_name

    def get_download_url(self, data, url):
        """Return the download URL from the data."""
        if data and 'files' in data:
            model_type, _ = self.get_model_info(data, url, None)  # Get model type for checking
            if any(t.lower() in model_type.lower() for t in self.SUPPORT_TYPES):
                return data.get('downloadUrl')
            return data['files'][1]['downloadUrl'] if len(data['files']) > 1 else data.get('downloadUrl')
        return None

    def get_full_and_clean_download_url(self, download_url):
        """Return both the clean and full download URLs."""
        clean_url = download_url
        full_url = f"{download_url}{'&' if '?' in download_url else '?'}token={self.token}"
        return clean_url, full_url

    def get_image_info(self, data, model_name, model_type):
        """Return image URL and name if applicable."""
        if not any(t in model_type for t in self.SUPPORT_TYPES):
            return None, None

        if data and 'images' in data:
            for image in data['images']:
                if image['nsfwLevel'] >= 4 and self.Kaggle:  # Filter NSFW images for Kaggle
                    continue
                image_url = image['url']
                image_extension = image_url.split('.')[-1]
                image_name = f"{model_name.split('.')[0]}.preview.{image_extension}" if image_url else None
                return image_url, image_name
        return None, None