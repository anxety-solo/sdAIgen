""" Season Info Module | by ANXETY """

import datetime
import argparse

from IPython.display import display, HTML
from pathlib import Path


TRANSLATIONS = {
    'en': {
        'done_message':   'Done! Now you can run the cells below. ☄️',
        'runtime_env':    'Runtime environment:',
        'project_path':   'Project location:',
        'current_github': 'Current github:',
        'current_branch': 'Current branch:'
    },
    'ru': {
        'done_message':   'Готово! Теперь вы можете выполнить ячейки ниже. ☄️',
        'runtime_env':    'Среда выполнения:',
        'project_path':   'Расположение проекта:',
        'current_github': 'Текущий гитхаб:',
        'current_branch': 'Текущая ветка:'
    }
}

SEASON_CONFIG = {
    'winter': {
        'bg': 'linear-gradient(180deg, #66666633, transparent)',
        'primary': '#666666',
        'accent': '#ffffff',
        'icon': '❄️',
        'particle_color': '#ffffff',
        'particle': {'class': 'snowflake', 'size': (8, 8), 'duration': (2, 5), 'interval': 50, 'max': 100}
    },
    'spring': {
        'bg': 'linear-gradient(180deg, #9366b433, transparent)',
        'primary': '#9366b4',
        'accent': '#dbcce6',
        'icon': '🌸',
        'particle_color': '#ffb3ba',
        'particle': {'class': 'petal', 'size': (8, 8), 'duration': (3, 6), 'interval': 250, 'max': 40}
    },
    'summer': {
        'bg': 'linear-gradient(180deg, #ffe76633, transparent)',
        'primary': '#ffe766',
        'accent': '#fff7cc',
        'icon': '🌴',
        'particle_color': '#ffd700',
        'particle': {'class': 'stick', 'size': (2, 15), 'duration': (3, 7), 'interval': 100, 'max': 25}
    },
    'autumn': {
        'bg': 'linear-gradient(180deg, #ff8f6633, transparent)',
        'primary': '#ff8f66',
        'accent': '#ffd9cc',
        'icon': '🍁',
        'particle_color': '#ff8f66',
        'particle': {'class': 'leaf', 'size': (12, 12), 'duration': (3, 6), 'interval': 250, 'max': 40}
    }
}

PARTICLE_STYLES = {
    'snowflake': 'border-radius: 50%; filter: blur(1px);',
    'petal':     'border-radius: 50% 50% 0 50%; transform: rotate(45deg); filter: blur(0.5px);',
    'stick':     'transform-origin: center bottom;',
    'leaf':      'clip-path: polygon(50% 0%, 0% 100%, 100% 100%);'
}

PARTICLE_ANIMATIONS = {
    'snowflake': 'translate(-50%, -50%) scale(0) | translate(-50%, -50%) scale(1) | translate(-50%, 350%) scale(0.5)',
    'petal':     'translate(-50%, -50%) scale(0) | translate(-50%, -50%) scale(1) rotate(180deg) | translate(-50%, 150%) scale(0.5) rotate(360deg)',
    'stick':     'translate(-50%, -50%) rotate(0) scale(0.5) | translate(-50%, -50%) rotate(0deg) scale(1) | translate(-50%, 150%) rotate(180deg) scale(0.5)',
    'leaf':      'translate(-50%, -50%) rotate(0deg) | translate(-50%, -50%) rotate(180deg) | translate(-50%, 150%) rotate(360deg)'
}


def get_season() -> str:
    month = datetime.datetime.now().month
    if month in range(3, 6):
        return 'spring'
    if month in range(6, 9):
        return 'summer'
    if month in range(9, 12):
        return 'autumn'
    return 'winter'


