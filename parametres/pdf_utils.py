# parametres/pdf_utils.py
"""En-tête magasin partagé par tous les PDF (factures, devis, avoirs, bons de
commande). Lit ParametresMagasin : nom, adresse, téléphone, email et logo."""
import io
import urllib.request
from xml.sax.saxutils import escape

from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph

from .models import ParametresMagasin

LARGEUR_LOGO = 35 * mm
HAUTEUR_MAX_LOGO = 22 * mm


def _texte_entete(config):
    lignes = [config.nom_magasin]
    if config.adresse:
        lignes.append(config.adresse)
    if config.telephone:
        lignes.append(config.telephone)
    if config.email:
        lignes.append(config.email)
    # escape() : un "&" ou "<" dans le nom du magasin ferait planter ReportLab
    return "<br/>".join(escape(ligne) for ligne in lignes)


def _logo(config):
    """Télécharge le logo (stocké sur Cloudinary) et le prépare pour le PDF.
    Retourne None en cas d'échec : le PDF se génère alors sans logo."""
    if not config.logo:
        return None
    try:
        with urllib.request.urlopen(config.logo.url, timeout=5) as reponse:
            donnees = reponse.read()
        image = Image(io.BytesIO(donnees))
        ratio = image.imageHeight / float(image.imageWidth)
        largeur = LARGEUR_LOGO
        hauteur = largeur * ratio
        if hauteur > HAUTEUR_MAX_LOGO:
            hauteur = HAUTEUR_MAX_LOGO
            largeur = hauteur / ratio
        image.drawWidth = largeur
        image.drawHeight = hauteur
        image.hAlign = 'RIGHT'
        return image
    except Exception:
        return None


def entete_magasin(style_droite):
    """Contenu de la cellule droite de l'en-tête d'un PDF. Retourne soit un
    Paragraph seul, soit [logo, Paragraph] si le logo a pu être chargé."""
    config = ParametresMagasin.charger()
    texte = Paragraph(_texte_entete(config), style_droite)
    logo = _logo(config)
    return [logo, texte] if logo is not None else texte
