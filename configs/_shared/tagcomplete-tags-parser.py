""" CSV Tags Downloader for sd-webui-tagcomplete extension | by ANXETY """

import argparse
import asyncio
import aiohttp
import re

from types import TracebackType
from datetime import datetime
from pathlib import Path

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH
from sdai.utils.logger import Logger
from sdai.utils.json import read


# ~~ Configuration ~~

EXTS_DIR = Path(read(SETTINGS_PATH, 'WEBUI.extension_dir'))

GITHUB_API_URL = 'https://api.github.com/repos/DraconicDragon/dbr-e621-lists-archive/contents/tag-lists'
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/DraconicDragon/dbr-e621-lists-archive/main/tag-lists'

# Order is IMPORTANT!
TARGET_CATEGORIES = ['danbooru_e621_merged', 'danbooru', 'e621']

TAGCOMPLETE_NAMES = {
    'a1111-sd-webui-tagcomplete', 'sd-webui-tagcomplete',
    'webui-tagcomplete', 'tag-complete', 'tagcomplete',
}

logger = Logger()


# ~~ Helpers ~~

def find_tagcomplete_dir() -> Path:
    """Find the TagComplete extension directory (create default if missing)"""
    candidates = EXTS_DIR.iterdir() if EXTS_DIR.exists() else ()
    for ext_dir in candidates:
        if ext_dir.is_dir() and ext_dir.name.lower() in TAGCOMPLETE_NAMES:
            return _ensure_tags_dir(ext_dir)
    return _ensure_tags_dir(EXTS_DIR / 'a1111-sd-webui-tagcomplete')


def _ensure_tags_dir(base_dir: Path) -> Path:
    """Create and return the `tags` directory under base_dir"""
    tags_dir = base_dir / 'tags'
    tags_dir.mkdir(parents=True, exist_ok=True)
    return tags_dir


# ~~ Tags Parser ~~

class TagsParser:
    """Finds and downloads the latest tag files for each target category"""

    def __init__(self, verbose=False):
        self.session: aiohttp.ClientSession | None = None
        self.tags_dir = find_tagcomplete_dir()
        self.logger   = Logger(enabled=verbose)

    async def __aenter__(self) -> 'TagsParser':
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if self.session:
            await self.session.close()

    async def _get_json(self, url: str) -> list:
        """GET url and return JSON payload (empty list on failure)"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                self.logger.error(f"Failed fetching {url}: {response.status}")
        except Exception as exc:
            self.logger.error(f"Failed fetching {url}: {exc}")
        return []

    async def get_directory_contents(self, path='') -> list:
        """Get contents of a directory from the GitHub API"""
        url = f"{GITHUB_API_URL}/{path}" if path else GITHUB_API_URL
        return await self._get_json(url)

    @staticmethod
    def extract_date_from_filename(filename: str) -> datetime | None:
        """Extract date from filename like 'danbooru_2025-07-05_pt20-ia-dd.csv'"""
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
        return None

    async def find_latest_files(self) -> dict:
        """Find the latest CSV file for each target category"""
        self.logger.info('Searching for latest tag files...')
        latest = {cat: {'date': None, 'file': None, 'path': None} for cat in TARGET_CATEGORIES}

        for item in await self.get_directory_contents():
            if item['type'] != 'dir':
                continue

            subdir = item['name']
            self.logger.info(f"Checking {subdir}...")

            for file_item in await self.get_directory_contents(subdir):
                filename = file_item.get('name', '')
                if file_item['type'] != 'file' or not filename.lower().endswith('.csv'):
                    continue

                file_date = self.extract_date_from_filename(filename)
                category = next((cat for cat in TARGET_CATEGORIES if cat in filename.lower()), None)

                if (category and file_date and
                        (latest[category]['date'] is None or
                         file_date > latest[category]['date'])):

                    latest[category] = {
                        'date': file_date,
                        'file': filename,
                        'path': f"{subdir}/{filename}",
                    }
                    self.logger.info(
                        f"Found {category} file: {filename} "
                        f"({file_date.strftime('%Y-%m-%d')})")

        return latest

    async def download_file(self, file_path: str, filename: str) -> bool:
        """Download a file from GitHub into tags_dir"""
        url = f"{GITHUB_RAW_URL}/{file_path}"
        local_path = self.tags_dir / filename
        self.logger.info(f"Downloading {filename}...")

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    local_path.write_bytes(await response.read())
                    self.logger.info(f"Downloaded: {filename}")
                    return True
                self.logger.error(f"Error downloading {filename}: {response.status}")
        except Exception as exc:
            self.logger.error(f"Error downloading {filename}: {exc}")
        return False

    async def download_latest_tags(self) -> int:
        """Download the latest tag files for each category"""
        self.logger.info(f"Tags will be saved to: {self.tags_dir}")
        downloaded = skipped = 0

        for category, info in (await self.find_latest_files()).items():
            if not info['file']:
                self.logger.warning(f"No {category} files found")
                continue

            output_filename = f"{category}_{info['date'].strftime('%Y-%m-%d')}.csv"
            local_path = self.tags_dir / output_filename
            self.logger.info(f"Latest {category} file: {info['file']}")

            if local_path.exists():
                self.logger.info(f"File {output_filename} already exists, skipping...")
                skipped += 1
                continue

            if await self.download_file(info['path'], output_filename):
                downloaded += 1

        if downloaded:
            print(f"Downloaded {downloaded} tag files to {self.tags_dir}")
        if skipped:
            self.logger.info(f"Skipped {skipped} existing files")
        return downloaded


# ~~ CLI ~~

async def main(args: list[str] | None = None):
    """CLI entry point"""
    parser = argparse.ArgumentParser(description=f"CSV Tags Parser for {', '.join(TARGET_CATEGORIES)}")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    args, _ = parser.parse_known_args(args)

    try:
        async with TagsParser(verbose=args.verbose) as tag_parser:
            await tag_parser.download_latest_tags()
    except Exception as exc:
        logger.error(f"Error: {exc}")


if __name__ == '__main__':
    asyncio.run(main())
