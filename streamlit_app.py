# streamlit_app.py
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date
import locale
import random
from pathlib import Path
import os
import re

# ===== Configuration Streamlit =====
st.set_page_config(
    page_title="BrudisWeb - Générateur de Factures",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration locale
try:
    locale.setlocale(locale.LC_ALL, 'fr_CH.utf8')
except Exception:
    try:
        locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
    except Exception:
        pass  # fallback

# ===== Classe PDF avec gestion des polices Unicode/fallback =====
class ModernInvoicePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=15)

        # Tentative d'enregistrer une police Unicode (DejaVu) depuis plusieurs emplacements connus.
        # Si on ne trouve pas de TTF, on reste sur les polices intégrées (Helvetica).
        self.unicode_font_available = False
        self.base_font = "Helvetica"  # fallback
        self._register_unicode_fonts_if_available()

    def _register_unicode_fonts_if_available(self):
        # Emplacements candidates pour les fichiers DejaVu
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
            ],
            "italic": [
                Path("DejaVuSans-Oblique.ttf"),
                Path("fonts/DejaVuSans-Oblique.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
                Path("C:/Windows/Fonts/DejaVuSans-Oblique.ttf"),
            ],
            "bolditalic": [
                Path("DejaVuSans-BoldOblique.ttf"),
                Path("fonts/DejaVuSans-BoldOblique.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
                Path("C:/Windows/Fonts/DejaVuSans-BoldOblique.ttf"),
            ],
        }

        found = {}
        for style, paths in candidates.items():
            for p in paths:
                if p.exists():
                    found[style] = p
                    break

        # Si on trouve au moins le regular, on enregistre.
        if "regular" in found:
            try:
                # register regular
                self.add_font("DejaVu", "", str(found["regular"]))
                # register bold (si trouvé, sinon on peut réutiliser regular)
                if "bold" in found:
                    self.add_font("DejaVu", "B", str(found["bold"]))
                else:
                    # fallback: reuse regular file for bold to avoid "Undefined font" errors
                    self.add_font("DejaVu", "B", str(found["regular"]))
                # italic
                if "italic" in found:
                    self.add_font("DejaVu", "I", str(found["italic"]))
                else:
                    self.add_font("DejaVu", "I", str(found["regular"]))
                # bold-italic
                if "bolditalic" in found:
                    self.add_font("DejaVu", "BI", str(found["bolditalic"]))
                else:
                    self.add_font("DejaVu", "BI", str(found["regular"]))

                self.unicode_font_available = True
                self.base_font = "DejaVu"
            except Exception:
                # en cas d'échec, fallback silencieux sur Helvetica
                self.unicode_font_available = False
                self.base_font = "Helvetica"

    def safe(self, text: str) -> str:
        """
        Retourne une version du texte sûre pour la police active :
         - si police Unicode dispo : retourne tel quel
         - sinon : remplace les puces/emoji non-latin1, retire caractères hors latin1
        """
        if text is None:
            return ""
        if self.unicode_font_available:
            return str(text)
        # remplacement simple pour puces
        t = str(text).replace("•", "-")
        # enlever emojis / caractères non Latin-1 (ord > 255)
        t = "".join(ch for ch in t if ord(ch) < 256)
        # évite caractères de controle problématiques
        t = re.sub(r"[\x00-\x1f\x7f]", "", t)
        return t

    # Header & footer utilisent self.base_font (DejaVu si dispo, sinon Helvetica)
    def header(self):
        self.set_fill_color(41, 128, 185)
        self.rect(0, 0, 210, 35, 'F')

        self.set_text_color(255, 255, 255)
        self.set_font(self.base_font, 'B', 24)
        self.cell(0, 25, self.safe('BrudisWeb'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font(self.base_font, '', 12)
        self.set_y(20)
        self.cell(0, 10, self.safe('Solutions web modernes & performantes'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(15)

    def footer(self):
        self.set_y(-25)
        self.set_fill_color(245, 245, 245)
        self.rect(0, self.get_y()-5, 210, 30, 'F')

        self.set_text_color(100, 100, 100)
        self.set_font(self.base_font, '', 9)

        self.cell(95, 5, self.safe('Urs Schweizer: urs.schweizer@brudisweb.ch | +41 78 256 14 66'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(95, 5, self.safe('www.brudisweb.ch'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(95, 5, self.safe('Marius Pochon: marius.pochon@brudisweb.ch | +41 79 101 61 94'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(95, 5, self.safe(f'Page {self.page_no()}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ===== Création du PDF =====
def create_pdf(entreprise, montant_float, description, adresse):
    """Génère le PDF de facture"""
    pdf = ModernInvoicePDF()
    pdf.add_page()

    now = date.today()
    try:
        date_str = now.strftime("Le %A %d %B %Y")
    except Exception:
        date_str = now.strftime("Le %d/%m/%Y")

    numero_facture = f"BW-{now.strftime('%Y%m%d')}-{random.randint(100, 999)}"

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

    # Section facturation
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(95, 10, pdf.safe('DE:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)

    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(95, 10, pdf.safe('À:'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)

    pdf.set_text_color(0, 0, 0)

    notre_info = [
        "BrudisWeb",
        "Urs Schweizer & Marius Pochon",
        "Solutions web modernes",
        "",
        "urs.schweizer@brudisweb.ch",
        "marius.pochon@brudisweb.ch",
        "+41 78 256 14 66"
    ]
    client_info = [entreprise or "", ""]
    if adresse:
        client_info.extend(adresse.split('\n'))
    else:
        client_info.append("Adresse non spécifiée")

    max_lines = max(len(notre_info), len(client_info))
    for i in range(max_lines):
        notre_line = notre_info[i] if i < len(notre_info) else ""
        if i == 0:
            pdf.set_font(pdf.base_font, 'B', 10)
        else:
            pdf.set_font(pdf.base_font, '', 10)
        pdf.cell(95, 6, pdf.safe(notre_line), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)

        client_line = client_info[i] if i < len(client_info) else ""
        if i == 0:
            pdf.set_font(pdf.base_font, 'B', 10)
        else:
            pdf.set_font(pdf.base_font, '', 10)
        pdf.cell(95, 6, pdf.safe(client_line), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(15)

    # Tableau
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(100, 10, pdf.safe('DESCRIPTION'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.cell(30, 10, pdf.safe('QUANTITÉ'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True, align='C')
    pdf.cell(30, 10, pdf.safe('PRIX UNIT.'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True, align='R')
    pdf.cell(30, 10, pdf.safe('TOTAL'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.base_font, '', 10)
    pdf.cell(100, 12, pdf.safe(description), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(30, 12, pdf.safe('1'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
    pdf.cell(30, 12, pdf.safe(f'CHF {montant_float:.2f}'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 12, pdf.safe(f'CHF {montant_float:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    for _ in range(3):
        pdf.cell(100, 8, '', border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 8, '', border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 8, '', border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(30, 8, '', border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(130, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, 'B', 11)
    pdf.cell(30, 8, pdf.safe('Sous-total:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.set_font(pdf.base_font, '', 11)
    pdf.cell(30, 8, pdf.safe(f'CHF {montant_float:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.cell(130, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, '', 10)
    pdf.cell(30, 8, pdf.safe('TVA (0%):'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(30, 8, pdf.safe('CHF 0.00'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(130, 8, '', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(30, 10, pdf.safe('TOTAL:'), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=True)
    pdf.cell(30, 10, pdf.safe(f'CHF {montant_float:.2f}'), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, align='R')

    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf.base_font, 'B', 12)
    pdf.cell(0, 10, pdf.safe('CONDITIONS DE PAIEMENT'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font(pdf.base_font, '', 10)
    conditions = [
        "• Paiement à 30 jours",
        "• Virement bancaire ou facture QR",
        "• En cas de retard, intérêts de 5% par an",
        "",
        "Merci de votre confiance !"
    ]
    for condition in conditions:
        pdf.cell(0, 6, pdf.safe(condition), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf, numero_facture


# ===== Interface Streamlit (identique à la tienne, avec small fixes) =====
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
        montant = st.number_input("💰 Montant (CHF) *", min_value=0.0, format="%.2f")
        st.markdown("---")
        description = st.text_input("📝 Description du service", value="Développement site web")
        adresse = st.text_area("📍 Adresse du client", placeholder="Rue de la Paix 123\n1000 Lausanne\nSuisse", height=100)
        st.markdown("---")
        st.markdown("*️⃣ *Champs obligatoires*")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📄 Aperçu de la Facture")
        if entreprise and montant > 0:
            st.success("✅ Prêt pour génération")
            with st.expander("🔍 Détails de la facture", expanded=True):
                st.write(f"**Client:** {entreprise}")
                st.write(f"**Montant:** CHF {montant:.2f}")
                st.write(f"**Service:** {description}")
                if adresse:
                    st.write(f"**Adresse:** {adresse}")
                today = date.today()
                demo_numero = f"BW-{today.strftime('%Y%m%d')}-XXX"
                st.write(f"**Date:** {today.strftime('%d/%m/%Y')}")
                st.write(f"**Numéro:** {demo_numero}")
        else:
            st.warning("⚠️ Veuillez remplir les champs obligatoires")

    with col2:
        st.markdown("### 🎯 Actions")

        if st.button("🚀 Générer la Facture"):
            if not entreprise:
                st.error("❌ Veuillez saisir le nom de l'entreprise")
            elif montant <= 0:
                st.error("❌ Le montant doit être supérieur à 0")
            else:
                try:
                    with st.spinner("📄 Génération du PDF en cours..."):
                        pdf, numero_facture = create_pdf(entreprise, montant, description, adresse)

                    # Solution plus robuste : utiliser output() au lieu d'output_bytes()
                    try:
                        # output() retourne directement des bytes utilisables
                        raw_output = pdf.output()
                        pdf_content = bytes(raw_output) if isinstance(raw_output, bytearray) else raw_output
                    except Exception:
                        # Si output() échoue, essayer output_bytes() avec conversion
                        try:
                            raw_output = pdf.output_bytes()
                            # Conversion forcée en bytes avec encoding latin1 si nécessaire
                            if isinstance(raw_output, bytearray):
                                pdf_content = bytes(raw_output)
                            else:
                                pdf_content = raw_output
                        except Exception:
                            # Dernier recours : écrire temporairement sur disque
                            import tempfile
                            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                                pdf.output(tmp.name)
                                with open(tmp.name, 'rb') as f:
                                    pdf_content = f.read()
                                os.unlink(tmp.name)
                                
                    filename = f'Facture_BrudisWeb_{numero_facture}.pdf'

                    st.success("✅ Facture générée avec succès !")
                    st.download_button(
                        label="📄 Télécharger la Facture",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération: {str(e)}")
                    # Debug: afficher le type exact du problème
                    import traceback
                    st.error(f"Détail de l'erreur: {traceback.format_exc()}")

        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        st.markdown("""
        **BrudisWeb**  
        - Urs Schweizer  
        - Marius Pochon  

        🌐 www.brudisweb.ch  
        📧 Contact disponible sur le site
        """)


if __name__ == "__main__":
    main()