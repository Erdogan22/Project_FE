from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import cm
import os


def generate_payslip_pdf(user, payroll, report, output_path):

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    title = Paragraph("<b>FICHE DE PAIE</b>", styles["Title"])
    content.append(title)
    content.append(Spacer(1, 12))

    # Employee info
    info = [
        f"<b>Employé :</b> {user.prenom} {user.nom}",
        f"<b>Email :</b> {user.email}",
        f"<b>Mois :</b> {payroll.month}/{payroll.year}",
    ]

    for i in info:
        content.append(Paragraph(i, styles["Normal"]))
        content.append(Spacer(1, 6))

    content.append(Spacer(1, 12))

    # Salary table
    data = [
        ["Élément", "Valeur (€)"],
        ["Salaire de base", f"{payroll.base_salary:.2f}"],
        ["Heures sup", f"{payroll.overtime_pay:.2f}"],
        ["Bonus", f"{payroll.bonus:.2f}"],
        ["Déductions", f"-{payroll.deductions:.2f}"],
        ["Taxes", f"-{payroll.taxes:.2f}"],
        ["Sécurité sociale", f"-{payroll.social_security:.2f}"],
        ["", ""],
        ["Salaire Net", f"{payroll.net_salary:.2f}"],
    ]

    table = Table(data, colWidths=[8*cm, 5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightblue),
    ]))

    content.append(table)
    content.append(Spacer(1, 24))

    footer = Paragraph("Document généré automatiquement par le système RH", styles["Italic"])
    content.append(footer)

    doc.build(content)