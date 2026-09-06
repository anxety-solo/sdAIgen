// Check CivitAI token validity (valid = 32 chars)
function checkCivitaiKey() {
    const input = document.querySelector('.cai-token-input input[type="text"]');
    if (!input) return;

    const len = input.value.trim().length;
    input.style.animation = 'none';
    void input.offsetWidth;

    if (len !== 32) { input.style.animation = len === 0 ? 'pulseBlue 1s ease 3' : 'pulseYellow 0.75s ease 5'; }
}

// Toggle Custom Downloads container (expand/collapse)
function toggleContainer() {
    const s = 'showed';
    document.querySelector('.container_cdl').classList.toggle('expanded');
    document.querySelector('.info').classList.toggle(s);
    document.querySelector('.empowerment').classList.toggle(s);
}

// Show notification in .sideContainer
function showNotification(msg, type = 'info', duration = 3000) {
    const ICONS = { success: '✅', error: '❌', info: '💡', warning: '⚠️' };
    const container = document.querySelector('.sideContainer');
    if (!container) return;

    document.querySelectorAll('.notification-popup').forEach(p => p.remove());

    const popup = Object.assign(document.createElement('div'), { className: `notification-popup ${type}` });
    popup.innerHTML = `
        <div class="notification ${type}">
            <span class="notification-icon">${ICONS[type] || ICONS.info}</span>
            <span class="notification-text">${msg}</span>
        </div>
    `;
    container.appendChild(popup);

    requestAnimationFrame(() => popup.classList.add('show'));
    setTimeout(() => {
        popup.classList.remove('show');
        setTimeout(() => popup.remove(), 500);
    }, duration);
}

// GDrive panel — show/hide with showedWidgets / hideWidgets animations
(() => {
    const poll = setInterval(() => {
        const panel = document.querySelector('.container_gdrive');
        if (!panel) return;
        clearInterval(poll);

        const show = () => {
            panel.style.display = '';
            panel.style.pointerEvents = 'auto';
            void panel.offsetWidth;
            panel.style.animation = 'showedWidgets 0.45s forwards ease';
        };

        const hide = (animate) => {
            panel.style.pointerEvents = 'none';
            if (animate) {
                panel.style.animation = 'hideWidgets 0.3s forwards ease';
                setTimeout(() => {
                    if (!panel.classList.contains('gdrive-visible') || panel.classList.contains('hide')) {
                        panel.style.display = 'none';
                        panel.style.animation = '';
                    }
                }, 320);
            } else {
                panel.style.display = 'none';
            }
        };

        if (panel.classList.contains('gdrive-visible')) {
            show();
        } else {
            hide(false);
        }

        new MutationObserver(() => {
            if (panel.classList.contains('hide')) {
                panel.style.pointerEvents = 'none';
                if (panel.classList.contains('gdrive-visible')) { panel.style.animation = 'hideWidgets 0.3s forwards ease'; }
                return;
            }
            panel.classList.contains('gdrive-visible') ? show() : hide(true);
        }).observe(panel, { attributes: true, attributeFilter: ['class'] });
    }, 100);
})();
