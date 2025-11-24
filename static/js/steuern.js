/**
 * NEXUS OVERLORD v2.0 - Steuern JavaScript (Auftrag 4.1)
 * Interaktionen für Kachel 3: Projekt steuern
 */

document.addEventListener('DOMContentLoaded', function() {
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

        // Nachricht zum Chat hinzufügen (Platzhalter - Funktion kommt später)
        addChatMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';

        // TODO: Auftrag 4.2+ - API-Aufruf für Nachricht
        console.log('Nachricht gesendet:', message);

        // Platzhalter-Antwort
        setTimeout(function() {
            addChatMessage('system', 'Diese Funktion wird in einem späteren Auftrag implementiert. Nutze die Buttons unten für spezifische Aktionen.');
        }, 500);
    }

    function addChatMessage(type, content) {
        // Leere Chat-Anzeige entfernen
        const chatLeer = chatContainer.querySelector('.chat-leer');
        if (chatLeer) {
            chatLeer.remove();
        }

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

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========================================
    // ACTION BUTTONS (Platzhalter)
    // ========================================

    // Auftrag Button
    if (btnAuftrag) {
        btnAuftrag.addEventListener('click', function() {
            showActionInfo('Auftrag', 'Nächsten Auftrag starten - Diese Funktion wird in Auftrag 4.2 implementiert.');
        });
    }

    // Fehler Button
    if (btnFehler) {
        btnFehler.addEventListener('click', function() {
            showActionInfo('Fehler', 'Problem melden - Diese Funktion wird in Auftrag 4.3 implementiert.');
        });
    }

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
            addChatMessage('system', 'Phase ' + this.querySelector('.phase-nummer').textContent + ' ausgewählt. Die Phasen-Details werden in einem späteren Auftrag geladen.');

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

    // ========================================
    // CHAT MESSAGE STYLING (für spätere Nutzung)
    // ========================================

    // CSS für Chat-Nachrichten dynamisch hinzufügen
    const chatStyles = document.createElement('style');
    chatStyles.textContent = `
        .chat-message {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 12px;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            margin-left: 50px;
        }

        .chat-system {
            background: #f5f7fa;
            color: #333;
            margin-right: 50px;
            border-left: 4px solid #667eea;
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }

        .chat-user .message-header {
            color: rgba(255, 255, 255, 0.8);
        }

        .chat-system .message-header {
            color: #999;
        }

        .message-sender {
            font-weight: bold;
        }

        .message-content {
            line-height: 1.5;
            white-space: pre-wrap;
        }

        @media (max-width: 768px) {
            .chat-user, .chat-system {
                margin-left: 0;
                margin-right: 0;
            }
        }
    `;
    document.head.appendChild(chatStyles);

    console.log('NEXUS OVERLORD - Steuern-Modul geladen');
});
