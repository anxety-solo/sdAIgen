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