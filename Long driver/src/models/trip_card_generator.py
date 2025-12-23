# -*- coding: utf-8 -*-
"""
Generator PDF karty drogowej (wzór zbliżony do SM-102)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import sqlite3
from pathlib import Path


class TripCardGenerator:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"

        # Rejestracja fontów z polskimi znakami (DejaVu)
        try:
            pdfmetrics.registerFont(
                TTFont("DejaVuSans", "C:\\Windows\\Fonts\\DejaVuSans.ttf")
            )
            pdfmetrics.registerFont(
                TTFont("DejaVuSans-Bold", "C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf")
            )
        except Exception:
            # Fallback - systemowe, mogą nie mieć wszystkich PL znaków
            pass

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except Exception:
            return None

    def get_trip_data(self, trip_id):
        """Pobiera dane przejazdu z bazy"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    t.id,
                    t.trip_number,
                    t.start_date,
                    t.end_date,
                    v.registration_number,
                    v.brand,
                    v.model,
                    v.fuel_consumption,
                    e.first_name,
                    e.last_name,
                    t.start_mileage,
                    t.end_mileage,
                    t.start_fuel,
                    t.end_fuel,
                    t.distance,
                    t.fuel_used,
                    t.calculated_fuel,
                    t.purpose,
                    t.ordered_by,
                    t.notes,
                    t.vehicle_ok,
                    t.fuel_cost
                FROM trips t
                JOIN vehicles v ON t.vehicle_id = v.id
                JOIN employees e ON t.employee_id = e.id
                WHERE t.id = ?
                """,
                (trip_id,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def generate_pdf(self, trip_id, output_path=None):
        """Generuje PDF karty drogowej"""
        trip_data = self.get_trip_data(trip_id)
        if not trip_data:
            raise ValueError(f"Nie znaleziono przejazdu o ID {trip_id}")

        (
            trip_id_val,
            trip_number,
            start_date,
            end_date,
            registration,
            brand,
            model,
            consumption,
            driver_first,
            driver_last,
            start_mileage,
            end_mileage,
            start_fuel,
            end_fuel,
            distance,
            fuel_used,
            calculated_fuel,
            purpose,
            ordered_by,
            notes,
            vehicle_ok,
            fuel_cost,
        ) = trip_data

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trip_num_safe = (trip_number or f"TRIP_{trip_id_val}").replace("/", "_")
            output_path = f"karta_drogowa_{trip_num_safe}_{timestamp}.pdf"

        # Dokument
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.8 * cm,
            leftMargin=0.8 * cm,
            topMargin=0.8 * cm,
            bottomMargin=0.8 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#008000"),
            alignment=1,
            spaceAfter=10,
            fontName="DejaVuSans-Bold",
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=11,
            textColor=colors.HexColor("#00695C"),
            spaceAfter=4,
            fontName="DejaVuSans-Bold",
        )
        normal_style = ParagraphStyle(
            "NormalPL",
            parent=styles["Normal"],
            fontSize=9,
            fontName="DejaVuSans",
        )

        elements = []

        # NAGŁÓWEK
        elements.append(Paragraph("KARTA DROGOWA", title_style))

        header_data = [
            [
                Paragraph(f"<b>Nr karty:</b> {trip_number or 'BRAK'}", normal_style),
                Paragraph(
                    f"<b>Data rozpoczęcia:</b> {start_date.split()[0] if start_date else ''}",
                    normal_style,
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=[8 * cm, 8 * cm])
        header_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F5E9")),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 0.3 * cm))

        # POJAZD
        elements.append(Paragraph("POJAZD", heading_style))
        vehicle_data = [
            ["Marka i model:", f"{brand} {model}"],
            ["Nr rejestracyjny:", registration or "---"],
            ["Średnie spalanie:", f"{consumption or 0:.1f} L/100km"],
        ]
        vehicle_table = Table(vehicle_data, colWidths=[4.5 * cm, 11.5 * cm])
        vehicle_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(vehicle_table)
        elements.append(Spacer(1, 0.3 * cm))

        # KIEROWCA
        elements.append(Paragraph("KIEROWCA", heading_style))
        driver_data = [
            ["Imię i nazwisko:", f"{driver_first} {driver_last}"],
            ["Zlecił wyjazd:", ordered_by or "---"],
        ]
        driver_table = Table(driver_data, colWidths=[4.5 * cm, 11.5 * cm])
        driver_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(driver_table)
        elements.append(Spacer(1, 0.3 * cm))

        # PRZEJAZD
        elements.append(Paragraph("PRZEJAZD", heading_style))
        journey_data = [
            ["Start (data i godz.):", start_date or "---"],
            ["Koniec (data i godz.):", end_date or "AKTYWNY"],
            ["Cel / trasa:", purpose or "---"],
        ]
        journey_table = Table(journey_data, colWidths=[4.5 * cm, 11.5 * cm])
        journey_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(journey_table)
        elements.append(Spacer(1, 0.3 * cm))

        # PRZEBIEG
        elements.append(Paragraph("PRZEBIEG LICZNIKA", heading_style))
        mileage_data = [
            ["Stan licznika przy wyjeździe:", f"{start_mileage or 0:.1f} km"],
            ["Stan licznika przy powrocie:", f"{end_mileage or 0:.1f} km"],
            ["DYSTANS:", f"{distance or 0:.1f} km"],
        ]
        mileage_table = Table(mileage_data, colWidths=[6 * cm, 10 * cm])
        mileage_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FFF3E0")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                    ("FONTNAME", (0, 2), (-1, 2), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(mileage_table)
        elements.append(Spacer(1, 0.3 * cm))

        # PALIWO
        elements.append(Paragraph("PALIWO", heading_style))
        fuel_data = [
            ["Stan paliwa przy wyjeździe:", f"{start_fuel or 0:.1f} L"],
            ["Stan paliwa przy powrocie:", f"{end_fuel or 0:.1f} L"],
            ["ZUŻYTE (rzeczywiste):", f"{fuel_used or 0:.1f} L"],
            ["PRZELICZONE wg normy:", f"{calculated_fuel or 0:.1f} L"],
            ["Koszt paliwa:", f"{fuel_cost or 0:.2f} zł" if fuel_cost else "0.00 zł"],
        ]
        fuel_table = Table(fuel_data, colWidths=[6 * cm, 10 * cm])
        fuel_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("BACKGROUND", (0, 2), (0, 3), colors.HexColor("#FFEBEE")),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(fuel_table)
        elements.append(Spacer(1, 0.3 * cm))

        # STAN POJAZDU
        elements.append(Paragraph("STAN POJAZDU", heading_style))
        vehicle_status = "SPRAWNY" if vehicle_ok else "USZKODZONY / UWAGI"
        status_data = [
            ["Status pojazdu:", vehicle_status],
        ]
        status_table = Table(status_data, colWidths=[6 * cm, 10 * cm])
        status_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (1, 0),
                        colors.HexColor("#C8E6C9")
                        if vehicle_ok
                        else colors.HexColor("#FFCDD2"),
                    ),
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(status_table)
        elements.append(Spacer(1, 0.3 * cm))

        # UWAGI
        if notes:
            elements.append(Paragraph("UWAGI", heading_style))
            notes_data = [[Paragraph(notes, normal_style)]]
            notes_table = Table(notes_data, colWidths=[16 * cm])
            notes_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(notes_table)
            elements.append(Spacer(1, 0.3 * cm))

        # PODPISY
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("PODPISY", heading_style))
        signature_data = [
            ["Kierowca:", "_" * 35, "Data:", "_" * 18],
            ["Wystawił kartę:", "_" * 35, "Data:", "_" * 18],
        ]
        signature_table = Table(signature_data, colWidths=[3.5 * cm, 7 * cm, 2.5 * cm, 3 * cm])
        signature_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "DejaVuSans-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "DejaVuSans-Bold"),
                ]
            )
        )
        elements.append(signature_table)

        # STOPKA
        elements.append(Spacer(1, 0.5 * cm))
        generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = Paragraph(
            f"Wygenerowano: {generated_date}",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                alignment=1,
                fontName="DejaVuSans",
            ),
        )
        elements.append(footer)

        doc.build(elements)
        return output_path


# ==========================
# Standalone test
# ==========================
if __name__ == "__main__":
    generator = TripCardGenerator()
    try:
        output = generator.generate_pdf(trip_id=1)
        print(f"✅ PDF wygenerowany: {output}")
    except Exception as e:
        print(f"❌ Błąd: {e}")
