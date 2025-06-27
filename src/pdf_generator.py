"""
PDF Generation Module for Cinema Tickets
This module provides comprehensive PDF generation for movie tickets with complete layout control.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import datetime
from typing import List, Dict, Any, Optional
import os

class TicketPDFGenerator:
    """Professional PDF generator for cinema tickets"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for ticket formatting"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='TicketTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0d6efd')
        ))
        
        # Movie title style
        self.styles.add(ParagraphStyle(
            name='MovieTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#212529')
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#0d6efd')
        ))
        
        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Highlight style for important info
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#198754'),
            fontName='Helvetica-Bold'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))

    def generate_booking_pdf(self, booking_data: Dict[str, Any], tickets_data: List[Dict[str, Any]], 
                           include_expired: bool = True) -> BytesIO:
        """
        Generate a comprehensive PDF for a booking with all tickets
        
        Args:
            booking_data: Dictionary containing booking information
            tickets_data: List of ticket dictionaries
            include_expired: Whether to include expired ticket notice
            
        Returns:
            BytesIO: PDF file as bytes
        """
        buffer = BytesIO()
        
        # Get booker name for document title
        booker_name = booking_data.get('booker_name', 'Anonymous User')
        
        # Create document with metadata
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=1*inch, bottomMargin=1*inch,
                               title=f"{booker_name} - Tickets",
                               author="Cinemacousas",
                               subject=f"Movie Tickets for {booking_data.get('movie_name', 'Movie')}",
                               creator="Cinemacousas Booking System")
        
        story = []
        
        # Header
        story.append(Paragraph("🎬 CINEMACOUSAS", self.styles['TicketTitle']))
        story.append(Spacer(1, 20))
        
        # Booking Information Section
        story.append(Paragraph("Booking Confirmation", self.styles['SectionHeader']))
        
        booking_info = [
            ['Booking ID:', f"#{booking_data.get('id', 'N/A')}"],
            ['Customer:', booking_data.get('booker_name', 'N/A')],
            ['Email:', booking_data.get('booker_email', 'N/A')],
            ['Booking Date:', datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Total Amount:', f"€{booking_data.get('price', 0):.2f}"],
            ['Number of Tickets:', str(len(tickets_data))]
        ]
        
        booking_table = Table(booking_info, colWidths=[2*inch, 3*inch])
        booking_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(booking_table)
        story.append(Spacer(1, 20))
        
        # Movie Information Section
        story.append(Paragraph("Movie Details", self.styles['SectionHeader']))
        story.append(Paragraph(booking_data.get('movie_name', 'Unknown Movie'), self.styles['MovieTitle']))
        
        movie_info = [
            ['Theater:', booking_data.get('room_name', 'N/A')],
            ['Date:', booking_data.get('date', datetime.date.today()).strftime('%A, %B %d, %Y')],
            ['Time:', self._format_time(booking_data.get('starttime', 0))],
            ['Duration:', f"{booking_data.get('duration', 0)} minutes"],
        ]
        
        movie_table = Table(movie_info, colWidths=[2*inch, 3*inch])
        movie_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(movie_table)
        story.append(Spacer(1, 20))
        
        # Expired Notice (if applicable)
        if include_expired and self._is_booking_expired(booking_data):
            story.append(Paragraph("⚠️ EXPIRED TICKET NOTICE", self.styles['SectionHeader']))
            story.append(Paragraph(
                "This booking has expired. The movie showing has already taken place. "
                "This document serves as a record of your past booking.",
                self.styles['InfoText']
            ))
            story.append(Spacer(1, 20))
        
        # Individual Tickets Section
        story.append(Paragraph("Individual Tickets", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        for i, ticket in enumerate(tickets_data, 1):
            # Ticket separator
            if i > 1:
                story.append(Spacer(1, 15))
                story.append(Paragraph("- " * 50, self.styles['Footer']))
                story.append(Spacer(1, 15))
            
            # Ticket header
            story.append(Paragraph(f"🎫 TICKET #{i}", self.styles['Highlight']))
            
            # Ticket details table
            ticket_info = [
                ['Seat Number:', ticket.get('seat_number', 'N/A')],
                ['Seat Type:', ticket.get('seat_type', 'Standard')],
                ['Ticket ID:', f"#{ticket.get('id', 'N/A')}"],
                ['Price:', f"€{ticket.get('price', 0):.2f}"]
            ]
            
            ticket_table = Table(ticket_info, colWidths=[1.5*inch, 2*inch])
            ticket_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ]))
            story.append(ticket_table)
        
        # Footer information
        story.append(Spacer(1, 30))
        story.append(Paragraph("Important Information", self.styles['SectionHeader']))
        
        footer_info = [
            "• Please arrive at least 15 minutes before the showing time",
            "• Tickets are non-refundable and non-transferable",
            "• Food and beverages purchased outside are not permitted",
            "• Mobile phones should be silenced during the movie",
            "• For assistance, contact our customer service"
        ]
        
        for info in footer_info:
            story.append(Paragraph(info, self.styles['InfoText']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Cinemacousas Cinema",
            self.styles['Footer']
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_single_ticket_pdf(self, ticket_data: Dict[str, Any], booking_data: Dict[str, Any]) -> BytesIO:
        """Generate a PDF for a single ticket"""
        buffer = BytesIO()
        
        # Get booker name for document title
        booker_name = booking_data.get('booker_name', 'Anonymous User')
        
        # Create document with metadata
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               title=f"{booker_name} - Ticket",
                               author="Cinemacousas",
                               subject=f"Movie Ticket for {booking_data.get('movie_name', 'Movie')}",
                               creator="Cinemacousas Booking System")
        
        story = []
        
        # Header
        story.append(Paragraph("🎬 CINEMACOUSAS", self.styles['TicketTitle']))
        story.append(Paragraph("MOVIE TICKET", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        
        # Ticket information
        story.append(Paragraph(booking_data.get('movie_name', 'Unknown Movie'), self.styles['MovieTitle']))
        
        ticket_info = [
            ['Booking ID:', f"#{booking_data.get('id', 'N/A')}"],
            ['Ticket ID:', f"#{ticket_data.get('id', 'N/A')}"],
            ['Date & Time:', f"{booking_data.get('date', datetime.date.today()).strftime('%A, %B %d, %Y')} at {self._format_time(booking_data.get('starttime', 0))}"],
            ['Theater:', booking_data.get('room_name', 'N/A')],
            ['Seat:', ticket_data.get('seat_number', 'N/A')],
            ['Type:', ticket_data.get('seat_type', 'Standard')],
            ['Price:', f"€{ticket_data.get('price', 0):.2f}"]
        ]
        
        ticket_table = Table(ticket_info, colWidths=[2*inch, 3*inch])
        ticket_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0d6efd')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ]))
        story.append(ticket_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _format_time(self, seconds) -> str:
        """Convert seconds to HH:MM format"""
        # Convert to int to handle both int and float inputs
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    
    def _is_booking_expired(self, booking_data: Dict[str, Any]) -> bool:
        """Check if a booking is expired"""
        try:
            booking_date = booking_data.get('date')
            start_time = booking_data.get('starttime', 0)
            
            if not booking_date:
                return False
            
            # Convert to datetime
            if isinstance(booking_date, str):
                booking_date = datetime.datetime.strptime(booking_date, '%Y-%m-%d').date()
            
            booking_datetime = datetime.datetime.combine(booking_date, datetime.time(0, 0)) + datetime.timedelta(seconds=start_time)
            
            return booking_datetime < datetime.datetime.now()
        except:
            return False

# Convenience function for easy import
def create_pdf_generator() -> TicketPDFGenerator:
    """Create and return a new PDF generator instance"""
    return TicketPDFGenerator()
