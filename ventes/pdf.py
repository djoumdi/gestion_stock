# ventes/pdf.py
"""Génération de la facture au format PDF avec ReportLab (pur Python, sans
dépendance système comme WeasyPrint en a besoin - important pour un poste de
dev Windows sans GTK/Cairo installés)."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from parametres.pdf_utils import entete_magasin

COULEUR_PRIMAIRE = colors.HexColor('#1D4ED8')
COULEUR_GRISE = colors.HexColor('#6B7280')
COULEUR_LIGNE = colors.HexColor('#E5E7EB')
COULEUR_FOND_ENTETE = colors.HexColor('#F9FAFB')


def generer_pdf_facture(facture):
    """Retourne un buffer BytesIO contenant le PDF de la facture, prêt à être
    servi par une vue (FileResponse) ou écrit sur disque."""
    vente = facture.vente
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"Facture {facture.numero}",
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('Titre', parent=styles['Heading1'], textColor=COULEUR_PRIMAIRE, fontSize=22, spaceAfter=2)
    style_normal = ParagraphStyle('NormalGris', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9)
    style_normal_droite = ParagraphStyle('NormalDroite', parent=style_normal, alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=8, spaceAfter=2)
    style_valeur = ParagraphStyle('Valeur', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=1)

    elements = []

    # En-tête : titre + infos magasin
    entete = Table([
        [
            Paragraph("FACTURE", style_titre),
            entete_magasin(style_normal_droite),
        ]
    ], colWidths=[100 * mm, 70 * mm])
    entete.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(entete)
    elements.append(Paragraph(f"{facture.numero}", style_normal))
    elements.append(Paragraph(f"Date : {vente.date_vente.strftime('%d/%m/%Y %H:%M')}", style_normal))
    elements.append(Spacer(1, 8 * mm))

    # Facturé à
    elements.append(Paragraph("FACTURÉ À", style_label))
    nom_client = vente.client.nom if vente.client else "Client anonyme"
    elements.append(Paragraph(nom_client, style_valeur))
    if vente.client and vente.client.telephone:
        elements.append(Paragraph(vente.client.telephone, style_normal))
    if vente.client and vente.client.email:
        elements.append(Paragraph(vente.client.email, style_normal))
    elements.append(Spacer(1, 8 * mm))

    # Tableau des articles
    entetes = ['#', 'Article', 'Qté', 'Prix unitaire', 'Total']
    lignes_tableau = [entetes]
    for i, ligne in enumerate(vente.lignes.all(), start=1):
        lignes_tableau.append([
            str(i),
            ligne.produit.nom,
            str(ligne.quantite),
            f"{ligne.prix_unitaire} FCFA",
            f"{ligne.sous_total} FCFA",
        ])

    tableau = Table(lignes_tableau, colWidths=[10 * mm, 75 * mm, 20 * mm, 35 * mm, 30 * mm])
    tableau.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COULEUR_FOND_ENTETE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COULEUR_GRISE),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, COULEUR_LIGNE),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, COULEUR_LIGNE),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tableau)
    elements.append(Spacer(1, 6 * mm))

    # Total
    libelle_total = "Total payé" if facture.est_payee else "Total à payer"
    tableau_total = Table([[libelle_total, f"{vente.total} FCFA"]], colWidths=[140 * mm, 30 * mm])
    tableau_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COULEUR_FOND_ENTETE),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (1, 0), (1, 0), COULEUR_PRIMAIRE),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
    ]))
    elements.append(tableau_total)

    if facture.est_payee:
        elements.append(Spacer(1, 2 * mm))
        texte_paiement = f"Réglé par {facture.paiement.get_mode_paiement_display()} le {facture.paiement.date_paiement.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(texte_paiement, style_normal_droite))

    elements.append(Spacer(1, 15 * mm))
    style_pied = ParagraphStyle('Pied', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9, alignment=TA_CENTER)
    elements.append(Paragraph("Merci de votre confiance.", style_pied))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_pdf_devis(devis):
    """Même structure visuelle que la facture, adaptée à un devis (pas encore
    payé, avec une date de validité et son statut)."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"Devis {devis.code}",
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('Titre', parent=styles['Heading1'], textColor=COULEUR_PRIMAIRE, fontSize=22, spaceAfter=2)
    style_normal = ParagraphStyle('NormalGris', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9)
    style_normal_droite = ParagraphStyle('NormalDroite', parent=style_normal, alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=8, spaceAfter=2)
    style_valeur = ParagraphStyle('Valeur', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=1)

    elements = []

    entete = Table([
        [
            Paragraph("DEVIS", style_titre),
            entete_magasin(style_normal_droite),
        ]
    ], colWidths=[100 * mm, 70 * mm])
    entete.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(entete)
    elements.append(Paragraph(f"{devis.code}", style_normal))
    elements.append(Paragraph(f"Émis le : {devis.date_creation.strftime('%d/%m/%Y')}", style_normal))
    if devis.date_validite:
        elements.append(Paragraph(f"Valable jusqu'au : {devis.date_validite.strftime('%d/%m/%Y')}", style_normal))
    elements.append(Paragraph(f"Statut : {devis.get_statut_display()}", style_normal))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("DEVIS ÉTABLI POUR", style_label))
    nom_client = devis.client.nom if devis.client else "Client anonyme"
    elements.append(Paragraph(nom_client, style_valeur))
    if devis.client and devis.client.telephone:
        elements.append(Paragraph(devis.client.telephone, style_normal))
    if devis.client and devis.client.email:
        elements.append(Paragraph(devis.client.email, style_normal))
    elements.append(Spacer(1, 8 * mm))

    entetes = ['#', 'Article', 'Qté', 'Prix unitaire', 'Total']
    lignes_tableau = [entetes]
    for i, ligne in enumerate(devis.lignes.all(), start=1):
        lignes_tableau.append([
            str(i),
            ligne.produit.nom,
            str(ligne.quantite),
            f"{ligne.prix_unitaire} FCFA",
            f"{ligne.sous_total} FCFA",
        ])

    tableau = Table(lignes_tableau, colWidths=[10 * mm, 75 * mm, 20 * mm, 35 * mm, 30 * mm])
    tableau.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COULEUR_FOND_ENTETE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COULEUR_GRISE),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, COULEUR_LIGNE),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, COULEUR_LIGNE),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tableau)
    elements.append(Spacer(1, 6 * mm))

    tableau_total = Table([["Total estimé", f"{devis.total} FCFA"]], colWidths=[140 * mm, 30 * mm])
    tableau_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COULEUR_FOND_ENTETE),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (1, 0), (1, 0), COULEUR_PRIMAIRE),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
    ]))
    elements.append(tableau_total)

    if devis.notes:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("NOTES", style_label))
        elements.append(Paragraph(devis.notes, style_normal))

    elements.append(Spacer(1, 15 * mm))
    style_pied = ParagraphStyle('Pied', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9, alignment=TA_CENTER)
    elements.append(Paragraph("Ce document est un devis, pas une facture — les prix sont susceptibles d'évoluer après sa date de validité.", style_pied))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_pdf_avoir(retour):
    """Justificatif d'avoir généré à partir d'un retour. Reprend le style des
    autres documents, avec un total négatif (montant dû AU client)."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"Avoir {retour.code}",
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('Titre', parent=styles['Heading1'], textColor=COULEUR_PRIMAIRE, fontSize=22, spaceAfter=2)
    style_normal = ParagraphStyle('NormalGris', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9)
    style_normal_droite = ParagraphStyle('NormalDroite', parent=style_normal, alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=8, spaceAfter=2)
    style_valeur = ParagraphStyle('Valeur', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=1)

    elements = []
    vente = retour.vente

    entete = Table([
        [
            Paragraph("AVOIR", style_titre),
            entete_magasin(style_normal_droite),
        ]
    ], colWidths=[100 * mm, 70 * mm])
    entete.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(entete)
    elements.append(Paragraph(f"{retour.code}", style_normal))
    elements.append(Paragraph(f"Date : {retour.date_retour.strftime('%d/%m/%Y %H:%M')}", style_normal))
    elements.append(Paragraph(f"Émis suite au retour de produits de la vente {vente.code}", style_normal))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("AVOIR ÉTABLI POUR", style_label))
    nom_client = vente.client.nom if vente.client else "Client anonyme"
    elements.append(Paragraph(nom_client, style_valeur))
    if vente.client and vente.client.telephone:
        elements.append(Paragraph(vente.client.telephone, style_normal))
    elements.append(Spacer(1, 8 * mm))

    entetes = ['#', 'Article retourné', 'Qté', 'Prix unitaire', 'Total']
    lignes_tableau = [entetes]
    for i, ligne in enumerate(retour.lignes.all(), start=1):
        lignes_tableau.append([
            str(i),
            ligne.produit.nom,
            str(ligne.quantite),
            f"{ligne.prix_unitaire} FCFA",
            f"{ligne.sous_total} FCFA",
        ])

    tableau = Table(lignes_tableau, colWidths=[10 * mm, 75 * mm, 20 * mm, 35 * mm, 30 * mm])
    tableau.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COULEUR_FOND_ENTETE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COULEUR_GRISE),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, COULEUR_LIGNE),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, COULEUR_LIGNE),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tableau)
    elements.append(Spacer(1, 6 * mm))

    tableau_total = Table([["Montant de l'avoir", f"{retour.total} FCFA"]], colWidths=[140 * mm, 30 * mm])
    tableau_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COULEUR_FOND_ENTETE),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (1, 0), (1, 0), COULEUR_PRIMAIRE),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
    ]))
    elements.append(tableau_total)

    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph("MOTIF DU RETOUR", style_label))
    elements.append(Paragraph(retour.motif, style_normal))

    elements.append(Spacer(1, 15 * mm))
    style_pied = ParagraphStyle('Pied', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9, alignment=TA_CENTER)
    elements.append(Paragraph("Cet avoir est un justificatif de retour, à faire valoir sur un prochain achat ou un remboursement selon la politique du magasin.", style_pied))

    doc.build(elements)
    buffer.seek(0)
    return buffer
