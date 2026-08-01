"""
PDF report generator.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io
from datetime import datetime

class PDFReportGenerator:
    """Generate PDF reports."""
    
    @staticmethod
    def generate_report(title: str, headers: list, data: list, 
                       summary: dict = None, date_range: str = None) -> bytes:
        """
        Generate a PDF report.
        
        Args:
            title: Report title
            headers: List of column headers
            data: List of rows (each row is a list)
            summary: Dictionary of summary data
            date_range: Date range string
        
        Returns:
            bytes: PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E4053'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        elements.append(Paragraph(title, title_style))
        
        # Date
        if date_range:
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#5D6D7E'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph(f"تاریخ: {date_range}", date_style))
        
        elements.append(Spacer(1, 20))
        
        # Table
        table_data = [headers] + data
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4053')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9F9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D5D8DC')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        # Summary
        if summary:
            elements.append(Spacer(1, 30))
            
            summary_style = ParagraphStyle(
                'SummaryStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#2E4053'),
                alignment=TA_RIGHT,
                spaceAfter=6
            )
            
            elements.append(Paragraph("--- خلاصه گزارش ---", summary_style))
            for key, value in summary.items():
                elements.append(Paragraph(f"{key}: {value}", summary_style))
        
        # Footer
        elements.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#95A5A6'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"تولید شده در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ربات مدیریت تعمیرات",
            footer_style
        ))
        
        doc.build(elements)
        return buffer.getvalue()
