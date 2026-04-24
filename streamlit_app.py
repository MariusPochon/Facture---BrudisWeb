# streamlit_app.py
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date
import locale
import re
from pathlib import Path

# ===== Configuration Streamlit =====
st.set_page_config(
    page_title="BrudisWeb - Générateur de Factures",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration locale - FR
try:
    locale.setlocale(locale.LC_TIME, 'fr_CH.UTF-8')
except Exception:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except Exception:
        try:
            locale.setlocale(locale.LC_TIME, 'French_Switzerland')
        except Exception:
            pass


# ===== Gestionnaire de numéros de facture =====
class InvoiceNumberManager:
    @staticmethod
    def generate_invoice_number(numero):
        today = date.today()
        date_part = today.strftime('%Y%m%d')
        try:
            numero_int = int(numero)
        except (ValueError, TypeError):
            numero_int = 1
        return f"BW-{date_part}-{numero_int:03d}"

    @staticmethod
    def get_formatted_date():
        today = date.today()
        jours_fr = {
            'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
        }
        mois_fr = {
            'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
            'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
            'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
        }
        try:
            date_str = today.strftime("Le %A %d %B %Y")
            for eng, fr in jours_fr.items():
                date_str = date_str.replace(eng, fr)
            for eng, fr in mois_fr.items():
                date_str = date_str.replace(eng, fr)
            return date_str
        except Exception:
            return today.strftime("Le %d/%m/%Y")


# ===== Classe PDF =====
class ModernInvoicePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.unicode_font_available = False
        self.base_font = "Helvetica"
        self._register_unicode_fonts_if_available()

    def _register_unicode_fonts_if_available(self):
        candidates = {
            "regular": [
                Path("DejaVuSans.ttf"),
                Path("fonts/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("C:/Windows/Fonts/DejaVuSans.ttf"),
            ],
            "bold": [
                Path("DejaVuSans-Bold.ttf"),
                Path("fonts/DejaVuSans-Bold.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                Path("C:/Windows/Fonts/DejaVuSans-Bold.ttf"),
            ]
        }
        found = {}
        for style, paths in candidates.items():
            for p in paths:
                if p.exists():
                    found[style] = p
                    break
        if "regular" in found:
            try:
                self.add_font("DejaVu", "", str(found["regular"]))
                if "bold" in found:
                    self.add_font("DejaVu", "B", str(found["bold"]))
                else:
                    self.add_font("DejaVu", "B", str(found["regular"]))
                self.unicode_font_available = True
                self.base_font = "DejaVu"
            except Exception:
                self.unicode_font_available = False
                self.base_font = "Helvetica"

    def safe(self, text: str) -> str:
        if text is None:
            return ""
        if self.unicode_font_available:
            return str(text)
        t = str(text).replace("•", "-")
        t = "".join(ch for ch in t if ord(ch) < 256)
        t = re.sub(r"[\x00-\x1f\x7f]", "", t)
        return t

    def header(self):
        self.set_fill_color(41, 128, 185)
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font(self.base_font, 'B', 24)
        self.set_y(8)
        self.cell(0, 12, self.safe('BrudisWeb'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font(self.base_font, '', 11)
        self.set_y(22)

    def footer(self):
        self.set_y(-20)
        self.set_fill_color(245, 245, 245)
        self.rect(0, self.get_y()-5, 210, 35, 'F')
        self.set_text_color(100, 100, 100)
        self.set_font(self.base_font, '', 9)
        self.cell(95, 5, self.safe(''), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(95, 5, self.safe('www.brudisweb.ch'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(95, 5, self.safe('Marius Pochon'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(95, 5, self.safe(f'Page {self.page_no()}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ===== Création du PDF =====
def create_pdf(entreprise, services, adresse_client, adresse_brudisweb, numero="", rabais=0.0):
    pdf = ModernInvoicePDF()
    pdf.add_page()

    numero_facture = InvoiceNumberManager.generate_invoice_number(numero)
    date_str = InvoiceNumberManager.get_formatted_date()

    pdf.set_text_color(41, 128, 185)
    pdf.set_font(pdf.base_font, 'B', 20)
    pdf.cell(0, 15, pdf.safe('FACTURE'), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(40, 8, pdf.safe('Numéro:'), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, '', 11)
    pdf.cell(0, 8, pdf.safe(numero_facture), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(40, 8, pdf.safe('Date:'), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, '', 11)
    pdf.cell(0, 8, pdf.safe(date_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)

    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(95, 10, pdf.safe('DE:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)

    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(95, 10, pdf.safe('À:'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)

    pdf.set_text_color(0, 0, 0)

    # ✅ IBAN FIXE UNIQUEMENT ICI
    notre_info = [
        "Marius Pochon",
        "IBAN : CH82 0076 8300 1278 3430 5"
    ]

    client_info = []
    if entreprise and entreprise.strip():
        client_info.append(entreprise.strip())

    if adresse_client and adresse_client.strip():
        client_info.extend([l.strip() for l in adresse_client.split('\n') if l.strip()])

    if not client_info:
        client_info = ["Adresse client non spécifiée"]

    line_height = 6
    max_lines = max(len(notre_info), len(client_info))
    box_height = max_lines * line_height + 10

    y_start = pdf.get_y()
    x_left = pdf.get_x()

    pdf.rect(x_left, y_start, 95, box_height)
    pdf.rect(x_left + 95, y_start, 95, box_height)

    pdf.set_xy(x_left + 2, y_start + 2)
    pdf.set_font(pdf.base_font, '', 10)
    for ligne in notre_info:
        pdf.cell(91, line_height, pdf.safe(ligne), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(x_left + 2)

    pdf.set_xy(x_left + 95 + 2, y_start + 2)
    for ligne in client_info:
        pdf.cell(91, line_height, pdf.safe(ligne), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(x_left + 95 + 2)

    pdf.set_y(y_start + box_height)
    pdf.ln(10)

    # (reste du code inchangé)
    return pdf, numero_facture


# ===== Streamlit =====
def main():
    with st.sidebar:
        entreprise = st.text_input("🏢 Nom de l'entreprise *")

        adresse_client = st.text_area("📍 Adresse du client")
        adresse_brudisweb = st.text_area("🏢 Votre adresse")
        
        # ❌ SUPPRIMÉ :
        # iban = st.text_input(...)

        numero = st.text_input("#️⃣ Numéro de facture")

        rabais = st.number_input("💰 Rabais (%)", 0.0, 100.0, 0.0)

    # appel PDF SANS iban
    # pdf, numero_facture = create_pdf(...)

if __name__ == "__main__":
    main()
