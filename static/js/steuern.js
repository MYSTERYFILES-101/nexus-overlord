/**
 * NEXUS OVERLORD v2.0 - Steuern JavaScript (Auftrag 4.1 + 4.2)
 * Interaktionen für Kachel 3: Projekt steuern
 */

// Globale Variable für Projekt-ID (wird aus URL extrahiert)
let projektId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Projekt-ID aus URL extrahieren
    const pathParts = window.location.pathname.split('/');
    const projektIndex = pathParts.indexOf('projekt');
    if (projektIndex !== -1 && pathParts[projektIndex + 1]) {
        projektId = parseInt(pathParts[projektIndex + 1]);
    }

    // DOM Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const chatContainer = document.getElementById('chatContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    // Action Buttons
    const btnAuftrag = document.getElementById('btnAuftrag');
    const btnFehler = document.getElementById('btnFehler');
    const btnAnalysieren = document.getElementById('btnAnalysieren');
    const btnUebergaben = document.getElementById('btnUebergaben');
    const btnExport = document.getElementById('btnExport');

    // Sidebar Overlay erstellen
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    // ========================================
    // SIDEBAR TOGGLE (Mobile)
    // ========================================

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', openSidebar);
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    overlay.addEventListener('click', closeSidebar);

    // ESC Taste schließt Sidebar
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });

    // ========================================
    // EINGABEFELD
    // ========================================

    // Auto-resize Textarea
    if (userInput) {
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });

        // Enter zum Senden (Shift+Enter für neue Zeile)
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Senden Button
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Nachricht zum Chat hinzufügen
        addChatMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';

        // Platzhalter-Antwort (wird in späteren Aufträgen erweitert)
        setTimeout(function() {
            addChatMessage('system', 'Diese Funktion wird in einem späteren Auftrag implementiert. Nutze die Buttons unten für spezifische Aktionen.');
        }, 500);
    }

    function addChatMessage(type, content) {
        // Leere Chat-Anzeige entfernen
        clearChatEmpty();

        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message chat-' + type;

        const timestamp = new Date().toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-sender">${type === 'user' ? 'Du' : 'NEXUS'}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${escapeHtml(content)}</div>
        `;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function clearChatEmpty() {
        const chatLeer = chatContainer.querySelector('.chat-leer');
        if (chatLeer) {
            chatLeer.remove();
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========================================
    // AUFTRAG BUTTON (Auftrag 4.2)
    // ========================================

    if (btnAuftrag) {
        btnAuftrag.addEventListener('click', function() {
            loadNextAuftrag();
        });
    }

    function loadNextAuftrag() {
        if (!projektId) {
            addChatMessage('system', 'Fehler: Projekt-ID nicht gefunden.');
            return;
        }

        // Button deaktivieren während des Ladens
        btnAuftrag.disabled = true;
        btnAuftrag.innerHTML = '<span class="btn-icon">&#8987;</span><span class="btn-text">Lädt...</span>';

        // Leere Chat-Anzeige entfernen
        clearChatEmpty();

        // API-Aufruf
        fetch(`/projekt/${projektId}/auftrag`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => response.text())
        .then(html => {
            // HTML in Chat-Container einfügen
            chatContainer.insertAdjacentHTML('beforeend', html);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Button wieder aktivieren
            btnAuftrag.disabled = false;
            btnAuftrag.innerHTML = '<span class="btn-icon">&#128196;</span><span class="btn-text">Auftrag</span>';
        })
        .catch(error => {
            console.error('Fehler beim Laden des Auftrags:', error);
            addChatMessage('system', 'Fehler beim Laden des Auftrags. Bitte versuche es erneut.');

            // Button wieder aktivieren
            btnAuftrag.disabled = false;
            btnAuftrag.innerHTML = '<span class="btn-icon">&#128196;</span><span class="btn-text">Auftrag</span>';
        });
    }

    // ========================================
    // FEHLER BUTTON + MODAL (Auftrag 4.3)
    // ========================================

    const fehlerModalOverlay = document.getElementById('fehlerModalOverlay');
    const fehlerModal = document.getElementById('fehlerModal');
    const fehlerModalClose = document.getElementById('fehlerModalClose');
    const fehlerModalCancel = document.getElementById('fehlerModalCancel');
    const fehlerAnalyzeBtn = document.getElementById('fehlerAnalyzeBtn');
    const fehlerInput = document.getElementById('fehlerInput');

    // Fehler Button öffnet Modal
    if (btnFehler) {
        btnFehler.addEventListener('click', function() {
            openFehlerModal();
        });
    }

    function openFehlerModal() {
        if (fehlerModalOverlay) {
            fehlerModalOverlay.classList.add('visible');
            document.body.style.overflow = 'hidden';
            if (fehlerInput) {
                fehlerInput.value = '';
                fehlerInput.focus();
            }
        }
    }

    function closeFehlerModal() {
        if (fehlerModalOverlay) {
            fehlerModalOverlay.classList.remove('visible');
            document.body.style.overflow = '';
        }
    }

    // Modal schließen Events
    if (fehlerModalClose) {
        fehlerModalClose.addEventListener('click', closeFehlerModal);
    }
    if (fehlerModalCancel) {
        fehlerModalCancel.addEventListener('click', closeFehlerModal);
    }
    if (fehlerModalOverlay) {
        fehlerModalOverlay.addEventListener('click', function(e) {
            if (e.target === fehlerModalOverlay) {
                closeFehlerModal();
            }
        });
    }

    // ESC schließt Modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && fehlerModalOverlay && fehlerModalOverlay.classList.contains('visible')) {
            closeFehlerModal();
        }
    });

    // Analysieren Button im Modal
    if (fehlerAnalyzeBtn) {
        fehlerAnalyzeBtn.addEventListener('click', function() {
            analyzeFehler();
        });
    }

    // Enter in Textarea (Shift+Enter für neue Zeile)
    if (fehlerInput) {
        fehlerInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                analyzeFehler();
            }
        });
    }

    function analyzeFehler() {
        const fehlerText = fehlerInput ? fehlerInput.value.trim() : '';

        if (!fehlerText) {
            alert('Bitte gib einen Fehler-Text ein.');
            return;
        }

        if (!projektId) {
            alert('Projekt-ID nicht gefunden.');
            return;
        }

        // Button deaktivieren
        if (fehlerAnalyzeBtn) {
            fehlerAnalyzeBtn.disabled = true;
            fehlerAnalyzeBtn.innerHTML = '<span class="btn-icon">&#8987;</span><span>Analysiere...</span>';
        }

        // Modal schließen
        closeFehlerModal();

        // Leere Chat-Anzeige entfernen
        clearChatEmpty();

        // User-Nachricht anzeigen
        addChatMessage('user', `Fehler melden: ${fehlerText.substring(0, 100)}${fehlerText.length > 100 ? '...' : ''}`);

        // API-Aufruf
        fetch(`/projekt/${projektId}/fehler`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `fehler_text=${encodeURIComponent(fehlerText)}`
        })
        .then(response => response.text())
        .then(html => {
            // HTML in Chat-Container einfügen
            chatContainer.insertAdjacentHTML('beforeend', html);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Button wieder aktivieren
            if (fehlerAnalyzeBtn) {
                fehlerAnalyzeBtn.disabled = false;
                fehlerAnalyzeBtn.innerHTML = '<span class="btn-icon">&#128269;</span><span>Analysieren</span>';
            }
        })
        .catch(error => {
            console.error('Fehler bei Analyse:', error);
            addChatMessage('system', 'Fehler bei der Analyse. Bitte versuche es erneut.');

            if (fehlerAnalyzeBtn) {
                fehlerAnalyzeBtn.disabled = false;
                fehlerAnalyzeBtn.innerHTML = '<span class="btn-icon">&#128269;</span><span>Analysieren</span>';
            }
        });
    }

    // ========================================
    // ACTION BUTTONS (Platzhalter für 4.4+)
    // ========================================

    // Analysieren Button
    if (btnAnalysieren) {
        btnAnalysieren.addEventListener('click', function() {
            showActionInfo('Analysieren', 'KI-Analyse starten - Diese Funktion wird in Auftrag 4.4 implementiert.');
        });
    }

    // Übergaben Button
    if (btnUebergaben) {
        btnUebergaben.addEventListener('click', function() {
            showActionInfo('Übergaben', 'Übergabe-Dokumente anzeigen - Diese Funktion wird in Auftrag 4.5 implementiert.');
        });
    }

    // Export Button
    if (btnExport) {
        btnExport.addEventListener('click', function() {
            showActionInfo('Export PDF', 'Projekt als PDF exportieren - Diese Funktion wird in Auftrag 4.6 implementiert.');
        });
    }

    function showActionInfo(action, message) {
        clearChatEmpty();
        addChatMessage('system', `[${action}] ${message}`);
    }

    // ========================================
    // PHASEN-NAVIGATION
    // ========================================

    const phaseItems = document.querySelectorAll('.phase-item');

    phaseItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const phaseId = this.dataset.phaseId;

            // Aktiv-Status aktualisieren
            phaseItems.forEach(function(p) {
                p.classList.remove('aktiv');
            });
            this.classList.add('aktiv');

            // TODO: Phase laden und anzeigen
            console.log('Phase ausgewählt:', phaseId);

            // Mobile: Sidebar schließen
            if (window.innerWidth <= 1024) {
                closeSidebar();
            }
        });
    });

    // ========================================
    // WINDOW RESIZE HANDLER
    // ========================================

    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 1024) {
                closeSidebar();
            }
        }, 250);
    });

    console.log('NEXUS OVERLORD - Steuern-Modul geladen (v4.2)');
});

// ========================================
// GLOBALE FUNKTIONEN (für onclick in HTML)
// ========================================

/**
 * Kopiert Auftrag-Text in die Zwischenablage (Auftrag 4.2)
 */
function copyAuftrag(auftragId) {
    const textElement = document.getElementById('auftragText' + auftragId);
    const feedbackElement = document.getElementById('copyFeedback' + auftragId);

    if (!textElement) {
        console.error('Auftrag-Text nicht gefunden:', auftragId);
        return;
    }

    const text = textElement.textContent;

    // Moderne Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showCopyFeedback(feedbackElement);
            })
            .catch(err => {
                console.error('Clipboard-Fehler:', err);
                fallbackCopy(text, feedbackElement);
            });
    } else {
        // Fallback für ältere Browser
        fallbackCopy(text, feedbackElement);
    }
}

/**
 * Fallback-Kopieren für ältere Browser
 */
function fallbackCopy(text, feedbackElement) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();

    try {
        document.execCommand('copy');
        showCopyFeedback(feedbackElement);
    } catch (err) {
        console.error('Fallback-Copy-Fehler:', err);
        alert('Kopieren fehlgeschlagen. Bitte manuell kopieren.');
    }

    document.body.removeChild(textarea);
}

/**
 * Zeigt Kopieren-Feedback an
 */
function showCopyFeedback(feedbackElement) {
    if (feedbackElement) {
        feedbackElement.style.display = 'block';
        setTimeout(() => {
            feedbackElement.style.display = 'none';
        }, 2000);
    }
}

/**
 * Markiert Auftrag als erledigt (Auftrag 4.2)
 */
function markAuftragFertig(auftragId) {
    // Projekt-ID aus URL extrahieren
    const pathParts = window.location.pathname.split('/');
    const projektIndex = pathParts.indexOf('projekt');
    const projektId = pathParts[projektIndex + 1];

    fetch(`/projekt/${projektId}/auftrag/${auftragId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'status=fertig'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Visuelles Feedback
            const messageElement = document.querySelector(`[data-auftrag-id="${auftragId}"]`);
            if (messageElement) {
                messageElement.classList.add('auftrag-erledigt');

                // Button ändern
                const fertigBtn = messageElement.querySelector('.btn-fertig');
                if (fertigBtn) {
                    fertigBtn.innerHTML = '<span class="btn-icon">&#10003;</span><span class="btn-text">Erledigt!</span>';
                    fertigBtn.disabled = true;
                    fertigBtn.classList.add('btn-success');
                }
            }
        } else {
            alert('Fehler: ' + (data.error || 'Unbekannter Fehler'));
        }
    })
    .catch(error => {
        console.error('Fehler beim Status-Update:', error);
        alert('Fehler beim Aktualisieren des Status.');
    });
}

