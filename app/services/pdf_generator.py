"""
NEXUS OVERLORD v2.0 - PDF Generator (Auftrag 6.1)

Erstellt professionelle PDF-Dokumentationen fuer Projekte.
Nutzt reportlab fuer PDF-Generierung mit Template-System.
"""

import io
import logging
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Logger
logger = logging.getLogger(__name__)


# ========================================
# FARBEN (NEXUS OVERLORD Design)
# ========================================

COLORS = {
    'primary': colors.HexColor('#3b82f6'),      # Blau
    'secondary': colors.HexColor('#6b7280'),    # Grau
    'dark': colors.HexColor('#1f2937'),         # Dunkel
    'light': colors.HexColor('#f3f4f6'),        # Hell
    'success': colors.HexColor('#22c55e'),      # Gruen
    'warning': colors.HexColor('#eab308'),      # Gelb
    'error': colors.HexColor('#ef4444'),        # Rot
    'text': colors.HexColor('#374151'),         # Text
    'muted': colors.HexColor('#9ca3af'),        # Gedaempft
    'white': colors.white,
    'black': colors.black,
}


# ========================================
# STYLES
# ========================================

def get_custom_styles() -> dict:
    """
    Erstellt benutzerdefinierte Paragraph-Styles.

    Returns:
        dict: Style-Dictionary
    """
    styles = getSampleStyleSheet()

    # Alle Custom Styles mit "Nx" Prefix um Konflikte zu vermeiden
    custom_styles = {
        'TitleMain': ParagraphStyle(
            name='TitleMain',
            parent=styles['Title'],
            fontSize=32,
            textColor=COLORS['primary'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ),
        'NxSubtitle': ParagraphStyle(
            name='NxSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=COLORS['secondary'],
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ),
        'ChapterTitle': ParagraphStyle(
            name='ChapterTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=COLORS['dark'],
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ),
        'SectionTitle': ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=COLORS['primary'],
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ),
        'SubsectionTitle': ParagraphStyle(
            name='SubsectionTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=COLORS['dark'],
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ),
        'NxCode': ParagraphStyle(
            name='NxCode',
            parent=styles['Normal'],
            fontSize=9,
            textColor=COLORS['dark'],
            backColor=COLORS['light'],
            fontName='Courier',
            leftIndent=10,
            rightIndent=10,
            spaceBefore=5,
            spaceAfter=5,
            leading=12
        ),
        'NxBullet': ParagraphStyle(
            name='NxBullet',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['text'],
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4,
            fontName='Helvetica'
        ),
        'NxFooter': ParagraphStyle(
            name='NxFooter',
            parent=styles['Normal'],
            fontSize=8,
            textColor=COLORS['muted'],
            alignment=TA_CENTER,
            fontName='Helvetica'
        ),
        'InfoBox': ParagraphStyle(
            name='InfoBox',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['dark'],
            backColor=colors.HexColor('#e0f2fe'),
            spaceBefore=10,
            spaceAfter=10,
            fontName='Helvetica',
            leftIndent=10,
            rightIndent=10
        ),
        'WarningBox': ParagraphStyle(
            name='WarningBox',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['dark'],
            backColor=colors.HexColor('#fef3c7'),
            spaceBefore=10,
            spaceAfter=10,
            fontName='Helvetica',
            leftIndent=10,
            rightIndent=10
        ),
        'TOCEntry': ParagraphStyle(
            name='TOCEntry',
            parent=styles['Normal'],
            fontSize=11,
            textColor=COLORS['text'],
            leftIndent=0,
            spaceAfter=8,
            fontName='Helvetica'
        ),
        'TOCSubEntry': ParagraphStyle(
            name='TOCSubEntry',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['secondary'],
            leftIndent=15,
            spaceAfter=4,
            fontName='Helvetica'
        ),
    }

    # Modifiziere Standard BodyText
    styles['BodyText'].fontSize = 10
    styles['BodyText'].textColor = COLORS['text']
    styles['BodyText'].spaceAfter = 6
    styles['BodyText'].alignment = TA_JUSTIFY
    styles['BodyText'].fontName = 'Helvetica'
    styles['BodyText'].leading = 14

    # Fuege alle Custom Styles hinzu (mit Try/Except fuer bereits existierende)
    for name, style in custom_styles.items():
        try:
            styles.add(style)
        except KeyError:
            # Style existiert bereits, aktualisiere ihn
            pass

    return styles


