"""
Email service module for sending booking confirmations with PDF attachments.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from .config import get_config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with booking confirmations."""
    
    def __init__(self):
        self.config = get_config()
        
    def send_booking_confirmation(self, booking_data, pdf_content, booker_email, booker_name):
        """
        Send booking confirmation email with PDF ticket attachment.
        
        Args:
            booking_data: Dictionary containing booking information
            pdf_content: PDF file content as bytes
            booker_email: Email address to send to
            booker_name: Name of the booker for personalization
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Handle BytesIO objects by extracting bytes
            from io import BytesIO
            if isinstance(pdf_content, BytesIO):
                pdf_content = pdf_content.getvalue()
            
            # Create email message
            msg = MIMEMultipart()
            
            # Email headers
            msg['From'] = formataddr(('Cinemacousas', self.config.EMAIL_FROM))
            msg['To'] = booker_email
            msg['Subject'] = f"Confirmation de réservation - {booking_data.get('movie_name', 'Cinéma')}"
            
            # Create email body
            html_body = self._create_email_body(booking_data, booker_name)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Attach PDF
            # Create a safe filename using booker name
            safe_booker_name = "".join(c for c in booker_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_booker_name = safe_booker_name.replace(' ', '_')
            pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename=f"tickets_{safe_booker_name}_{booking_data.get('id', 'unknown')}.pdf"
            )
            msg.attach(pdf_attachment)
            
            # Send email
            return self._send_email(msg)
            
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email: {e}")
            return False
    
    def _create_email_body(self, booking_data, booker_name):
        """Create HTML email body for booking confirmation."""
        
        # Format date and time
        show_date = booking_data.get('date', 'N/A')
        start_time = booking_data.get('starttime', 0)
        
        # Convert start time to HH:MM format
        if isinstance(start_time, (int, float)):
            hours = int(start_time // 3600)
            minutes = int((start_time % 3600) // 60)
            formatted_time = f"{hours:02d}:{minutes:02d}"
        else:
            formatted_time = str(start_time)
        
        # Format price
        price = booking_data.get('price', 0)
        if isinstance(price, (int, float)):
            price_euros = price / 100.0  # Convert cents to euros
            formatted_price = f"{price_euros:.2f} €"
        else:
            formatted_price = f"{price} €"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmation de réservation</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e9ecef;
                }}
                .logo {{
                    font-size: 2em;
                    font-weight: bold;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin-bottom: 10px;
                }}
                .booking-details {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #495057;
                }}
                .detail-value {{
                    color: #212529;
                }}
                .price {{
                    font-size: 1.2em;
                    font-weight: bold;
                    color: #28a745;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #e9ecef;
                    color: #6c757d;
                    font-size: 0.9em;
                }}
                .attachment-note {{
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .movie-title {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #495057;
                    text-align: center;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎬 Cinemacousas</div>
                    <h1>Confirmation de réservation</h1>
                    <p>Bonjour <strong>{booker_name}</strong>,</p>
                    <p>Votre réservation a été confirmée avec succès !</p>
                </div>
                
                <div class="movie-title">
                    🎭 {booking_data.get('movie_name', 'Film')}
                </div>
                
                <div class="booking-details">
                    <div class="detail-row">
                        <span class="detail-label">📅 Date de la séance:</span>
                        <span class="detail-value">{show_date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🕐 Heure:</span>
                        <span class="detail-value">{formatted_time}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🏛️ Salle:</span>
                        <span class="detail-value">{booking_data.get('room_name', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🎫 Nombre de places:</span>
                        <span class="detail-value">{booking_data.get('num_spectators', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📋 Numéro de réservation:</span>
                        <span class="detail-value">#{booking_data.get('booking_id', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">💰 Prix total:</span>
                        <span class="detail-value price">{formatted_price}</span>
                    </div>
                </div>
                
                <div class="attachment-note">
                    <strong>📎 Vos billets sont en pièce jointe</strong><br>
                    Veuillez présenter ce document PDF à l'entrée du cinéma.
                </div>
                
                <div class="footer">
                    <p><strong>Informations importantes :</strong></p>
                    <ul style="text-align: left; display: inline-block;">
                        <li>Présentez-vous 15 minutes avant le début de la séance</li>
                        <li>Les billets sont nominatifs et non remboursables</li>
                        <li>Merci de respecter les places qui vous ont été attribuées</li>
                    </ul>
                    <p>Nous vous souhaitons une excellente séance !</p>
                    <p><em>L'équipe Cinemacousas</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _send_email(self, msg):
        """Send email using SMTP."""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.config.EMAIL_HOST, self.config.EMAIL_PORT)
            
            # Enable TLS encryption
            if self.config.EMAIL_USE_TLS:
                server.starttls()
            
            # Login to server
            server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.config.EMAIL_FROM, msg['To'], text)
            server.quit()
            
            logger.info(f"Booking confirmation email sent successfully to {msg['To']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


def send_booking_confirmation_email(booking_data, pdf_content, booker_email, booker_name):
    """
    Convenience function to send booking confirmation email.
    
    Args:
        booking_data: Dictionary containing booking information
        pdf_content: PDF file content as bytes
        booker_email: Email address to send to
        booker_name: Name of the booker for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    email_service = EmailService()
    return email_service.send_booking_confirmation(booking_data, pdf_content, booker_email, booker_name)
