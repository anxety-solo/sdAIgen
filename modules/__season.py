from IPython.display import display, HTML
import datetime
import argparse

TRANSLATIONS = {
    'en': {
        'done_message': "Done! Now you can run the cells below. ☄️",
        'runtime_env': "Runtime environment:",
        'file_location': "File location:",
        'current_fork': "Current fork:",
        'current_branch': "Current branch:"
    },
    'ru': {
        'done_message': "Готово! Теперь вы можете выполнить ячейки ниже. ☄️",
        'runtime_env': "Среда выполнения:",
        'file_location': "Расположение файлов:",
        'current_fork': "Текущий форк:",
        'current_branch': "Текущая ветка:"
    }
}

def get_season():
    month = datetime.datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def display_info(env, scr_folder, branch, lang='en', fork=None):
    season = get_season()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])

    season_config = {
        'winter': {
            'bg': 'linear-gradient(180deg, #66666633, transparent)',
            'primary': '#666666',
            'accent': '#ffffff',
            'icon': '❄️',
            'particle_color': '#ffffff'
        },
        'spring': {
            'bg': 'linear-gradient(180deg, #9366b433, transparent)',
            'primary': '#9366b4',
            'accent': '#dbcce6',
            'icon': '🌸',
            'particle_color': '#ffb3ba'
        },
        'summer': {
            'bg': 'linear-gradient(180deg, #ffe76633, transparent)',
            'primary': '#ffe766',
            'accent': '#fff7cc',
            'icon': '🌴',
            'particle_color': '#ffd700'
        },
        'autumn': {
            'bg': 'linear-gradient(180deg, #ff8f6633, transparent)',
            'primary': '#ff8f66',
            'accent': '#ffd9cc',
            'icon': '🍁',
            'particle_color': '#ff8f66'
        }
    }
    config = season_config.get(season, season_config['winter'])

    CONTENT = f"""
    <div class="season-container">
      <div class="text-container">
        <span>{config['icon']}</span>
        <span>A</span><span>N</span><span>X</span><span>E</span><span>T</span><span>Y</span>
        <span>&nbsp;</span>
        <span>S</span><span>D</span><span>-</span><span>W</span><span>E</span><span>B</span><span>U</span><span>I</span>
        <span>&nbsp;</span>
        <span>V</span><span>2</span>
        <span>{config['icon']}</span>
      </div>

      <div class="message-container">
        <span>{translations['done_message']}</span>
        <span>{translations['runtime_env']} <span class="env">{env}</span></span>
        <span>{translations['file_location']} <span class="files-location">{scr_folder}</span></span>
        {f"<span>{translations['current_fork']} <span class='fork'>{fork}</span></span>" if fork else ""}
        <span>{translations['current_branch']} <span class="branch">{branch}</span></span>
      </div>
    </div>
    """

    STYLE = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');

    .season-container {{
      position: relative;
      margin: 0 10px !important;
      padding: 20px !important;
      border-radius: 15px;
      margin: 10px 0;
      overflow: hidden;
      min-height: 200px;
      background: {config['bg']};
      border-top: 2px solid {config['primary']};
      animation: fadeIn 0.5s ease-in !important;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}

    .text-container {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 0.5em;
      font-family: 'Righteous', cursive;
      margin-bottom: 1em;
    }}

    .text-container span {{
      font-size: 2.5rem;
      color: {config['primary']};
      opacity: 0;
      transform: translateY(-20px);
      filter: blur(4px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .text-container.loaded span {{
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
      color: {config['accent']};
    }}

    .message-container {{
      font-family: 'Righteous', cursive;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 0.5em;
    }}

    .message-container span {{
      font-size: 1.2rem;
      color: {config['primary']};
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .message-container.loaded span {{
      opacity: 1;
      transform: translateY(0);
      color: {config['accent']};
    }}

    .env {{ color: #FFA500 !important; }}
    .files-location {{ color: #FF99C2 !important; }}
    .branch {{ color: #16A543 !important; }}
    .fork {{ color: #C786D3 !important; }}
    </style>
    """

    SCRIPT = """
    <script>
    (function() {
      // Text animation
      const textContainer = document.querySelector('.text-container');
      const messageContainer = document.querySelector('.message-container');
      const textSpans = textContainer.querySelectorAll('span');
      const messageSpans = messageContainer.querySelectorAll('span');

      textSpans.forEach((span, index) => {
        span.style.transitionDelay = `${index * 25}ms`;
      });

      messageSpans.forEach((span, index) => {
        span.style.transitionDelay = `${index * 50}ms`;
      });

      setTimeout(() => {
        textContainer.classList.add('loaded');
        messageContainer.classList.add('loaded');
      }, 250);
    })();
    </script>
    """

    display(HTML(CONTENT + STYLE + SCRIPT))

    # === Season Scripts ===

    ## OLD VER | adaptation needed...
    # WINTER_SCRIPT = """
    # <script>
    # // Function to create snowflakes
    # function createSnowflake() {
    #   const snowContainer = document.getElementById('snow-container');
    #   const snowflake = document.createElement('div');
    #   snowflake.className = 'snowflake';

    #   // Set random size
    #   const size = Math.random() * 5 + 3; // Size from 3 to 8 pixels
    #   snowflake.style.width = size + 'px';
    #   snowflake.style.height = size + 'px';

    #   // Position the snowflake within the snow container
    #   const containerRect = snowContainer.getBoundingClientRect();
    #   snowflake.style.left = Math.random() * (containerRect.width - size) + 'px';
    #   snowflake.style.top = -size + 'px'; // Start just above the container

    #   // Set random opacity between 0.1 and 0.5
    #   const opacity = Math.random() * 0.4 + 0.1;
    #   snowflake.style.opacity = opacity;

    #   // Set random fall duration and angle (up to 25 degrees)
    #   const fallDuration = Math.random() * 3 + 2; // Random fall duration (from 2 to 5 seconds)
    #   const angle = (Math.random() * 50 - 25) * (Math.PI / 180); // Angle from -25 to 25 degrees
    #   const horizontalMovement = Math.sin(angle) * (containerRect.height / 2); // Horizontal shift
    #   const verticalMovement = Math.cos(angle) * (containerRect.height + 10); // Vertical shift

    #   snowContainer.appendChild(snowflake); // Append snowflake to snow container

    #   // Animation for falling with horizontal movement
    #   snowflake.animate([
    #     { transform: `translate(0, 0)`, opacity: 1 },
    #     { transform: `translate(${horizontalMovement}px, ${verticalMovement}px)`, opacity: 0 }
    #   ], {
    #     duration: fallDuration * 1000,
    #     easing: 'linear',
    #     fill: 'forwards'
    #   });

    #   // Also remove the snowflake after falling
    #   setTimeout(() => {
    #     snowflake.remove();
    #   }, fallDuration * 1000);
    # }
    # setInterval(createSnowflake, 50);
    # </script>
    # """

    WINTER_SCRIPT = f"""
    <script>
    (function() {{
      const container = document.querySelector('.season-container');
      const style = document.createElement('style');
      style.innerHTML = `
        .snowflake {{
          position: absolute;
          background: {config['particle_color']};
          border-radius: 50%;
          filter: blur(1px);
          opacity: 0;
          animation: snow-fall linear forwards;
        }}
        @keyframes snow-fall {{
          0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0); }}
          20% {{ opacity: 0.8; transform: translate(-50%, -50%) scale(1); }}
          100% {{ opacity: 0; transform: translate(-50%, 150%) scale(0.5); }}
        }}
      `;
      document.head.appendChild(style);

      function createSnowflake() {{
        const snowflake = document.createElement('div');
        snowflake.className = 'snowflake';
        const size = Math.random() * 5 + 3;
        const x = Math.random() * 100;
        const duration = Math.random() * 3 + 2;
        snowflake.style.cssText = `
          width: ${{size}}px;
          height: ${{size}}px;
          left: ${{x}}%;
          top: ${{Math.random() * 100}}%;
          animation: snow-fall ${{duration}}s linear forwards;
        `;
        snowflake.addEventListener('animationend', () => snowflake.remove());
        container.appendChild(snowflake);
      }}
      setInterval(createSnowflake, 50);
    }})();
    </script>
    """

    SPRING_SCRIPT = f"""
    <script>
    (function() {{
      const container = document.querySelector('.season-container');
      const style = document.createElement('style');
      style.innerHTML = `
        .petal {{
          position: absolute;
          width: 8px;
          height: 8px;
          background: {config['particle_color']};
          border-radius: 50% 50% 0 50%;
          transform: rotate(45deg);
          opacity: 0;
          pointer-events: none;
          filter: blur(0.5px);
        }}
        @keyframes spring-fall {{
          0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0); }}
          20% {{ opacity: 0.8; transform: translate(-50%, -50%) scale(1) rotate(180deg); }}
          100% {{ opacity: 0; transform: translate(-50%, 150%) scale(0.5) rotate(360deg); }}
        }}
      `;
      document.head.appendChild(style);

      function createPetal() {{
        const petal = document.createElement('div');
        petal.className = 'petal';
        const startX = Math.random() * 100;
        const duration = Math.random() * 3 + 3;
        petal.style.cssText = `
          left: ${{startX}}%;
          top: ${{Math.random() * 100}}%;
          animation: spring-fall ${{duration}}s linear forwards;
        `;
        petal.addEventListener('animationend', () => petal.remove());
        container.appendChild(petal);
      }}
      setInterval(createPetal, 250);
    }})();
    </script>
    """

    SUMMER_SCRIPT = f"""
    <script>
    (function() {{
      const container = document.querySelector('.season-container');
      const style = document.createElement('style');
      style.innerHTML = `
        .sun-ray {{
          position: absolute;
          width: 3px;
          height: 20px;
          background: linear-gradient(to bottom, {config['particle_color']}, transparent);
          transform-origin: bottom center;
          opacity: 0;
        }}
        @keyframes summer-shine {{
          0%, 100% {{ opacity: 0; transform: rotate(var(--angle)) scale(0); }}
          50% {{ opacity: 0.5; transform: rotate(var(--angle)) scale(1); }}
        }}
      `;
      document.head.appendChild(style);

      function createRay() {{
        const ray = document.createElement('div');
        ray.className = 'sun-ray';
        const angle = Math.random() * 360;
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        const duration = Math.random() * 1 + 1;
        ray.style.cssText = `
          left: ${{x}}%;
          top: ${{y}}%;
          --angle: ${{angle}}deg;
          animation: summer-shine ${{duration}}s ease-in-out infinite;
        `;
        container.appendChild(ray);
      }}
      setInterval(createRay, 650);
    }})();
    </script>
    """

    AUTUMN_SCRIPT = f"""
    <script>
    (function() {{
      const container = document.querySelector('.season-container');
      const style = document.createElement('style');
      style.innerHTML = `
        .leaf {{
          position: absolute;
          width: 12px;
          height: 12px;
          background: {config['particle_color']};
          clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
          opacity: 0;
        }}
        @keyframes autumn-fall {{
          0% {{ opacity: 0; transform: translate(-50%, -50%) rotate(0deg); }}
          20% {{ opacity: 0.8; transform: translate(-50%, -50%) rotate(180deg); }}
          100% {{ opacity: 0; transform: translate(-50%, 150%) rotate(360deg); }}
        }}
      `;
      document.head.appendChild(style);

      function createLeaf() {{
        const leaf = document.createElement('div');
        leaf.className = 'leaf';
        const startX = Math.random() * 100;
        const duration = Math.random() * 3 + 3;
        leaf.style.cssText = `
          left: ${{startX}}%;
          top: ${{Math.random() * 100}}%;
          animation: autumn-fall ${{duration}}s linear forwards;
        `;
        leaf.addEventListener('animationend', () => leaf.remove());
        container.appendChild(leaf);
      }}
      setInterval(createLeaf, 250);
    }})();
    </script>
    """

    # Season Scripts
    if season == 'winter':
        display(HTML(WINTER_SCRIPT))
    elif season == 'spring':
        display(HTML(SPRING_SCRIPT))
    elif season == 'summer':
        display(HTML(SUMMER_SCRIPT))
    elif season == 'autumn':
        display(HTML(AUTUMN_SCRIPT))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('env', type=str, help='Runtime environment')
    parser.add_argument('scr_folder', type=str, help='Script folder location')
    parser.add_argument('branch', type=str, help='Current branch')
    parser.add_argument('lang', type=str, help='Language for messages (ru/en)')
    parser.add_argument('fork', type=str, help='Current git-fork')

    args = parser.parse_args()

    display_info(
        env=args.env,
        scr_folder=args.scr_folder,
        branch=args.branch,
        lang=args.lang,
        fork=args.fork
    )