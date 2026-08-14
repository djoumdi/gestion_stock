# achats/pdf.py
"""Génération du bon de commande fournisseur au format PDF (ReportLab).
Même structure que ventes/pdf.py, adaptée au fournisseur plutôt qu'au client."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

COULEUR_PRIMAIRE = colors.HexColor('#1D4ED8')
COULEUR_GRISE = colors.HexColor('#6B7280')
COULEUR_LIGNE = colors.HexColor('#E5E7EB')
COULEUR_FOND_ENTETE = colors.HexColor('#F9FAFB')


def generer_pdf_bon_commande(achat):
    """Retourne un buffer BytesIO contenant le PDF du bon de commande."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"Bon de commande {achat.code}",
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('Titre', parent=styles['Heading1'], textColor=COULEUR_PRIMAIRE, fontSize=20, spaceAfter=2)
    style_normal = ParagraphStyle('NormalGris', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9)
    style_normal_droite = ParagraphStyle('NormalDroite', parent=style_normal, alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=8, spaceAfter=2)
    style_valeur = ParagraphStyle('Valeur', parent=styles['Normal'], fontSize=11, textColor=colors.black, spaceAfter=1)

    elements = []

    entete = Table([
        [
            Paragraph("BON DE COMMANDE", style_titre),
            Paragraph("TechStock<br/>Magasin informatique", style_normal_droite),
        ]
    ], colWidths=[100 * mm, 70 * mm])
    entete.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(entete)
    elements.append(Paragraph(f"{achat.code}", style_normal))
    elements.append(Paragraph(f"Date : {achat.date_achat.strftime('%d/%m/%Y %H:%M')}", style_normal))
    elements.append(Paragraph(f"Statut : {achat.get_statut_display()}", style_normal))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("COMMANDE ADRESSÉE À", style_label))
    fournisseur = achat.fournisseur
    elements.append(Paragraph(fournisseur.nom if fournisseur else "Fournisseur non renseigné", style_valeur))
    if fournisseur and fournisseur.telephone:
        elements.append(Paragraph(fournisseur.telephone, style_normal))
    if fournisseur and fournisseur.email:
        elements.append(Paragraph(fournisseur.email, style_normal))
    if fournisseur and fournisseur.adresse:
        adresse = fournisseur.adresse
        if fournisseur.ville:
            adresse += f", {fournisseur.ville}"
        elements.append(Paragraph(adresse, style_normal))
    elements.append(Spacer(1, 8 * mm))

    entetes = ['#', 'Article', 'Qté', 'Prix unitaire', 'Total']
    lignes_tableau = [entetes]
    for i, ligne in enumerate(achat.lignes.all(), start=1):
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

    tableau_total = Table([["Total commande", f"{achat.total} FCFA"]], colWidths=[140 * mm, 30 * mm])
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

    if achat.notes:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("NOTES", style_label))
        elements.append(Paragraph(achat.notes, style_normal))

    elements.append(Spacer(1, 15 * mm))
    style_pied = ParagraphStyle('Pied', parent=styles['Normal'], textColor=COULEUR_GRISE, fontSize=9, alignment=TA_CENTER)
    elements.append(Paragraph("Merci de confirmer la réception de cette commande.", style_pied))

    doc.build(elements)
    buffer.seek(0)
    return buffer
