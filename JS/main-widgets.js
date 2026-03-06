// Toggle container visibility and extension (Custom Downloads)
function toggleContainer() {
    const SHOW_CLASS = 'showed';
    const elements = {
        downloadContainer: document.querySelector('.container_cdl'),
        info: document.querySelector('.info'),
        empowerment: document.querySelector('.empowerment')
    };

    elements.downloadContainer.classList.toggle('expanded');
    elements.info.classList.toggle(SHOW_CLASS);
    elements.empowerment.classList.toggle(SHOW_CLASS);
}

// Show/Hide Notification
function showNotification(message, type='info', duration=2500) {
    const ICONS = { success:'✅', error:'❌', info:'💡', warning:'⚠️' };
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

    // Hide и remove
    setTimeout(() => {
        popup.classList.remove('show'); // fadeOut
        setTimeout(() => popup.remove(), 500);
    }, duration);
}

// GDrive Symlinks Panel — show/hide with showedWidgets/hideWidgets animation (faster speed)
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

        // Watch for class changes (gdrive button toggle or Save .hide)
        new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.attributeName !== 'class') continue;

                // .hide added by Save button — trigger hideWidgets animation if panel is visible
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
                    void panel.offsetWidth; // force reflow → animation replays
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