/**
 * Kopiert Fehler-Auftrag in die Zwischenablage (Auftrag 4.3)
 */
function copyFehlerAuftrag(fehlerId) {
    const textElement = document.getElementById('fehlerAuftrag' + fehlerId);
    const feedbackElement = document.getElementById('copyFehlerFeedback' + fehlerId);

    if (!textElement) {
        console.error('Fehler-Auftrag nicht gefunden:', fehlerId);
        return;
    }

    const text = textElement.textContent;

    // Moderne Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showCopyFeedback(feedbackElement);
            })
            .catch(err => {
                console.error('Clipboard-Fehler:', err);
                fallbackCopy(text, feedbackElement);
            });
    } else {
        fallbackCopy(text, feedbackElement);
    }
}

/**
 * Sendet Feedback zur Fehler-Lösung (Auftrag 4.3)
 */
function sendFehlerFeedback(fehlerId, erfolg) {
    const pathParts = window.location.pathname.split('/');
    const projektIndex = pathParts.indexOf('projekt');
    const projektId = pathParts[projektIndex + 1];

    fetch(`/projekt/${projektId}/fehler/${fehlerId}/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `erfolg=${erfolg}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Feedback-Buttons ausblenden und Nachricht anzeigen
            const feedbackResponse = document.getElementById('feedbackResponse' + fehlerId);
            const messageElement = document.querySelector(`[data-fehler-id="${fehlerId}"]`);

            if (messageElement) {
                // Feedback-Buttons verstecken
                const feedbackBtns = messageElement.querySelectorAll('.btn-success-feedback, .btn-fail-feedback');
                feedbackBtns.forEach(btn => btn.style.display = 'none');
            }

            if (feedbackResponse) {
                feedbackResponse.style.display = 'block';
                feedbackResponse.innerHTML = erfolg
                    ? '<span class="feedback-success">&#10003; Danke für dein Feedback! Die Erfolgsrate wurde aktualisiert.</span>'
                    : '<span class="feedback-fail">&#10003; Feedback gespeichert. Wir verbessern unsere Lösungen.</span>';
            }
        }
    })
    .catch(error => {
        console.error('Fehler beim Feedback:', error);
    });
}