def generate_particle_script(season: str, config: dict) -> str:
    particle = config['particle']
    particle_class = particle['class']
    color = config['particle_color']

    anim_steps = PARTICLE_ANIMATIONS[particle_class].split(' | ')

    style = f'''
        .{particle_class} {{
          position: absolute;
          width: {particle['size'][0]}px;
          height: {particle['size'][1]}px;
          background: {color};
          {PARTICLE_STYLES[particle_class]}
          opacity: 0;
          pointer-events: none;
        }}
        @keyframes particle-fall {{
          0% {{ opacity: 0; transform: {anim_steps[0]}; }}
          20% {{ opacity: 0.8; transform: {anim_steps[1]}; }}
          100% {{ opacity: 0; transform: {anim_steps[2]}; }}
        }}
    '''

    return f'''
    <script>
    ((() => {{
      const container = document.querySelector('.season-container');
      if (!container) return;

      const style = document.createElement('style');
      style.textContent = `{style}`;
      document.head.appendChild(style);

      let activeParticles = 0;
      const maxParticles = {particle['max']};

      const createParticle = () => {{
        if (activeParticles >= maxParticles) return;

        const particle = document.createElement('div');
        particle.className = '{particle_class}';
        const duration = {particle['duration'][0]} + Math.random() * {particle['duration'][1] - particle['duration'][0]};

        particle.style.cssText = `
          left: ${{Math.random() * 100}}%;
          top: ${{Math.random() * 100}}%;
          animation: particle-fall ${{duration}}s linear forwards;
        `;

        activeParticles++;
        particle.addEventListener('animationend', () => {{
          particle.remove();
          activeParticles--;
        }}, {{ once: true }});

        container.appendChild(particle);
      }};

      const interval = setInterval(createParticle, {particle['interval']});

      const observer = new MutationObserver(() => {{
        if (!document.contains(container)) {{
          clearInterval(interval);
          observer.disconnect();
        }}
      }});
      observer.observe(document.body, {{ childList: true, subtree: true }});
    }}))();
    </script>
    '''


def display_info(env_name: str, project_path: str | Path, github: str | None = None, branch='main', lang='en'):
    season = get_season()
    config = SEASON_CONFIG[season]
    tr     = TRANSLATIONS.get(lang, TRANSLATIONS['en'])

    content = f'''
    <div class="season-container">
      <div class="text-container">
        {''.join(f'<span>{c}</span>' for c in f"{config['icon']} ANXETY   SDAIGEN   V3 {config['icon']}")}
      </div>
      <div class="message-container">
        <span>{tr['done_message']}</span>
        <span>{tr['runtime_env']} <span class="env">{env_name}</span></span>
        {f'<span>{tr["current_github"]} <span class="github">{github}</span></span>' if github and github.split('/', 1)[0] != 'anxety-solo' else ''}
        <span>{tr['project_path']} <span class="project">{project_path}</span></span>
        <span>{tr['current_branch']} <span class="branch">{branch}</span></span>
      </div>
    </div>
    '''

    style = f'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');

    .season-container {{
      position: relative;
      margin: 0 10px !important;
      padding: 20px !important;
      min-height: 200px;
      background: {config['bg']};
      border-top: 2px solid {config['primary']};
      border-radius: 15px;
      overflow: hidden;
      animation: fadeIn 0.5s ease-in;
    }}

    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

    .text-container {{
      font-family: 'Righteous', cursive;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      margin-bottom: 1em;
      gap: 0.5em;
    }}

    .text-container span,
    .message-container span {{
      opacity: 0;
      filter: blur(4px);
      transform: translateY(-20px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .text-container span {{
      color: {config['primary']};
      font-size: 2.5rem;
    }}

    .message-container {{
      display: flex;
      flex-direction: column;
      font-family: 'Righteous', cursive;
      text-align: center;
      gap: 0.5em;
    }}

    .message-container span {{
      color: {config['primary']};
      font-size: 1.2rem;
      transform: translateY(20px);
    }}

    .text-container.loaded span,
    .message-container.loaded span {{
      opacity: 1;
      filter: blur(0);
      transform: translateY(0);
      color: {config['accent']};
    }}

    .env {{ color: #FFA500 !important; }}
    .project {{ color: #FF99C2 !important; }}
    .branch {{ color: #16A543 !important; }}
    .github {{ color: #C786D3 !important; }}
    </style>
    '''

    script = '''
    <script>
    (() => {
      const textContainer = document.querySelector('.text-container');
      const messageContainer = document.querySelector('.message-container');

      textContainer.querySelectorAll('span').forEach((span, i) => {
        span.style.transitionDelay = `${i * 25}ms`;
      });

      messageContainer.querySelectorAll('span').forEach((span, i) => {
        span.style.transitionDelay = `${i * 50}ms`;
      });

      setTimeout(() => {
        textContainer.classList.add('loaded');
        messageContainer.classList.add('loaded');
      }, 250);
    })();
    </script>
    '''

    display(HTML(content + style + script))
    display(HTML(generate_particle_script(season, config)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('env_name', type=str)
    parser.add_argument('project_path', type=str)
    parser.add_argument('github', type=str)
    parser.add_argument('branch', type=str)
    parser.add_argument('lang', type=str)

    args = parser.parse_args()

    display_info(
        env_name=args.env_name,
        project_path=args.project_path,
        github=args.github,
        branch=args.branch,
        lang=args.lang,
    )
