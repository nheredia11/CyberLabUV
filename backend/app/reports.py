"""Generación del reporte académico en PDF (ReportLab)."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .database import utcnow


def build_student_report_pdf(student_id: str, dashboard: dict | None, all_modules: list) -> bytes:
    """Devuelve los bytes del PDF con el progreso y los checkpoints del estudiante."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
    )
    heading_style = ParagraphStyle(
        'ReportHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    story = []

    story.append(Paragraph("CyberLabUV — Reporte Académico de Evidencias", title_style))
    story.append(Paragraph(f"<b>Estudiante ID:</b> {student_id} | <b>Fecha de Generación:</b> {utcnow()[:10]}", subtitle_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Resumen de Progreso General", heading_style))
    progress_pct = dashboard.get('progress_percent', 0.0) if dashboard else 0.0
    completed_mods = dashboard.get('completed_modules_count', 0) if dashboard else 0
    total_mods = dashboard.get('total_modules_count', len(all_modules)) if dashboard else len(all_modules)
    
    summary_data = [
        [Paragraph("<b>Métrica</b>", body_style), Paragraph("<b>Valor</b>", body_style)],
        [Paragraph("Progreso Global del Estudiante", body_style), Paragraph(f"{progress_pct:.1f}%", body_style)],
        [Paragraph("Módulos Completados", body_style), Paragraph(f"{completed_mods} de {total_mods}", body_style)],
    ]
    t_summary = Table(summary_data, colWidths=[250, 260])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. Detalle de Checkpoints y Competencias", heading_style))
    
    cp_rows = [[Paragraph("<b>Módulo / Checkpoint ID</b>", body_style), Paragraph("<b>Estado</b>", body_style), Paragraph("<b>Nivel Competencia</b>", body_style)]]
    
    modules_sub = dashboard.get("modules", []) if dashboard else []
    if not modules_sub:
        cp_rows.append([Paragraph("Sin registros de checkpoints aún.", body_style), Paragraph("-", body_style), Paragraph("Inicial", body_style)])
    else:
        for mod in modules_sub:
            status_text = mod.get('status', 'pending')
            level = "Autónomo" if status_text in ("done", "completed") else "En consolidación"
            cp_rows.append([
                Paragraph(f"{mod.get('module_id', 'M00')} : {mod.get('checkpoint_id', 'CP')}", body_style),
                Paragraph(status_text.upper(), body_style),
                Paragraph(level, body_style),
            ])

    t_cp = Table(cp_rows, colWidths=[200, 110, 200])
    t_cp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_cp)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<i>Nota: Generado automáticamente por el núcleo de evaluación de CyberLabUV. Válido para sustentación de tesis de pregrado.</i>", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
