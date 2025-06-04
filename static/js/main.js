// Sayaç animasyonu
function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-count'));
    const duration = 2000;
    const step = target / duration * 10;
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 10);
}

// Sayfa yüklendiğinde sayaçları başlat
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-count]').forEach(animateCounter);
}); 