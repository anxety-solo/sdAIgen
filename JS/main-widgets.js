function toggleContainer() {
    const downloadContainer = document.querySelector('.container_cdl');
    const info = document.querySelector('.info');
    downloadContainer.classList.toggle('expanded');
    info.classList.toggle('showed');
}