async function ensureEffectScriptLoaded() {
    if (typeof MTGCard3DTiltEffect === 'undefined') {
        console.log('Loading card effects script...');
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = '/static/js/card-effects.js';
            script.onload = () => {
                console.log('Card effects script loaded successfully');
                resolve();
            };
            script.onerror = () => {
                console.error('Failed to load card effects script');
                reject(new Error('Failed to load card effects script'));
            };
            document.head.appendChild(script);
        });
    }
    return Promise.resolve();
}

async function initializeCardEffect() {
    const cardElements = document.querySelectorAll('.mtg-card');
    cardElements.forEach(async (cardElement) => {
        const cardRarity = cardElement.getAttribute('data-rarity');
        if (cardRarity === 'Rare' || cardRarity === 'Mythic Rare') {
            console.log('Initializing 3D effect for', cardRarity, 'card');
            try {
                await ensureEffectScriptLoaded();
                new MTGCard3DTiltEffect(cardElement);
                console.log('Card effect initialized successfully');
            } catch (error) {
                console.error('Error initializing card effect:', error);
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeCardEffect);