"""
Generator PDF dla karty drogowej SM-102
"""

import logging
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import qrcode
from io import BytesIO

from src.models.trip_sheet import TripSheet
from src.models.vehicle import Vehicle
from src.models.employee import Employee

class PDFService:
    """Usługa generowania dokumentów PDF"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.output_path = Path(config['pdf']['output_path'])
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_trip_sheet_pdf(self, trip_sheet: TripSheet, vehicle: Vehicle, 
                               employee: Employee, trips: list) -> str:
        """Generuje kartę drogową SM-102 w formacie PDF"""
        
        # Utwórz nazwę pliku
        filename = f"karta_drogowa_{trip_sheet.sheet_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_path / filename
        
        # Utwórz dokument
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Elementy dokumentu
        story = []
        styles = getSampleStyleSheet()
        
        # Dodaj własne style
        self.add_custom_styles(styles)
        
        # Nagłówek
        story.append(self.create_header(styles))
        story.append(Spacer(1, 0.5*cm))
        
        # Informacje podstawowe
        story.append(self.create_basic_info_table(trip_sheet, vehicle, employee, styles))
        story.append(Spacer(1, 0.5*cm))
        
        # Tabela przejazdów
        story.append(self.create_trips_table(trips, styles))
        story.append(Spacer(1, 0.5*cm))
        
        # Podsumowanie
        story.append(self.create_summary_table(trips, vehicle, styles))
        story.append(Spacer(1, 1*cm))
        
        # Podpisy
        story.append(self.create_signature_section(styles))
        
        # Stopka z QR code
        story.append(self.create_footer(trip_sheet, styles))
        
        # Generuj PDF
        doc.build(story)
        
        self.logger.info(f"Wygenerowano kartę drogową PDF: {filepath}")
        return str(filepath)
    
    def add_custom_styles(self, styles):
        """Dodaje niestandardowe style do dokumentu"""
        # Styl dla nagłówka
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=12,
            alignment=1  # Center
        ))
        
        # Styl dla podtytułów
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Styl dla komórek tabeli
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=10
        ))
    
    def create_header(self, styles):
        """Tworzy nagłówek dokumentu"""
        header_elements = []
        
        # Tytuł
        title = Paragraph("<b>KARTA DROGOWA SM-102</b>", styles['CustomTitle'])
        header_elements.append(title)
        
        # Informacja o firmie
        company_info = Paragraph(
            f"<b>{self.config['app']['company']}</b><br/>"
            f"System Ewidencji Pojazdów v{self.config['app']['version']}",
            styles['Normal']
        )
        header_elements.append(company_info)
        
        # Data generowania
        gen_date = Paragraph(
            f"Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            styles['Italic']
        )
        header_elements.append(gen_date)
        
        return header_elements
    
    def create_basic_info_table(self, trip_sheet, vehicle, employee, styles):
        """Tworzy tabelę z informacjami podstawowymi"""
        data = [
            ["Numer karty:", trip_sheet.sheet_number, "Data:", trip_sheet.date.strftime('%d.%m.%Y')],
            ["Pojazd:", f"{vehicle.registration_number} ({vehicle.brand} {vehicle.model})", 
             "Paliwo:", vehicle.fuel_type],
            ["Pracownik:", f"{employee.first_name} {employee.last_name}", 
             "Stanowisko:", employee.position],
            ["Przebieg początkowy:", f"{trip_sheet.start_mileage:.1f} km", 
             "Status:", self.get_polish_status(trip_sheet.status)]
        ]
        
        table = Table(data, colWidths=[4*cm, 6*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def create_trips_table(self, trips, styles):
        """Tworzy tabelę przejazdów"""
        # Nagłówki kolumn
        headers = ["Lp.", "Godzina rozpoczęcia", "Godzina zakończenia", 
                  "Miejsce rozpoczęcia", "Miejsce zakończenia", "Cel przejazdu", "Uwagi"]
        
        data = [headers]
        
        # Dodaj wiersze z danymi
        for i, trip in enumerate(trips, 1):
            row = [
                str(i),
                trip.start_time.strftime('%H:%M'),
                trip.end_time.strftime('%H:%M'),
                trip.from_location,
                trip.to_location,
                trip.purpose,
                trip.notes or "-"
            ]
            data.append(row)
        
        # Utwórz tabelę
        col_widths = [1*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 4*cm]
        table = Table(data, colWidths=col_widths)
        
        # Styl tabeli
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            
            # Naprzemienne tło wierszy
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ])
        
        table.setStyle(table_style)
        return table
    
    def create_summary_table(self, trips, vehicle, styles):
        """Tworzy tabelę podsumowującą"""
        # Oblicz sumaryczne wartości
        total_distance = sum(trip.distance for trip in trips if trip.distance)
        fuel_used = vehicle.calculate_fuel_usage(total_distance)
        
        data = [
            ["PODSUMOWANIE:", "", "", ""],
            ["Łączna odległość:", f"{total_distance:.1f} km", "Średnie spalanie:", f"{vehicle.fuel_consumption} l/100km"],
            ["Zużyte paliwo:", f"{fuel_used:.2f} l", "Typ paliwa:", vehicle.fuel_type],
            ["Przebieg końcowy:", f"{vehicle.current_mileage:.1f} km", "Data zamknięcia:", datetime.now().strftime('%d.%m.%Y')]
        ]
        
        table = Table(data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (3, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        
        return table
    
    def create_signature_section(self, styles):
        """Tworzy sekcję podpisów"""
        data = [
            ["", "", ""],
            ["Podpis pracownika:", "Podpis kierownika:", "Data odbioru:"],
            [".................................", ".................................", "...................."],
            ["", "", ""],
            ["Uwagi i zastrzeżenia:", "", ""],
            ["................................................................................", "", ""],
            ["................................................................................", "", ""]
        ]
        
        table = Table(data, colWidths=[6*cm, 6*cm, 4*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, 2), 0.5, colors.grey),
            
            ('SPAN', (0, 4), (2, 4)),
            ('SPAN', (0, 5), (2, 5)),
            ('SPAN', (0, 6), (2, 6)),
            
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            
            ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#f1c40f')),
        ]))
        
        return table
    
    def create_footer(self, trip_sheet, styles):
        """Tworzy stopkę z kodem QR"""
        # Generuj kod QR z numerem karty
        qr_data = f"KARTA_DROGOWA:{trip_sheet.sheet_number}:{trip_sheet.date.strftime('%Y%m%d')}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Zapisz kod QR do bufora
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Utwórz element z kodem QR
        qr_table_data = [
            ["Kod QR karty drogowej:", ""],
            ["", ""]
        ]
        
        qr_table = Table(qr_table_data, colWidths=[10*cm, 6*cm])
        
        # Dodaj kod QR do komórki tabeli
        from reportlab.platypus import Image
        qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
        
        table_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (1, 0), (1, 0), 50),
        ])
        
        qr_table.setStyle(table_style)
        
        # Ustaw obraz w komórce
        qr_table._argW[1] = 3*cm
        qr_table._argH[0] = 3*cm
        
        return qr_table
    
    def get_polish_status(self, status: str) -> str:
        """Konwertuje status na polski"""
        status_map = {
            'otwarta': 'Otwarta',
            'zamknięta': 'Zamknięta',
            'archiwum': 'Archiwum'
        }
        return status_map.get(status, status)