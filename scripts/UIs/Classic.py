# ~ Classic.py | by ANXETY ~

from _core import Core
import asyncio
from IPython.utils import capture

# Constants
UI = 'Classic'
REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
METHOD = 'zip'

CONFIGS = [
    # settings
    f"{UI}/config.json",
    f"{UI}/ui-config.json",
    "styles.csv",
    "user.css",
    # other
    "notification.mp3"
]

EXTENSIONS = [
    # ANXETY Edits
    'https://github.com/anxety-solo/webui_timer timer',
    'https://github.com/anxety-solo/anxety-theme',
    'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',

    # Gutris1
    'https://github.com/gutris1/sd-image-viewer Image-Viewer',
    'https://github.com/gutris1/sd-image-info Image-Info',
    'https://github.com/gutris1/sd-hub SD-Hub',

    # OTHER | ON
    'https://github.com/Bing-su/adetailer',
]

def fixes_modules(webui_path):
    """Apply specific fixes for Classic UI modules"""
    module_path = f"{webui_path}/modules/cmd_args.py"
    with open(module_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        if '# Arguments added by ANXETY' in content:
            return

        add_block = [
            '\n\n# Arguments added by ANXETY',
            'parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
            'default=os.path.join(models_path, \'hypernetworks\'), help="hypernetwork directory")'
        ]

        prefix = '\n' if content and not content.endswith('\n') else ''
        f.seek(0, 2)
        f.write(prefix + '\n'.join(add_block))

async def main():
    # Initialize core with UI name
    core = Core(UI)
    
    # Prepare full config URLs
    config_urls = [f"https://raw.githubusercontent.com/{core.FORK_REPO}/{core.BRANCH}/__configs__/{cfg}" 
                  for cfg in CONFIGS]
    
    # Add Kaggle-specific extension if needed
    extensions = EXTENSIONS.copy()
    if core.ENV_NAME == 'Kaggle':
        extensions.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')
    
    # Perform installation
    with capture.capture_output():
        await core.core_install(
            source=REPO_URL,
            configs=config_urls,
            extensions=extensions,
            mode=METHOD
        )
        
        # Apply Classic-specific fixes
        fixes_modules(core.WEBUI)

if __name__ == '__main__':
    asyncio.run(main())