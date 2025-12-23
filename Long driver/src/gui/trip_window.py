from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                              QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
                              QComboBox, QFormLayout, QGroupBox, QDateTimeEdit, 
                              QDoubleSpinBox, QLineEdit, QTextEdit, QSplitter, 
                              QCheckBox, QInputDialog, QScrollArea)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QColor
import sqlite3
from pathlib import Path
from datetime import datetime

class TripWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dbpath = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.vehicleconsumption = 0.0
        self.startmileagesaved = 0.0
        self.startfuelsaved = 0.0
        self.setupui()
        self.loaddata()

    def setupui(self):
        mainlayout = QVBoxLayout(self)
        
        # HEADER
        header = QLabel("🚗 ZARZĄDZANIE PRZEJAZDAMI - Long Driver")
        headerfont = QFont()
        headerfont.setPointSize(16)
        headerfont.setBold(True)
        header.setFont(headerfont)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 20px;")
        mainlayout.addWidget(header)

        # SPLITTER: Formularz | Tabela
        splitter = QSplitter(Qt.Horizontal)
        
        # LEWY PANEL - FORMULARZ
        formwidget = QWidget()
        formlayout = QVBoxLayout(formwidget)
        formgroup = QGroupBox("Dodaj / Edytuj przejazd")
        formgroup.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        form = QFormLayout(formgroup)

        # POLA FORMULARZA
        self.tripid = QLineEdit()
        self.tripid.setVisible(False)
        
        self.tripnumber = QLineEdit()
        self.tripnumber.setPlaceholderText("Np. SM10120250001 (opcjonalnie)")
        
        self.vehiclecombo = QComboBox()
        self.vehiclecombo.setPlaceholderText("Wybierz pojazd...")
        self.vehiclecombo.currentIndexChanged.connect(self.onvehicleselected)
        
        self.drivercombo = QComboBox()
        self.drivercombo.setPlaceholderText("Wybierz kierowcę...")
        
        self.startdate = QDateTimeEdit()
        self.startdate.setDateTime(QDateTime.currentDateTime())
        self.startdate.setCalendarPopup(True)
        
        self.enddate = QDateTimeEdit()
        self.enddate.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.enddate.setCalendarPopup(True)
        
        self.quickendcheck = QCheckBox("Zakończ teraz")
        self.quickendcheck.setChecked(True)
        self.quickendcheck.stateChanged.connect(self.toggleenddate)
        
        self.startmileage = QDoubleSpinBox()
        self.startmileage.setRange(0, 1000000)
        self.startmileage.setSuffix(" km")
        self.startmileage.valueChanged.connect(self.calculatelive)
        
        self.endmileage = QDoubleSpinBox()
        self.endmileage.setRange(0, 1000000)
        self.endmileage.setSuffix(" km")
        self.endmileage.valueChanged.connect(self.calculatelive)
        
        self.livedistancelabel = QLabel("Dystans: 0.0 km")
        self.livefuellabel = QLabel("Przeliczone paliwo: 0.0 L")
        self.liveconsumptionlabel = QLabel("Średnie spalanie: -- L/100km")
        
        self.startfuel = QDoubleSpinBox()
        self.startfuel.setRange(0, 200)
        self.startfuel.setSuffix(" L")
        
        self.refuelcheck = QCheckBox("Tankowanie w tym przejeździe")
        self.refuelliters = QDoubleSpinBox()
        self.refuelliters.setRange(0, 1000)
        self.refuelliters.setSuffix(" L")
        self.refuelcost = QDoubleSpinBox()
        self.refuelcost.setRange(0, 100000)
        self.refuelcost.setSuffix(" zł")
        
        self.purpose = QLineEdit()
        self.purpose.setPlaceholderText("np. Dostawa do klienta...")
        self.orderedby = QLineEdit()
        self.orderedby.setPlaceholderText("Np. Kowalski - Dział handlowy")
        self.vehicleokcheck = QCheckBox("Pojazd sprawny do jazdy")
        self.vehicleokcheck.setChecked(True)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        
        self.lastcheckoutinfo = QLabel("Wybierz pojazd → auto-wypełnienie danych")
        self.lastcheckoutinfo.setStyleSheet("QLabel { color: #3498db; font-size: 11pt; padding: 5px; background-color: #ecf0f1; border-radius: 5px; }")

        # RZĘDY FORMULARZA
        form.addRow("ID:", self.tripid)
        form.addRow("Nr karty przejazdu:", self.tripnumber)
        form.addRow("Pojazd:", self.vehiclecombo)
        form.addRow("Kierowca:", self.drivercombo)
        form.addRow("Start:", self.startdate)
        form.addRow("Koniec:", self.enddate)
        form.addRow("", self.quickendcheck)
        form.addRow("Ostatni keylog:", self.lastcheckoutinfo)
        form.addRow("Przebieg start:", self.startmileage)
        form.addRow("Przebieg koniec:", self.endmileage)
        form.addRow("Dystans LIVE:", self.livedistancelabel)
        form.addRow("Paliwo LIVE:", self.livefuellabel)
        form.addRow("Spalanie:", self.liveconsumptionlabel)
        form.addRow("Paliwo start:", self.startfuel)
        form.addRow("Tankowanie:", self.refuelcheck)
        form.addRow("Ilość zatankowana:", self.refuelliters)
        form.addRow("Koszt paliwa:", self.refuelcost)
        form.addRow("Cel:", self.purpose)
        form.addRow("Kto zlecił:", self.orderedby)
        form.addRow("Pojazd sprawny:", self.vehicleokcheck)
        form.addRow("Uwagi:", self.notes)

        # PRZYCISKI
        buttonlayout = QHBoxLayout()
        self.addbutton = QPushButton("🚀 Rozpocznij przejazd")
        self.addbutton.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        self.addbutton.clicked.connect(self.addtrip)
        
        self.endbutton = QPushButton("✅ Zakończ przejazd")
        self.endbutton.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 10px;")
        self.endbutton.clicked.connect(self.endtrip)
        
        self.deletebutton = QPushButton("🗑️ Usuń przejazd")
        self.deletebutton.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 10px;")
        self.deletebutton.clicked.connect(self.deletetrip)
        
        self.clearbutton = QPushButton("🧹 Wyczyść")
        self.clearbutton.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px;")
        self.clearbutton.clicked.connect(self.clearform)

        buttonlayout.addWidget(self.addbutton)
        buttonlayout.addWidget(self.endbutton)
        buttonlayout.addWidget(self.deletebutton)
        buttonlayout.addWidget(self.clearbutton)
        form.addRow(buttonlayout)

        # SCROLL DLA FORMULARZA
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(formgroup)
        formlayout.addWidget(scroll)
        splitter.addWidget(formwidget)

        # PRAWY PANEL - TABELA
        tablewidget = QWidget()
        tablelayout = QVBoxLayout(tablewidget)
        
        filterlayout = QHBoxLayout()
        filterlabel = QLabel("Status:")
        self.statusfilter = QComboBox()
        self.statusfilter.addItems(["Wszystkie", "Aktywne", "Zakończone", "Dzisiaj"])
        self.statusfilter.currentTextChanged.connect(self.loaddata)
        filterlayout.addWidget(filterlabel)
        filterlayout.addWidget(self.statusfilter)
        filterlayout.addStretch()
        tablelayout.addLayout(filterlayout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(["ID", "Nr karty", "Pojazd", "Kierowca", "Start", "Koniec", "Dystans", "Paliwo[L]", "Calc[L]", "Status", "Cel"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.loadtriptoform)
        tablelayout.addWidget(self.table)
        
        splitter.addWidget(tablewidget)
        splitter.setSizes([500, 900])
        mainlayout.addWidget(splitter)
        
        # STATYSTYKI
        statslayout = QHBoxLayout()
        self.totallabel = QLabel("Łącznie: 0 przejazdów")
        self.activelabel = QLabel("Aktywne: 0")
        self.distancelabel = QLabel("Dystans: 0 km")
        statslayout.addWidget(self.totallabel)
        statslayout.addWidget(self.activelabel)
        statslayout.addWidget(self.distancelabel)
        statslayout.addStretch()
        mainlayout.addLayout(statslayout)

    def calculatelive(self):
        start = self.startmileage.value()
        end = self.endmileage.value()
        if start > 0 and end > start:
            distance = end - start
            self.livedistancelabel.setText(f"Dystans: {distance:.1f} km")
            self.livedistancelabel.setStyleSheet("QLabel { color: green; font-size: 12pt; }")
            if self.vehicleconsumption > 0:
                fuelneeded = distance * self.vehicleconsumption / 100.0
                self.livefuellabel.setText(f"Przeliczone paliwo: {fuelneeded:.1f} L")
                self.livefuellabel.setStyleSheet("QLabel { color: orange; font-size: 12pt; }")
        else:
            self.livedistancelabel.setText("Dystans: 0.0 km")
            self.livefuellabel.setText("Przeliczone paliwo: 0.0 L")

    def toggleenddate(self, state):
        self.enddate.setEnabled(not bool(state))

    def getconnection(self):
        try:
            return sqlite3.connect(self.dbpath)
        except Exception as e:
            print(f"BŁĄD POŁĄCZENIA Z BAZĄ: {e}")
            return None

    def onvehicleselected(self, index):
        if index == -1: return
        
        conn = self.getconnection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            vehicleid = self.vehiclecombo.currentData()
            
            # SPALANIE Z POJAZDU
            cursor.execute("SELECT fuelconsumption, currentmileage, currentfuel FROM vehicles WHERE id=?", (vehicleid,))
            vrow = cursor.fetchone()
            if vrow:
                self.vehicleconsumption = vrow[0] or 7.5
                self.startmileagesaved = vrow[1] or 0
                self.startfuelsaved = vrow[2] or 0
                self.liveconsumptionlabel.setText(f"Średnie spalanie: {self.vehicleconsumption:.1f} L/100km")
                self.lastcheckoutinfo.setText(f"AUTO-WYPEŁNIANO: przebieg {self.startmileagesaved:.0f}km | paliwo {self.startfuelsaved:.1f}L")
                self.startmileage.setValue(self.startmileagesaved)
                self.startfuel.setValue(self.startfuelsaved)
                self.calculatelive()
            
        finally:
            conn.close()

    def loaddata(self):
        print("🔄 Ładowanie danych przejazdów...")
        conn = self.getconnection()
        if not conn: 
            print("❌ Brak połączenia z bazą!")
            return
        
        try:
            cursor = conn.cursor()
            
            # DIAGNOSTYKA
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            vehicles_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM employees WHERE isactive=1")
            employees_count = cursor.fetchone()[0]
            print(f"📊 DIAGNOZA: Pojazdy={vehicles_count}, Aktywni pracownicy={employees_count}")
            
            # WSZYSTKIE POJAZDY (NIE TYLKO Z KLUCZEM)
            cursor.execute("SELECT id, registrationnumber || ' - ' || COALESCE(brand,'') || ' ' || COALESCE(model,'') FROM vehicles ORDER BY registrationnumber")
            vehicles = cursor.fetchall()
            print(f"🚗 Znaleziono {len(vehicles)} pojazdów")
            
            self.vehiclecombo.clear()
            for vid, name in vehicles:
                self.vehiclecombo.addItem(name, vid)
            
            # KIEROWCY
            cursor.execute("SELECT id, firstname || ' ' || lastname FROM employees WHERE isactive = 1 ORDER BY lastname, firstname")
            drivers = cursor.fetchall()
            print(f"👤 Znaleziono {len(drivers)} kierowców")
            
            self.drivercombo.clear()
            for eid, name in drivers:
                self.drivercombo.addItem(name, eid)
            
            # TABELA PRZEJAZDÓW
            filtertext = self.statusfilter.currentText()
            query = """SELECT t.id, COALESCE(t.tripnumber, ''), 
                              v.registrationnumber || ' - ' || v.brand || ' ' || v.model,
                              e.firstname || ' ' || e.lastname,
                              t.startdate, t.enddate, COALESCE(t.distance, 0),
                              COALESCE(t.fuelused, 0), COALESCE(t.calculatedfuel, 0),
                              t.status, COALESCE(t.purpose, '')
                       FROM trips t 
                       LEFT JOIN vehicles v ON t.vehicleid = v.id 
                       LEFT JOIN employees e ON t.employeeid = e.id"""
            
            if filtertext == "Aktywne": 
                query += " WHERE t.status = 'active'"
            elif filtertext == "Zakończone": 
                query += " WHERE t.status = 'completed'"
            elif filtertext == "Dzisiaj": 
                query += " WHERE date(t.startdate) = date('now')"
            
            query += " ORDER BY t.startdate DESC LIMIT 50"
            
            cursor.execute(query)
            trips = cursor.fetchall()
            print(f"📋 Znaleziono {len(trips)} przejazdów")
            
            self.table.setRowCount(len(trips))
            totaltrips = len(trips)
            activetrips = 0
            totaldistance = 0.0
            
            for rowidx, trip in enumerate(trips):
                for colidx, value in enumerate(trip):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    if colidx in [6, 7, 8]:  # dystans, paliwo, calc
                        try:
                            num = float(value or 0)
                            item.setText(f"{num:.1f}")
                            if colidx == 6: 
                                totaldistance += num
                        except: 
                            pass
                    
                    if colidx == 9 and 'active' in str(value).lower():
                        item.setBackground(QColor(255, 255, 0, 100))
                        activetrips += 1
                    elif colidx == 9 and 'completed' in str(value).lower():
                        item.setBackground(QColor(144, 238, 144, 100))
                    
                    self.table.setItem(rowidx, colidx, item)
            
            self.totallabel.setText(f"Łącznie: {totaltrips} przejazdów")
            self.activelabel.setText(f"Aktywne: {activetrips}")
            self.distancelabel.setText(f"Dystans: {totaldistance:.1f} km")
            
            print("✅ loaddata() zakończone pomyślnie!")
            
        except Exception as e:
            print(f"❌ BŁĄD w loaddata(): {e}")
        finally:
            conn.close()

    def addtrip(self):
        print("🚀 Rozpoczynanie przejazdu...")
        if self.vehiclecombo.currentIndex() == -1:
            QMessageBox.warning(self, "Błąd", "Wybierz pojazd!")
            return
        if self.drivercombo.currentIndex() == -1:
            QMessageBox.warning(self, "Błąd", "Wybierz kierowcę!")
            return

        conn = self.getconnection()
        if not conn: 
            QMessageBox.critical(self, "Błąd", "Brak połączenia z bazą!")
            return
        
        try:
            cursor = conn.cursor()
            vehicleid = self.vehiclecombo.currentData()
            driverid = self.drivercombo.currentData()
            
            # SPRAWDŹ CZY NIE MA AKTYWNEGO PRZEJAZDU
            cursor.execute("SELECT COUNT(*) FROM trips WHERE vehicleid=? AND status='active'", (vehicleid,))
            activetrips = cursor.fetchone()[0]
            if activetrips > 0:
                QMessageBox.warning(self, "Błąd", "Pojazd ma już aktywny przejazd!")
                return

            # DODAJ PRZEJAZD
            tripnumber = self.tripnumber.text().strip() or None
            cursor.execute("""INSERT INTO trips (tripnumber, vehicleid, employeeid, startdate, 
                                    startmileage, startfuel, purpose, orderedby, status, 
                                    vehicleok, notes, avgconsumption)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
                          (tripnumber, vehicleid, driverid,
                           self.startdate.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                           self.startmileage.value(), self.startfuel.value(),
                           self.purpose.text().strip(), self.orderedby.text().strip(),
                           1 if self.vehicleokcheck.isChecked() else 0,
                           self.notes.toPlainText().strip(),
                           self.vehicleconsumption))
            
            conn.commit()
            QMessageBox.information(self, "Sukces", "Przejazd rozpoczęty!")
            self.clearform()
            self.loaddata()
            print("✅ Przejazd dodany!")
            
        except Exception as e:
            print(f"❌ Błąd addtrip: {e}")
            QMessageBox.critical(self, "Błąd", f"Błąd zapisu: {e}")
        finally:
            conn.close()

    def endtrip(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Błąd", "Wybierz aktywny przejazd!")
            return
        
        row = selected[0].row()
        tripid = int(self.table.item(row, 0).text())
        
        currentmileage, ok = QInputDialog.getDouble(self, "Przebieg końcowy", 
            "Podaj przebieg końcowy [km]:", 0, 0, 1000000, 1)
        if not ok: return
        
        endfuel, ok = QInputDialog.getDouble(self, "Stan paliwa", 
            "Stan paliwa po trasie [L]:", 0, 0, 200, 1)
        if not ok: return
        
        conn = self.getconnection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT vehicleid, startmileage, startfuel FROM trips WHERE id=?", (tripid,))
            rowdata = cursor.fetchone()
            
            if rowdata:
                vehicleid, startmileage, startfuel = rowdata
                distance = max(0.0, currentmileage - (startmileage or 0))
                refuelliters = self.refuelliters.value() if self.refuelcheck.isChecked() else 0.0
                realfuelused = max(0.0, startfuel + refuelliters - endfuel)
                
                cursor.execute("""UPDATE trips SET enddate=?, endmileage=?, distance=?, endfuel=?, 
                                fuelused=?, status='completed' WHERE id=?""",
                              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), currentmileage, 
                               distance, endfuel, realfuelused, tripid))
                
                cursor.execute("UPDATE vehicles SET currentmileage=?, currentfuel=? WHERE id=?", 
                              (currentmileage, endfuel, vehicleid))
                
                conn.commit()
                QMessageBox.information(self, "Sukces", f"Przejazd zakończony!\nZużycie: {realfuelused:.1f} L\nBak: {endfuel:.1f} L")
                self.loaddata()
            
        finally:
            conn.close()

    def deletetrip(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Błąd", "Wybierz przejazd!")
            return
        
        row = selected[0].row()
        tripid = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Potwierdź", "Usunąć przejazd?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.getconnection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM trips WHERE id=?", (tripid,))
                    conn.commit()
                    self.loaddata()
                finally:
                    conn.close()

    def clearform(self):
        self.tripid.clear()
        self.tripnumber.clear()
        self.vehiclecombo.setCurrentIndex(-1)
        self.drivercombo.setCurrentIndex(-1)
        self.startdate.setDateTime(QDateTime.currentDateTime())
        self.enddate.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.startmileage.setValue(0)
        self.endmileage.setValue(0)
        self.startfuel.setValue(0)
        self.refuelcheck.setChecked(False)
        self.refuelliters.setValue(0)
        self.refuelcost.setValue(0)
        self.purpose.clear()
        self.orderedby.clear()
        self.notes.clear()
        self.vehicleokcheck.setChecked(True)
        self.calculatelive()

    def loadtriptoform(self, index):
        row = index.row()
        self.tripid.setText(self.table.item(row, 0).text())
        self.tripnumber.setText(self.table.item(row, 1).text())
        self.addbutton.setEnabled(False)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = TripWindow()
    window.setWindowTitle("Test - Przejazdy")
    window.resize(1500, 800)
    window.show()
    sys.exit(app.exec())
