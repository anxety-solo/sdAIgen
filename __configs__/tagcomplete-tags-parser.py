# ~ tagcomplete-tags-parser.py | CSV Tags Downloader for sd-webui-tagcomplete | by ANXETY ~

import json_utils as js

import argparse
import asyncio
import aiohttp
import re
import os
from datetime import datetime
from pathlib import Path


# Configuration
GITHUB_API_URL = "https://api.github.com/repos/DraconicDragon/dbr-e621-lists-archive/contents/tag-lists"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/DraconicDragon/dbr-e621-lists-archive/main/tag-lists"

# Target categories to process
TARGET_CATEGORIES = ['danbooru_e621_merged', 'danbooru', 'e621'] # Order is IMPORTANT!

osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS['home_path']
SETTINGS_PATH = PATHS['settings_path']

# Get current UI and extensions path
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))


# Find TagComplete extension directory
def find_tagcomplete_dir():
    """Find the TagComplete extension directory."""
    possible_names = [
        'a1111-sd-webui-tagcomplete',
        'sd-webui-tagcomplete',
        'webui-tagcomplete',
        'tag-complete',
        'tagcomplete'
    ]

    # Get all existing directories in extensions folder
    if EXTS.exists():
        for ext_dir in EXTS.iterdir():
            if ext_dir.is_dir():
                dir_name_lower = ext_dir.name.lower()

                # Check if directory name matches any of possible names
                for possible_name in possible_names:
                    if dir_name_lower == possible_name.lower():
                        tags_dir = ext_dir / 'tags'
                        tags_dir.mkdir(parents=True, exist_ok=True)
                        return tags_dir

    # If not found, create default
    default_dir = EXTS / 'a1111-sd-webui-tagcomplete' / 'tags'
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir

class TagsParser:
    def __init__(self, verbose=False):
        self.session = None
        self.tags_dir = find_tagcomplete_dir()
        self.verbose = verbose

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_directory_contents(self, path=''):
        """Get contents of a directory from GitHub API."""
        url = f"{GITHUB_API_URL}/{path}" if path else GITHUB_API_URL

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    if self.verbose:
                        print(f"Error fetching directory {path}: {response.status}")
                    return []
        except Exception as e:
            if self.verbose:
                print(f"Error fetching directory {path}: {e}")
            return []

    def extract_date_from_filename(self, filename):
        """Extract date from filename like 'danbooru_2025-07-05_pt20-ia-dd.csv'."""
        # Pattern to match YYYY-MM-DD format
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)

        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                return None
        return None

    def is_csv_file(self, filename):
        """Check if file is a CSV file."""
        return filename.lower().endswith('.csv')

    async def find_latest_files(self):
        """Find the latest CSV files for each category (TARGET_CATEGORIES)."""
        if self.verbose:
            print('🔍 Searching for latest tag files...')

        # Get main directory contents
        contents = await self.get_directory_contents()

        # Initialize with target categories
        latest_files = {category: {'date': None, 'file': None, 'path': None}
                       for category in TARGET_CATEGORIES}

        # Process each subdirectory
        for item in contents:
            if item['type'] == 'dir':
                subdir_name = item['name']

                if self.verbose:
                    print(f"📁 Checking {subdir_name}...")

                # Get subdirectory contents
                subdir_contents = await self.get_directory_contents(subdir_name)

                # Find CSV files in subdirectory
                for file_item in subdir_contents:
                    if file_item['type'] == 'file' and self.is_csv_file(file_item['name']):
                        filename = file_item['name']
                        file_date = self.extract_date_from_filename(filename)

                        if file_date:
                            # Find matching category
                            category = None
                            for target_cat in TARGET_CATEGORIES:
                                if target_cat in filename.lower():
                                    category = target_cat
                                    break

                            if category:
                                # Check if this is the latest file for this category
                                if (latest_files[category]['date'] is None or
                                    file_date > latest_files[category]['date']):
                                    latest_files[category] = {
                                        'date': file_date,
                                        'file': filename,
                                        'path': f"{subdir_name}/{filename}"
                                    }
                                    if self.verbose:
                                        print(f"📅 Found {category} file: {filename} ({file_date.strftime('%Y-%m-%d')})")

        return latest_files

    async def download_file(self, file_path, filename):
        """Download a file from GitHub."""
        url = f"{GITHUB_RAW_URL}/{file_path}"
        local_path = self.tags_dir / filename

        if self.verbose:
            print(f"⬇️  Downloading {filename}...")

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    with open(local_path, 'wb') as f:
                        f.write(await response.read())
                    if self.verbose:
                        print(f"✅ Downloaded: {filename}")
                    return True
                else:
                    if self.verbose:
                        print(f"❌ Error downloading {filename}: {response.status}")
                    return False
        except Exception as e:
            if self.verbose:
                print(f"❌ Error downloading {filename}: {e}")
            return False

    async def download_latest_tags(self):
        """Download the latest tag files."""
        if self.verbose:
            print(f"📂 Tags will be saved to: {self.tags_dir}")

        latest_files = await self.find_latest_files()

        downloaded = 0
        skipped = 0

        for category, info in latest_files.items():
            if info['file']:
                if self.verbose:
                    print(f"\n🎯 Latest {category} file: {info['file']} ({info['date'].strftime('%Y-%m-%d')})")

                # Generate filename with date after underscore
                date_str = info['date'].strftime('%Y-%m-%d')
                output_filename = f"{category}_{date_str}.csv"
                local_path = self.tags_dir / output_filename

                # Check if file already exists
                if local_path.exists():
                    if self.verbose:
                        print(f"⏭️  File {output_filename} already exists, skipping...")
                    skipped += 1
                    continue

                if await self.download_file(info['path'], output_filename):
                    downloaded += 1
            else:
                if self.verbose:
                    print(f"⚠️  No {category} files found")

        # Show summary
        if downloaded > 0:
            print(f"🎉 Downloaded {downloaded} tag files to {self.tags_dir}")

        if skipped > 0:
            if self.verbose:
                print(f"⏭️  Skipped {skipped} existing files")

        return downloaded

async def main(args=None):
    """Main function to run the parser."""
    parser = argparse.ArgumentParser(description=f"CSV Tags Parser for {', '.join(TARGET_CATEGORIES)}")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args, _ = parser.parse_known_args(args)

    if args.verbose:
        print(f"🚀 Starting CSV Tags Parser for {', '.join(TARGET_CATEGORIES)}")
        print('=' * 50)

    try:
        async with TagsParser(verbose=args.verbose) as tag_parser:
            await tag_parser.download_latest_tags()
    except Exception as e:
        print(f"❌ Error: {e}")

    if args.verbose:
        print('✨ Parser completed!')

if __name__ == '__main__':
    asyncio.run(main())