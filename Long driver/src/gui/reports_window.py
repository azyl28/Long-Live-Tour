# -*- coding: utf-8 -*-
"""
Okno generowania raport車w
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QFormLayout, QGroupBox, QDateEdit, QCheckBox,
    QTextEdit, QSplitter, QProgressBar, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import tempfile
import os

class ReportsWindow(QWidget):
    """Okno generowania raport車w"""
    
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_report_types()
    
    def setup_ui(self):
        """Konfiguruje interfejs"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Nag?車wek
        header = QLabel("?? Generowanie Raport車w")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel konfiguracji
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        
        config_group = QGroupBox("?? Konfiguracja raportu")
        config_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        form = QFormLayout()
        
        # Typ raportu
        self.report_type = QComboBox()
        
        # Okres
        period_group = QGroupBox("?? Okres raportowania")
        period_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        period_layout.addWidget(QLabel("Od:"))
        period_layout.addWidget(self.date_from)
        period_layout.addWidget(QLabel("Do:"))
        period_layout.addWidget(self.date_to)
        period_group.setLayout(period_layout)
        
        # Szybkie okresy
        self.quick_periods = QComboBox()
        self.quick_periods.addItems([
            "Dzisiaj",
            "Ostatnie 7 dni",
            "Bie??cy tydzie里",
            "Ostatni miesi?c",
            "Bie??cy miesi?c",
            "Bie??cy rok",
            "Niestandardowy"
        ])
        self.quick_periods.currentTextChanged.connect(self.on_quick_period_changed)
        
        # Opcje
        options_group = QGroupBox("?? Opcje raportu")
        options_layout = QVBoxLayout()
        
        self.export_excel = QCheckBox("Eksport do Excel")
        self.export_pdf = QCheckBox("Eksport do PDF")
        self.export_pdf.setChecked(True)
        
        options_layout.addWidget(self.export_excel)
        options_layout.addWidget(self.export_pdf)
        options_group.setLayout(options_layout)
        
        # Notatki
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Notatki do raportu...")
        
        form.addRow("Typ raportu*:", self.report_type)
        form.addRow("Szybki okres:", self.quick_periods)
        form.addRow(period_group)
        form.addRow(options_group)
        form.addRow("Notatki:", self.notes)
        
        config_group.setLayout(form)
        config_layout.addWidget(config_group)
        
        # Przyciski
        button_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("?? Generuj raport")
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        self.generate_button.clicked.connect(self.generate_report)
        
        self.preview_button = QPushButton("??? Podgl?d danych")
        self.preview_button.setStyleSheet("background-color: #3498db; color: white;")
        self.preview_button.clicked.connect(self.preview_data)
        
        self.clear_button = QPushButton("??? Wyczy??")
        self.clear_button.setStyleSheet("background-color: #95a5a6; color: white;")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.clear_button)
        
        config_layout.addLayout(button_layout)
        
        # Pasek post?pu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        config_layout.addWidget(self.progress_bar)
        
        config_widget.setLayout(config_layout)
        
        # Panel podgl?du
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        preview_header = QLabel("??? Podgl?d danych")
        preview_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        preview_layout.addWidget(preview_header)
        
        # Tabela podgl?du
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(1)
        self.preview_table.setHorizontalHeaderLabels(["Podgl?d danych"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        preview_layout.addWidget(self.preview_table)
        
        # Statystyki
        stats_group = QGroupBox("?? Statystyki")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        preview_layout.addWidget(stats_group)
        
        preview_widget.setLayout(preview_layout)
        
        # Dodaj do splittera
        splitter.addWidget(config_widget)
        splitter.addWidget(preview_widget)
        splitter.setSizes([500, 900])
        
        main_layout.addWidget(splitter)
    
    def load_report_types(self):
        """?aduje typy raport車w"""
        report_types = [
            "?? Przegl?d og車lny",
            "?? Aktywno?? pojazd車w",
            "?? Aktywno?? kierowc車w",
            "? Zu?ycie paliwa",
            "?? Koszty eksploatacji",
            "?? Harmonogram serwis車w",
            "?? Historia wypo?ycze里",
            "??? Raport przejazd車w",
            "?? Miesi?czny przegl?d"
        ]
        
        self.report_type.addItems(report_types)
    
    def on_quick_period_changed(self, period):
        """Ustawia daty na podstawie szybkiego okresu"""
        today = QDate.currentDate()
        
        if period == "Dzisiaj":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif period == "Ostatnie 7 dni":
            self.date_from.setDate(today.addDays(-7))
            self.date_to.setDate(today)
        elif period == "Bie??cy tydzie里":
            day_of_week = today.dayOfWeek()
            self.date_from.setDate(today.addDays(1 - day_of_week))
            self.date_to.setDate(today)
        elif period == "Ostatni miesi?c":
            self.date_from.setDate(today.addMonths(-1))
            self.date_to.setDate(today)
        elif period == "Bie??cy miesi?c":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif period == "Bie??cy rok":
            self.date_from.setDate(QDate(today.year(), 1, 1))
            self.date_to.setDate(today)
    
    def get_connection(self):
        """Po??czenie z baz? danych"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "B??d", f"B??d po??czenia z baz?:\n{str(e)}")
            return None
    
    def generate_report(self):
        """Generuje raport"""
        report_type = self.report_type.currentText()
        
        if not report_type:
            QMessageBox.warning(self, "B??d", "Wybierz typ raportu!")
            return
        
        # Poka? post?p
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Symulacja post?pu
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.progress_bar.setValue(self.progress_bar.value() + 10))
        timer.start(100)
        
        try:
            # Pobierz dane
            data = self.get_report_data(report_type)
            
            # Generuj raporty
            if self.export_excel.isChecked():
                self.export_to_excel(data, report_type)
            
            if self.export_pdf.isChecked():
                self.export_to_pdf(data, report_type)
            
            # Ukryj post?p
            timer.stop()
            self.progress_bar.setVisible(False)
            
            # Poka? podgl?d
            self.show_preview(data)
            
            QMessageBox.information(self, "Sukces", 
                f"Raport '{report_type}' zosta? wygenerowany pomy?lnie!")
            
        except Exception as e:
            timer.stop()
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "B??d", f"B??d generowania raportu:\n{str(e)}")
    
    def get_report_data(self, report_type):
        """Pobiera dane dla raportu"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        try:
            cursor = conn.cursor()
            data = {}
            
            if "Przegl?d og車lny" in report_type:
                # Statystyki pojazd車w
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM vehicles 
                    GROUP BY status
                """)
                data['vehicle_stats'] = cursor.fetchall()
                
                # Statystyki pracownik車w
                cursor.execute("""
                    SELECT 
                        CASE WHEN is_active = 1 THEN 'Aktywni' ELSE 'Nieaktywni' END as status,
                        COUNT(*) as count 
                    FROM employees 
                    GROUP BY is_active
                """)
                data['employee_stats'] = cursor.fetchall()
                
                # Aktywne wypo?yczenia
                cursor.execute("""
                    SELECT COUNT(*) as active_checkouts 
                    FROM key_logs 
                    WHERE return_date IS NULL
                """)
                data['active_checkouts'] = cursor.fetchone()[0]
                
                # Aktywne przejazdy
                cursor.execute("""
                    SELECT COUNT(*) as active_trips 
                    FROM trips 
                    WHERE end_date IS NULL
                """)
                data['active_trips'] = cursor.fetchone()[0]
            
            elif "Aktywno?? pojazd車w" in report_type:
                cursor.execute("""
                    SELECT 
                        v.registration_number,
                        v.brand,
                        v.model,
                        COUNT(DISTINCT t.id) as trip_count,
                        SUM(t.distance) as total_distance,
                        COUNT(DISTINCT kl.id) as checkout_count
                    FROM vehicles v
                    LEFT JOIN trips t ON v.id = t.vehicle_id 
                        AND t.start_date BETWEEN ? AND ?
                    LEFT JOIN key_logs kl ON v.id = kl.vehicle_id 
                        AND kl.checkout_date BETWEEN ? AND ?
                    GROUP BY v.id
                    ORDER BY trip_count DESC
                """, (date_from, date_to, date_from, date_to))
                data['vehicle_activity'] = cursor.fetchall()
            
            elif "Aktywno?? kierowc車w" in report_type:
                cursor.execute("""
                    SELECT 
                        e.first_name,
                        e.last_name,
                        e.position,
                        COUNT(DISTINCT t.id) as trip_count,
                        SUM(t.distance) as total_distance,
                        COUNT(DISTINCT kl.id) as checkout_count
                    FROM employees e
                    LEFT JOIN trips t ON e.id = t.employee_id 
                        AND t.start_date BETWEEN ? AND ?
                    LEFT JOIN key_logs kl ON e.id = kl.employee_id 
                        AND kl.checkout_date BETWEEN ? AND ?
                    WHERE e.is_active = 1
                    GROUP BY e.id
                    ORDER BY trip_count DESC
                """, (date_from, date_to, date_from, date_to))
                data['driver_activity'] = cursor.fetchall()
            
            elif "Historia wypo?ycze里" in report_type:
                cursor.execute("""
                    SELECT 
                        kl.checkout_date,
                        kl.return_date,
                        v.registration_number,
                        v.brand,
                        v.model,
                        e.first_name,
                        e.last_name,
                        CASE 
                            WHEN kl.return_date IS NULL THEN 'Aktywne'
                            ELSE 'Zako里czone'
                        END as status
                    FROM key_logs kl
                    JOIN vehicles v ON kl.vehicle_id = v.id
                    JOIN employees e ON kl.employee_id = e.id
                    WHERE kl.checkout_date BETWEEN ? AND ?
                    ORDER BY kl.checkout_date DESC
                """, (date_from, date_to))
                data['key_history'] = cursor.fetchall()
            
            elif "Raport przejazd車w" in report_type:
                cursor.execute("""
                    SELECT 
                        t.start_date,
                        t.end_date,
                        v.registration_number,
                        e.first_name,
                        e.last_name,
                        t.distance,
                        t.purpose,
                        t.notes
                    FROM trips t
                    JOIN vehicles v ON t.vehicle_id = v.id
                    JOIN employees e ON t.employee_id = e.id
                    WHERE t.start_date BETWEEN ? AND ?
                    ORDER BY t.start_date DESC
                """, (date_from, date_to))
                data['trips_report'] = cursor.fetchall()
            
            data['report_type'] = report_type
            data['period'] = f"{date_from} - {date_to}"
            data['generated_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return data
            
        finally:
            conn.close()
    
    def export_to_excel(self, data, report_type):
        """Eksportuje do Excel"""
        try:
            # Utw車rz DataFrame
            df = None
            
            if 'vehicle_activity' in data:
                df = pd.DataFrame(data['vehicle_activity'], 
                    columns=['Nr rejestracyjny', 'Marka', 'Model', 'Liczba przejazd車w', 'Dystans', 'Wypo?yczenia'])
            
            elif 'driver_activity' in data:
                df = pd.DataFrame(data['driver_activity'],
                    columns=['Imi?', 'Nazwisko', 'Stanowisko', 'Liczba przejazd車w', 'Dystans', 'Wypo?yczenia'])
            
            elif 'key_history' in data:
                df = pd.DataFrame(data['key_history'],
                    columns=['Data wyp.', 'Data zwr.', 'Nr rej.', 'Marka', 'Model', 'Imi?', 'Nazwisko', 'Status'])
            
            elif 'trips_report' in data:
                df = pd.DataFrame(data['trips_report'],
                    columns=['Start', 'Koniec', 'Nr rej.', 'Kierowca', 'Nazwisko', 'Dystans', 'Cel', 'Uwagi'])
            
            if df is not None:
                # Zapytaj o miejsce zapisu
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Zapisz raport Excel", 
                    f"raport_{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "Excel Files (*.xlsx)"
                )
                
                if file_path:
                    df.to_excel(file_path, index=False)
                    print(f"Raport Excel zapisany: {file_path}")
            
        except Exception as e:
            print(f"B??d eksportu do Excel: {e}")
    
    def export_to_pdf(self, data, report_type):
        """Eksportuje do PDF (symulacja)"""
        try:
            # Tutaj mo?na doda? rzeczywiste generowanie PDF z ReportLab
            # Na razie tylko komunikat
            print(f"Generowanie PDF: {report_type}")
            
            QMessageBox.information(self, "PDF", 
                f"Raport '{report_type}' gotowy do eksportu PDF.\n"
                f"Funkcja PDF w przygotowaniu.\n"
                f"Dane dost?pne w podgl?dzie.")
            
        except Exception as e:
            print(f"B??d eksportu do PDF: {e}")
    
    def preview_data(self):
        """Pokazuje podgl?d danych"""
        report_type = self.report_type.currentText()
        
        if not report_type:
            QMessageBox.warning(self, "B??d", "Wybierz typ raportu!")
            return
        
        data = self.get_report_data(report_type)
        self.show_preview(data)
    
    def show_preview(self, data):
        """Pokazuje podgl?d danych w tabeli"""
        if not data:
            self.preview_table.setRowCount(0)
            self.stats_text.clear()
            return
        
        # Wy?wietl odpowiednie dane w zale?no?ci od typu raportu
        if 'vehicle_activity' in data:
            rows = data['vehicle_activity']
            self.preview_table.setColumnCount(6)
            self.preview_table.setHorizontalHeaderLabels([
                'Nr rej.', 'Marka', 'Model', 'Przejazdy', 'Dystans', 'Wypo?yczenia'
            ])
            self.display_data_in_table(rows)
            
        elif 'driver_activity' in data:
            rows = data['driver_activity']
            self.preview_table.setColumnCount(6)
            self.preview_table.setHorizontalHeaderLabels([
                'Imi?', 'Nazwisko', 'Stanowisko', 'Przejazdy', 'Dystans', 'Wypo?yczenia'
            ])
            self.display_data_in_table(rows)
            
        elif 'key_history' in data:
            rows = data['key_history']
            self.preview_table.setColumnCount(8)
            self.preview_table.setHorizontalHeaderLabels([
                'Wypo?yczenie', 'Zwrot', 'Nr rej.', 'Marka', 'Model', 'Imi?', 'Nazwisko', 'Status'
            ])
            self.display_data_in_table(rows)
            
        elif 'trips_report' in data:
            rows = data['trips_report']
            self.preview_table.setColumnCount(8)
            self.preview_table.setHorizontalHeaderLabels([
                'Start', 'Koniec', 'Nr rej.', 'Kierowca', 'Nazwisko', 'Dystans', 'Cel', 'Uwagi'
            ])
            self.display_data_in_table(rows)
        
        # Wy?wietl statystyki
        stats_text = f"""
        <b>Raport:</b> {data.get('report_type', '')}<br>
        <b>Okres:</b> {data.get('period', '')}<br>
        <b>Wygenerowano:</b> {data.get('generated_date', '')}<br>
        <br>
        """
        
        if 'vehicle_stats' in data:
            stats_text += "<b>Statystyki pojazd車w:</b><br>"
            for status, count in data['vehicle_stats']:
                stats_text += f"  {status}: {count}<br>"
        
        if 'employee_stats' in data:
            stats_text += "<br><b>Statystyki pracownik車w:</b><br>"
            for status, count in data['employee_stats']:
                stats_text += f"  {status}: {count}<br>"
        
        if 'active_checkouts' in data:
            stats_text += f"<br><b>Aktywne wypo?yczenia:</b> {data['active_checkouts']}<br>"
        
        if 'active_trips' in data:
            stats_text += f"<b>Aktywne przejazdy:</b> {data['active_trips']}<br>"
        
        self.stats_text.setHtml(stats_text)
    
    def display_data_in_table(self, rows):
        """Wy?wietla dane w tabeli"""
        self.preview_table.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.preview_table.setItem(row_idx, col_idx, item)
        
        # Dopasuj szeroko?? kolumn
        header = self.preview_table.horizontalHeader()
        for i in range(self.preview_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
    
    def clear_form(self):
        """Czy?ci formularz"""
        self.report_type.setCurrentIndex(0)
        self.quick_periods.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.export_excel.setChecked(False)
        self.export_pdf.setChecked(True)
        self.notes.clear()
        self.preview_table.setRowCount(0)
        self.stats_text.clear()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = ReportsWindow()
    window.setWindowTitle("Test - Generowanie Raport車w")
    window.resize(1400, 700)
    window.show()
    sys.exit(app.exec())