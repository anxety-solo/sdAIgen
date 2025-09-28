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

// Trigger file download of JSON content
function downloadJson(data, filename='widget_settings.json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Open file picker and send parsed JSON to Python callback
function openFilePicker(callbackName='importSettingsFromJS') {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.style.display = 'none';

    input.onchange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const jsonData = JSON.parse(text);
            google.colab.kernel.invokeFunction(callbackName, [jsonData], {});
        } catch (err) {
            // Notify Python of JSON parsing error using a registered callback
            google.colab.kernel.invokeFunction('showNotificationFromJS',
                ["Failed to parse JSON: " + err.message, "error"], {});
        }
    };

    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
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