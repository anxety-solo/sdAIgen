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

// Hide Notification PopUp
function hideNotification(delay = 2500) {
    setTimeout(() => {
        const popup = document.querySelector('.notification-popup');
        if (popup) {
            setTimeout(() => {
                popup.classList.add('hidden')
                popup.classList.remove('visible')
            }, 500);
        };
    }, delay);
}