# ========================================
# PDF GENERATOR KLASSE
# ========================================

class NexusPDFGenerator:
    """
    PDF-Generator fuer NEXUS OVERLORD Projekt-Dokumentation.

    Verwendung:
        pdf = NexusPDFGenerator()
        pdf.add_title_page("Projekt Name", "Beschreibung")
        pdf.add_toc([("Kapitel 1", 1), ("Kapitel 2", 2)])
        pdf.add_chapter("Kapitel 1", "Inhalt...")
        buffer = pdf.build()
    """

    def __init__(self, title: str = "NEXUS OVERLORD Dokumentation"):
        """
        Initialisiert den PDF-Generator.

        Args:
            title: Dokument-Titel
        """
        self.title = title
        self.buffer = io.BytesIO()
        self.styles = get_custom_styles()
        self.elements = []
        self.toc_entries = []
        self.page_count = 0

        # Dokument erstellen
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm,
            title=title,
            author="NEXUS OVERLORD v2.0"
        )

        logger.debug(f"PDF-Generator initialisiert: {title}")

    def _header_footer(self, canvas, doc):
        """
        Zeichnet Header und Footer auf jeder Seite.
        """
        canvas.saveState()

        # Header-Linie
        canvas.setStrokeColor(COLORS['primary'])
        canvas.setLineWidth(0.5)
        canvas.line(2*cm, A4[1] - 1.8*cm, A4[0] - 2*cm, A4[1] - 1.8*cm)

        # Header-Text (links)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COLORS['muted'])
        canvas.drawString(2*cm, A4[1] - 1.5*cm, "NEXUS OVERLORD v2.0")

        # Header-Text (rechts)
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.5*cm, self.title)

        # Footer-Linie
        canvas.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)

        # Seitenzahl (mittig)
        canvas.drawCentredString(A4[0]/2, 1*cm, f"Seite {doc.page}")

        # Datum (links)
        canvas.drawString(2*cm, 1*cm, datetime.now().strftime("%d.%m.%Y"))

        canvas.restoreState()

    def add_title_page(
        self,
        projekt_name: str,
        beschreibung: str = "",
        status: str = "Aktiv",
        version: str = "2.0"
    ):
        """
        Fuegt eine Titelseite hinzu.

        Args:
            projekt_name: Name des Projekts
            beschreibung: Kurze Beschreibung
            status: Projekt-Status
            version: Version
        """
        # Spacer fuer vertikale Zentrierung
        self.elements.append(Spacer(1, 4*cm))

        # Haupttitel
        self.elements.append(Paragraph(
            f"<b>{projekt_name}</b>",
            self.styles['TitleMain']
        ))

        # Untertitel
        self.elements.append(Paragraph(
            "Projekt-Dokumentation",
            self.styles['NxSubtitle']
        ))

        self.elements.append(Spacer(1, 1*cm))

        # Horizontale Linie
        self.elements.append(HRFlowable(
            width="60%",
            thickness=2,
            color=COLORS['primary'],
            spaceBefore=10,
            spaceAfter=10,
            hAlign='CENTER'
        ))

        self.elements.append(Spacer(1, 1*cm))

        # Beschreibung
        if beschreibung:
            self.elements.append(Paragraph(
                beschreibung,
                self.styles['NxSubtitle']
            ))
            self.elements.append(Spacer(1, 2*cm))

        # Info-Tabelle
        info_data = [
            ["Version:", version],
            ["Status:", status],
            ["Erstellt:", datetime.now().strftime("%d.%m.%Y %H:%M")],
            ["Generator:", "NEXUS OVERLORD v2.0"]
        ]

        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), COLORS['secondary']),
            ('TEXTCOLOR', (1, 0), (1, -1), COLORS['text']),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        self.elements.append(info_table)

        # Seitenumbruch
        self.elements.append(PageBreak())

        logger.debug("Titelseite hinzugefuegt")

    def add_toc(self, entries: list[tuple[str, int]] = None):
        """
        Fuegt ein Inhaltsverzeichnis hinzu.

        Args:
            entries: Liste von (Titel, Seitenzahl) Tupeln
                    Falls None, werden gesammelte Eintraege verwendet
        """
        self.elements.append(Paragraph(
            "Inhaltsverzeichnis",
            self.styles['ChapterTitle']
        ))

        self.elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=COLORS['primary'],
            spaceBefore=5,
            spaceAfter=15
        ))

        entries = entries or self.toc_entries

        if not entries:
            self.elements.append(Paragraph(
                "Keine Eintraege verfuegbar.",
                self.styles['BodyText']
            ))
        else:
            for title, level in entries:
                style = 'TOCEntry' if level == 1 else 'TOCSubEntry'
                prefix = "" if level == 1 else "    "
                self.elements.append(Paragraph(
                    f"{prefix}{title}",
                    self.styles[style]
                ))

        self.elements.append(PageBreak())
        logger.debug(f"TOC hinzugefuegt mit {len(entries)} Eintraegen")

    def add_chapter(self, title: str, content: str = "", add_to_toc: bool = True):
        """
        Fuegt ein Kapitel hinzu.

        Args:
            title: Kapitel-Titel
            content: Kapitel-Inhalt (kann Absaetze enthalten)
            add_to_toc: Zum Inhaltsverzeichnis hinzufuegen
        """
        if add_to_toc:
            self.toc_entries.append((title, 1))

        self.elements.append(Paragraph(title, self.styles['ChapterTitle']))
        self.elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=COLORS['primary'],
            spaceBefore=0,
            spaceAfter=10
        ))

        if content:
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    self.elements.append(Paragraph(
                        paragraph.strip(),
                        self.styles['BodyText']
                    ))

        logger.debug(f"Kapitel hinzugefuegt: {title}")

    def add_section(self, title: str, content: str = "", add_to_toc: bool = True):
        """
        Fuegt einen Abschnitt hinzu (H2).

        Args:
            title: Abschnitt-Titel
            content: Abschnitt-Inhalt
            add_to_toc: Zum Inhaltsverzeichnis hinzufuegen
        """
        if add_to_toc:
            self.toc_entries.append((title, 2))

        self.elements.append(Paragraph(title, self.styles['SectionTitle']))

        if content:
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    self.elements.append(Paragraph(
                        paragraph.strip(),
                        self.styles['BodyText']
                    ))

        logger.debug(f"Abschnitt hinzugefuegt: {title}")

    def add_subsection(self, title: str, content: str = ""):
        """
        Fuegt einen Unter-Abschnitt hinzu (H3).

        Args:
            title: Titel
            content: Inhalt
        """
        self.elements.append(Paragraph(title, self.styles['SubsectionTitle']))

        if content:
            self.elements.append(Paragraph(content, self.styles['BodyText']))

    def add_paragraph(self, text: str, style: str = 'BodyText'):
        """
        Fuegt einen Absatz hinzu.

        Args:
            text: Text-Inhalt
            style: Style-Name
        """
        self.elements.append(Paragraph(text, self.styles[style]))

    def add_bullet_list(self, items: list[str]):
        """
        Fuegt eine Bullet-Liste hinzu.

        Args:
            items: Liste von Eintraegen
        """
        for item in items:
            self.elements.append(Paragraph(
                f"• {item}",
                self.styles['NxBullet']
            ))

    def add_numbered_list(self, items: list[str]):
        """
        Fuegt eine nummerierte Liste hinzu.

        Args:
            items: Liste von Eintraegen
        """
        for i, item in enumerate(items, 1):
            self.elements.append(Paragraph(
                f"{i}. {item}",
                self.styles['NxBullet']
            ))

    def add_code_block(self, code: str):
        """
        Fuegt einen Code-Block hinzu.

        Args:
            code: Code-Text
        """
        # Code in einzelne Zeilen aufteilen
        lines = code.strip().split('\n')
        for line in lines:
            self.elements.append(Paragraph(
                line.replace(' ', '&nbsp;'),
                self.styles['NxCode']
            ))

    def add_table(
        self,
        data: list[list[str]],
        col_widths: list[float] = None,
        header: bool = True
    ):
        """
        Fuegt eine Tabelle hinzu.

        Args:
            data: 2D-Liste mit Tabellendaten
            col_widths: Spaltenbreiten in cm (optional)
            header: Erste Zeile als Header formatieren
        """
        if not data:
            return

        # Spaltenbreiten berechnen
        if col_widths:
            widths = [w*cm for w in col_widths]
        else:
            num_cols = len(data[0])
            available = 17*cm  # A4 minus Margins
            widths = [available/num_cols] * num_cols

        table = Table(data, colWidths=widths)

        # Basis-Style
        style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['light']),
        ]

        # Header-Style
        if header and len(data) > 0:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
            ])

        # Alternating Rows
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i), COLORS['light'])
                )

        table.setStyle(TableStyle(style_commands))
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.5*cm))

        logger.debug(f"Tabelle hinzugefuegt: {len(data)} Zeilen")

    def add_info_box(self, text: str):
        """
        Fuegt eine Info-Box hinzu.

        Args:
            text: Info-Text
        """
        self.elements.append(Paragraph(
            f"ℹ️ {text}",
            self.styles['InfoBox']
        ))

    def add_warning_box(self, text: str):
        """
        Fuegt eine Warning-Box hinzu.

        Args:
            text: Warning-Text
        """
        self.elements.append(Paragraph(
            f"⚠️ {text}",
            self.styles['WarningBox']
        ))

    def add_spacer(self, height: float = 0.5):
        """
        Fuegt einen Abstand hinzu.

        Args:
            height: Hoehe in cm
        """
        self.elements.append(Spacer(1, height*cm))

    def add_page_break(self):
        """Fuegt einen Seitenumbruch hinzu."""
        self.elements.append(PageBreak())

    def add_horizontal_line(self, width: str = "100%", thickness: float = 1):
        """
        Fuegt eine horizontale Linie hinzu.

        Args:
            width: Breite (z.B. "100%" oder "50%")
            thickness: Linienstaerke
        """
        self.elements.append(HRFlowable(
            width=width,
            thickness=thickness,
            color=COLORS['secondary'],
            spaceBefore=5,
            spaceAfter=5
        ))

    def add_status_badge(self, status: str) -> str:
        """
        Gibt HTML fuer Status-Badge zurueck.

        Args:
            status: Status-Text

        Returns:
            str: HTML mit Farbe
        """
        status_colors = {
            'fertig': '#22c55e',
            'in_arbeit': '#3b82f6',
            'offen': '#6b7280',
            'aktiv': '#22c55e',
            'veraltet': '#ef4444',
        }
        color = status_colors.get(status.lower(), '#6b7280')
        return f'<font color="{color}"><b>[{status.upper()}]</b></font>'

    def build(self) -> bytes:
        """
        Baut das PDF und gibt es als Bytes zurueck.

        Returns:
            bytes: PDF-Daten
        """
        logger.info(f"Baue PDF: {len(self.elements)} Elemente")

        self.doc.build(
            self.elements,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer
        )

        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()

        logger.info(f"PDF erstellt: {len(pdf_bytes)} Bytes")
        return pdf_bytes


