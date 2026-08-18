// main-widgets.js | by ANXETY

// CivitAI Token check (valid = 32 chars)
function checkCivitaiKey() {
    const input = document.querySelector('.cai-token-input input[type="text"]');
    if (!input) return;

    const len = input.value.trim().length;
    input.style.animation = 'none';
    void input.offsetWidth;

    if (len === 32) return;

    input.style.animation = len === 0
        ? 'pulseBlue 1s ease 3'
        : 'pulseYellow 0.75s ease 5';
}


// Toggle Custom Downloads container (expand/collapse)
function toggleContainer() {
    const SHOW_CLASS = 'showed';
    document.querySelector('.container_cdl').classList.toggle('expanded');
    document.querySelector('.info').classList.toggle(SHOW_CLASS);
    document.querySelector('.empowerment').classList.toggle(SHOW_CLASS);
}


// Notifications (rendered into .sideContainer)
function showNotification(message, type = 'info', duration = 2500) {
    const ICONS = { success: '✅', error: '❌', info: '💡', warning: '⚠️' };
    const sideContainer = document.querySelector('.sideContainer');
    if (!sideContainer) return;

    document.querySelectorAll('.notification-popup').forEach(p => p.remove());

    const popup = document.createElement('div');
    popup.className = `notification-popup ${type}`;
    popup.innerHTML = `
        <div class="notification ${type}">
            <span class="notification-icon">${ICONS[type] || ICONS.info}</span>
            <span class="notification-text">${message}</span>
        </div>
    `;

    sideContainer.appendChild(popup);

    // FadeIn
    requestAnimationFrame(() => popup.classList.add('show'));

    // FadeOut + remove
    setTimeout(() => {
        popup.classList.remove('show');
        setTimeout(() => popup.remove(), 500);
    }, duration);
}


// GDrive panel — show/hide with showedWidgets/hideWidgets animation
(function initGDrivePanel() {
    const SHOW_DUR = '0.45s';
    const HIDE_DUR = '0.3s';

    const poll = setInterval(() => {
        const panel = document.querySelector('.container_gdrive');
        if (!panel) return;
        clearInterval(poll);

        // Initial state — no animation on page load
        const visible = panel.classList.contains('gdrive-visible');
        panel.style.display = visible ? '' : 'none';
        panel.style.pointerEvents = visible ? 'auto' : 'none';
        if (visible) panel.style.animation = `showedWidgets ${SHOW_DUR} forwards ease`;

        // Watch class changes (gdrive toggle or Save .hide)
        new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.attributeName !== 'class') continue;

                // .hide added by Save button — hide panel if visible
                if (panel.classList.contains('hide')) {
                    panel.style.pointerEvents = 'none';
                    if (panel.classList.contains('gdrive-visible')) {
                        panel.style.animation = `hideWidgets ${HIDE_DUR} forwards ease`;
                    }
                    continue;
                }

                const nowVisible = panel.classList.contains('gdrive-visible');
                if (nowVisible) {
                    panel.style.display = '';
                    panel.style.pointerEvents = 'auto';
                    void panel.offsetWidth; // force reflow → replay animation
                    panel.style.animation = `showedWidgets ${SHOW_DUR} forwards ease`;
                } else {
                    panel.style.animation = `hideWidgets ${HIDE_DUR} forwards ease`;
                    panel.style.pointerEvents = 'none';
                    setTimeout(() => {
                        if (!panel.classList.contains('gdrive-visible')) {
                            panel.style.display = 'none';
                            panel.style.animation = '';
                        }
                    }, 320);
                }
            }
        }).observe(panel, { attributes: true, attributeFilter: ['class'] });
    }, 100);
})();
