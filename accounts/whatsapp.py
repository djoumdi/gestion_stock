# accounts/whatsapp.py
"""
Génère des liens "wa.me" pour envoyer un message WhatsApp pré-rempli, sans
passer par une API payante. L'utilisateur clique, WhatsApp s'ouvre avec le
message déjà rédigé, il valide l'envoi lui-même. Aucune clé API requise.
"""
from urllib.parse import quote
from django.conf import settings


def normaliser_numero_whatsapp(telephone):
    """Convertit un numéro de téléphone local en format international
    attendu par wa.me (chiffres uniquement, avec indicatif pays, sans '+').

    Retourne None si le numéro est vide, pour permettre d'afficher/masquer
    le bouton WhatsApp proprement dans les templates.
    """
    if not telephone:
        return None

    chiffres = ''.join(c for c in telephone if c.isdigit() or c == '+')

    if chiffres.startswith('+'):
        return chiffres[1:]
    if chiffres.startswith('00'):
        return chiffres[2:]

    # Numéro local. Certains pays utilisent un "0" de tête (ex. France, Sénégal :
    # 07XXXXXXXX), d'autres non (le Cameroun : les numéros mobiles s'écrivent
    # directement sur 9 chiffres, ex. 699887766, sans 0 devant). On retire ce 0
    # SEULEMENT s'il est présent, puis on préfixe l'indicatif pays configuré
    # dans les deux cas — sans ça, un numéro camerounais sans 0 repartait tel
    # quel, sans indicatif, et le lien wa.me était invalide.
    local = chiffres[1:] if chiffres.startswith('0') else chiffres
    indicatif = getattr(settings, 'WHATSAPP_INDICATIF_PAYS', '')
    return f"{indicatif}{local}" if indicatif else chiffres


def lien_whatsapp(telephone, message):
    """Construit l'URL wa.me complète (numéro + message pré-rempli encodé).
    Retourne None si le numéro est invalide/absent — le template n'affiche
    alors pas le bouton plutôt que de proposer un lien cassé."""
    numero = normaliser_numero_whatsapp(telephone)
    if not numero:
        return None
    return f"https://wa.me/{numero}?text={quote(message)}"