# ========================================
# CONVENIENCE FUNKTIONEN
# ========================================

def create_simple_pdf(title: str, content: str) -> bytes:
    """
    Erstellt ein einfaches PDF mit Titel und Inhalt.

    Args:
        title: Dokument-Titel
        content: Text-Inhalt

    Returns:
        bytes: PDF-Daten
    """
    pdf = NexusPDFGenerator(title)
    pdf.add_title_page(title)
    pdf.add_chapter("Inhalt", content)
    return pdf.build()


def create_test_pdf() -> bytes:
    """
    Erstellt ein Test-PDF zur Ueberpruefung des Generators.

    Returns:
        bytes: PDF-Daten
    """
    pdf = NexusPDFGenerator("NEXUS OVERLORD - Test-PDF")

    # Titelseite
    pdf.add_title_page(
        projekt_name="NEXUS OVERLORD",
        beschreibung="Test-Dokumentation fuer PDF-Generator",
        status="Test",
        version="2.0"
    )

    # Inhaltsverzeichnis (wird spaeter gefuellt)
    toc_entries = [
        ("1. Uebersicht", 1),
        ("2. Funktionen", 1),
        ("   2.1 Tabellen", 2),
        ("   2.2 Listen", 2),
        ("   2.3 Code-Bloecke", 2),
        ("3. Zusammenfassung", 1),
    ]
    pdf.add_toc(toc_entries)

    # Kapitel 1
    pdf.add_chapter("1. Uebersicht")
    pdf.add_paragraph(
        "Dies ist ein Test-PDF, das alle Funktionen des NEXUS OVERLORD "
        "PDF-Generators demonstriert. Der Generator unterstuetzt verschiedene "
        "Elemente wie Kapitel, Abschnitte, Tabellen, Listen und Code-Bloecke."
    )
    pdf.add_spacer()
    pdf.add_info_box("Dies ist eine Info-Box fuer wichtige Hinweise.")
    pdf.add_warning_box("Dies ist eine Warning-Box fuer Warnungen.")

    # Kapitel 2
    pdf.add_chapter("2. Funktionen")

    # Abschnitt 2.1 - Tabellen
    pdf.add_section("2.1 Tabellen")
    pdf.add_paragraph("Beispiel einer Tabelle mit Projektdaten:")
    pdf.add_table([
        ["Phase", "Name", "Status", "Fortschritt"],
        ["1", "Grundgeruest", "Fertig", "100%"],
        ["2", "KI-Integration", "Fertig", "100%"],
        ["3", "Steuerung", "Fertig", "100%"],
        ["4", "Features", "Fertig", "100%"],
        ["5", "Fehler-DB", "Fertig", "100%"],
        ["6", "PDF Export", "In Arbeit", "50%"],
    ], col_widths=[2, 5, 3, 3])

    # Abschnitt 2.2 - Listen
    pdf.add_section("2.2 Listen")
    pdf.add_paragraph("Bullet-Liste:")
    pdf.add_bullet_list([
        "Erstes Element",
        "Zweites Element",
        "Drittes Element"
    ])
    pdf.add_spacer(0.3)
    pdf.add_paragraph("Nummerierte Liste:")
    pdf.add_numbered_list([
        "Schritt eins",
        "Schritt zwei",
        "Schritt drei"
    ])

    # Abschnitt 2.3 - Code
    pdf.add_section("2.3 Code-Bloecke")
    pdf.add_paragraph("Beispiel Python-Code:")
    pdf.add_code_block("""def hello_world():
    print("Hello, NEXUS OVERLORD!")
    return True

# Aufruf
hello_world()""")

    # Kapitel 3
    pdf.add_page_break()
    pdf.add_chapter("3. Zusammenfassung")
    pdf.add_paragraph(
        "Der PDF-Generator funktioniert korrekt und kann fuer die "
        "Projekt-Dokumentation verwendet werden. Alle Basis-Funktionen "
        "sind implementiert und getestet."
    )

    pdf.add_spacer()
    pdf.add_horizontal_line()
    pdf.add_paragraph(
        "Erstellt mit NEXUS OVERLORD v2.0 PDF-Generator",
        style='NxFooter'
    )

    return pdf.build()
