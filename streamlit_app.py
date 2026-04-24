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
        self.ln(15)

    def footer(self):
        self.set_y(-20)
        self.set_fill_color(245, 245, 245)
        self.rect(0, self.get_y()-5, 210, 35, 'F')
        self.set_text_color(100, 100, 100)
        self.set_font(self.base_font, '', 9)
        self.cell(95, 5, self.safe('www.brudisweb.ch'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(95, 5, self.safe('Marius Pochon'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(95, 5, self.safe(f'Page {self.page_no()}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ===== Création du PDF =====
def create_pdf(entreprise, services, adresse_client, adresse_brudisweb, iban="", numero=""):
    pdf = ModernInvoicePDF()
    pdf.add_page()

    numero_facture = InvoiceNumberManager.generate_invoice_number(numero)
    date_str = InvoiceNumberManager.get_formatted_date()

    # En-tête facture
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

    # Section facturation - Headers
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(95, 10, pdf.safe('DE:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)

    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(95, 10, pdf.safe('À:'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)

    pdf.set_text_color(0, 0, 0)

    # --- Préparation des informations ---
    notre_info = [
        "Marius Pochon",
        "contact@brudisweb.ch"
    ]
    
    # Traitement de l'adresse BrudisWeb avec gestion correcte des retours à la ligne
    if adresse_brudisweb and adresse_brudisweb.strip():
        # Séparer les lignes et filtrer les lignes vides
        lignes_adresse = [ligne.strip() for ligne in adresse_brudisweb.split('\n') if ligne.strip()]
        notre_info.extend(lignes_adresse)
    
    if iban and iban.strip():
        notre_info.append(f"IBAN: {iban.strip()}")

    # --- Infos client ---
    client_info = []
    if entreprise and entreprise.strip():
        client_info.append(entreprise.strip())
    
    # Traitement de l'adresse client avec gestion correcte des retours à la ligne
    if adresse_client and adresse_client.strip():
        # Séparer les lignes et filtrer les lignes vides
        lignes_client = [ligne.strip() for ligne in adresse_client.split('\n') if ligne.strip()]
        client_info.extend(lignes_client)
    
    if not client_info:
        client_info = ["Adresse client non spécifiée"]

    # --- Calcul des hauteurs nécessaires ---
    line_height = 6
    max_lines = max(len(notre_info), len(client_info))
    box_height = max_lines * line_height + 10  # +10 pour padding

    # --- Impression des colonnes avec bordures complètes ---
    y_start = pdf.get_y()
    x_left = pdf.get_x()
    
    # Dessiner les bordures des deux colonnes
    pdf.rect(x_left, y_start, 95, box_height)  # Colonne DE
    pdf.rect(x_left + 95, y_start, 95, box_height)  # Colonne À
    
    # Colonne "DE" - contenu
    pdf.set_xy(x_left + 2, y_start + 2)  # Petit padding
    pdf.set_font(pdf.base_font, '', 10)
    for ligne in notre_info:
        if pdf.get_y() < y_start + box_height - 2:
            pdf.cell(91, line_height, pdf.safe(ligne), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_x(x_left + 2)
    
    # Colonne "À" - contenu
    pdf.set_xy(x_left + 95 + 2, y_start + 2)  # Petit padding
    for ligne in client_info:
        if pdf.get_y() < y_start + box_height - 2:
            pdf.cell(91, line_height, pdf.safe(ligne), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_x(x_left + 95 + 2)
    
    # Se positionner après les cases
    pdf.set_y(y_start + box_height)
    pdf.ln(10)

    # Tableau des services
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(80, 10, pdf.safe('DESCRIPTION'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.cell(30, 10, pdf.safe('HEURE'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True, align='C')
    pdf.cell(40, 10, pdf.safe('PRIX UNIT.'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True, align='R')
    pdf.cell(40, 10, pdf.safe('TOTAL'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.base_font, '', 10)

    total_general = 0.0
    for service in services:
        desc, qty, price = service
        line_total = qty * price
        total_general += line_total
        pdf.cell(80, 10, pdf.safe(desc), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 10, pdf.safe(str(qty)), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
        pdf.cell(40, 10, pdf.safe(f'CHF {price:.2f}'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
        pdf.cell(40, 10, pdf.safe(f'CHF {line_total:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    pdf.ln(5)

    # Totaux
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(110, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(40, 8, pdf.safe('Sous-total:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.set_font(pdf.base_font, '', 11)
    pdf.cell(40, 8, pdf.safe(f'CHF {total_general:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.cell(110, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, '', 10)
    pdf.cell(40, 8, pdf.safe('TVA (0%):'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(40, 8, pdf.safe('CHF 0.00'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(110, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(40, 10, pdf.safe('TOTAL:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.cell(40, 10, pdf.safe(f'CHF {total_general:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.ln(12)

    # Conditions de paiement
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(0, 8, pdf.safe('CONDITIONS DE PAIEMENT'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font(pdf.base_font, '', 10)
    conditions = [
        "• Virement bancaire",
        "• Paiement à 30 jours",
        "• En cas de retard, intérêts de 5% par an",
        "• En cas de non-paiement, le site pourra être suspendu"
    ]
    for condition in conditions:
        pdf.cell(0, 5, pdf.safe(condition), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(3)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(0, 6, pdf.safe("Merci de votre confiance !"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf, numero_facture


# ===== Interface Streamlit =====
def main():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #2980b9 0%, #3498db 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #ecf0f1;
        font-size: 1.1rem;
        margin: 0;
    }
    .stTextArea textarea {
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1>🚀 BrudisWeb</h1>
        <p>Générateur de Factures Professionnelles</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 📋 Informations Facture")
        st.markdown("---")

        entreprise = st.text_input("🏢 Nom de l'entreprise *", placeholder="Ex: Apple Inc.")
        st.markdown("---")

        # --- Services multiples ---
        st.markdown("### 🛠️ Services")
        if "services" not in st.session_state:
            st.session_state.services = []

        with st.form("services_form", clear_on_submit=True):
            desc = st.text_input("Description du service")
            qty = st.number_input("Quantité", min_value=1, value=1)
            price = st.number_input("Prix unitaire (CHF)", min_value=0.0, format="%.2f")
            add = st.form_submit_button("➕ Ajouter le service")
            if add and desc and price > 0:
                st.session_state.services.append((desc, qty, price))

        if st.session_state.services:
            st.markdown("#### Services ajoutés :")
            for i, (d, q, p) in enumerate(st.session_state.services):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i+1}. {d} – {q} × CHF {p:.2f} = CHF {q*p:.2f}")
                with col2:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.services.pop(i)
                        st.rerun()

        st.markdown("---")

        adresse_client = st.text_area(
            "📍 Adresse du client", 
            height=100,
            placeholder="Nom de l'entreprise\nRue et numéro\nCode postal Ville\nPays"
        )
        
        adresse_brudisweb = st.text_area(
            "🏢 Votre adresse (Entreprise)", 
            height=100,
            placeholder="Rue et numéro\nCode postal Ville\nPays"
        )
        
        iban = st.text_input("🏦 IBAN", placeholder="CH00 0000 0000 0000 0000 0")
        numero = st.text_input("#️⃣ Numéro de facture", placeholder="01")
        st.markdown("---")
        st.markdown("*️⃣ *Champs obligatoires*")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📄 Aperçu de la Facture")
        if entreprise and st.session_state.services:
            st.success("✅ Prêt pour génération")
            with st.expander("🔍 Détails de la facture", expanded=True):
                st.write(f"**Client:** {entreprise}")
                total_preview = sum(q*p for _, q, p in st.session_state.services)
                st.write(f"**Total estimé:** CHF {total_preview:.2f}")
                st.write(f"**Services:**")
                for d, q, p in st.session_state.services:
                    st.write(f"- {d} ({q} × CHF {p:.2f}) = CHF {q*p:.2f}")
                
                # Affichage des adresses avec préservation des retours à la ligne
                st.write("**Adresse client:**")
                if adresse_client:
                    for ligne in adresse_client.split('\n'):
                        if ligne.strip():
                            st.write(f"  {ligne}")
                else:
                    st.write("  (non spécifiée)")
                
                st.write("**Adresse entreprise:**")
                if adresse_brudisweb:
                    for ligne in adresse_brudisweb.split('\n'):
                        if ligne.strip():
                            st.write(f"  {ligne}")
                else:
                    st.write("  (non spécifiée)")
                
                if iban:
                    st.write(f"**IBAN:** {iban}")
                if numero:
                    st.write(f"**Numéro:** {numero}")
                demo_numero = InvoiceNumberManager.generate_invoice_number(numero)
                demo_date = InvoiceNumberManager.get_formatted_date()
                st.write(f"**Date:** {demo_date}")
                st.write(f"**Numéro de facture:** {demo_numero}")
        else:
            st.warning("⚠️ Veuillez remplir les champs obligatoires et ajouter au moins un service")

    with col2:
        st.markdown("### 🎯 Actions")
        if st.button("🚀 Générer la Facture", type="primary", use_container_width=True):
            if not entreprise:
                st.error("❌ Veuillez saisir le nom de l'entreprise")
            elif not st.session_state.services:
                st.error("❌ Ajoutez au moins un service")
            else:
                try:
                    with st.spinner("📄 Génération du PDF en cours..."):
                        pdf, numero_facture = create_pdf(
                            entreprise,
                            st.session_state.services,
                            adresse_client,
                            adresse_brudisweb,
                            iban,
                            numero
                        )
                        raw_output = pdf.output()
                        pdf_content = bytes(raw_output) if isinstance(raw_output, bytearray) else raw_output
                        filename = f'Facture_BrudisWeb_{numero_facture}.pdf'
                        st.success("✅ Facture générée avec succès !")
                        st.download_button(
                            label="📥 Télécharger la Facture",
                            data=pdf_content,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération: {str(e)}")

        if st.button("🗑️ Réinitialiser les services", use_container_width=True):
            st.session_state.services = []
            st.rerun()

        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        st.markdown("""
        **BrudisWeb**   
        - Marius Pochon  

        🌐 www.brudisweb.ch  
        📧 contact@brudisweb.ch
        """)


if __name__ == "__main__":
    main()
