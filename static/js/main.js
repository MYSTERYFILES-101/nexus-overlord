/**
 * NEXUS OVERLORD v2.0 - Main JavaScript
 */

console.log('NEXUS OVERLORD v2.0 - Loaded');

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('NEXUS OVERLORD - Ready');

    // Event Listeners für Kacheln
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            alert('Funktion wird in späteren Phasen implementiert!');
        });
    });
});
