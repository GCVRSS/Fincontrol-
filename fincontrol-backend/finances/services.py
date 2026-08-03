from datetime import date
from django.db.models import Sum
from .models import Transaction, Goal


def get_monthly_summary(user):
    today = date.today()
    start_of_month = today.replace(day=1)

    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_of_month,
        date__lte=today
    )

    total_income = transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
    total_expense = transactions.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expense

    expenses_by_category = (
        transactions.filter(type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    goals = Goal.objects.filter(user=user)
    goals_progress = [
        {
            'name': goal.name,
            'target_amount': goal.target_amount,
            'current_amount': goal.current_amount,
            'progress_percent': round((goal.current_amount / goal.target_amount) * 100, 1) if goal.target_amount > 0 else 0,
        }
        for goal in goals
    ]

    return {
        'period': f"{start_of_month.strftime('%d/%m/%Y')} a {today.strftime('%d/%m/%Y')}",
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'expenses_by_category': list(expenses_by_category),
        'goals_progress': goals_progress,
    }

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_report(user):
    summary = get_monthly_summary(user)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('TitleCustom', parent=styles['Title'], fontSize=20, spaceAfter=6)
    elements.append(Paragraph("FinControl - Relatório Financeiro", title_style))
    elements.append(Paragraph(f"Usuário: {user.username} | Período: {summary['period']}", styles['Normal']))
    elements.append(Spacer(1, 0.8*cm))

    resumo_data = [
        ['Total de Receitas', f"R$ {summary['total_income']:.2f}"],
        ['Total de Despesas', f"R$ {summary['total_expense']:.2f}"],
        ['Saldo do Período', f"R$ {summary['balance']:.2f}"],
    ]
    resumo_table = Table(resumo_data, colWidths=[8*cm, 6*cm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(resumo_table)
    elements.append(Spacer(1, 1*cm))

    elements.append(Paragraph("Gastos por Categoria", styles['Heading2']))
    if summary['expenses_by_category']:
        cat_data = [['Categoria', 'Total Gasto']]
        for item in summary['expenses_by_category']:
            nome = item['category__name'] or 'Sem categoria'
            cat_data.append([nome, f"R$ {item['total']:.2f}"])

        cat_table = Table(cat_data, colWidths=[8*cm, 6*cm])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(cat_table)
    else:
        elements.append(Paragraph("Nenhuma despesa registrada neste período.", styles['Normal']))

    elements.append(Spacer(1, 1*cm))

    elements.append(Paragraph("Progresso das Metas", styles['Heading2']))
    if summary['goals_progress']:
        goal_data = [['Meta', 'Progresso', 'Valor Atual / Alvo']]
        for goal in summary['goals_progress']:
            goal_data.append([
                goal['name'],
                f"{goal['progress_percent']}%",
                f"R$ {goal['current_amount']:.2f} / R$ {goal['target_amount']:.2f}"
            ])

        goal_table = Table(goal_data, colWidths=[5*cm, 3*cm, 6*cm])
        goal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(goal_table)
    else:
        elements.append(Paragraph("Nenhuma meta cadastrada.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer

