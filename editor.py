import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QFileDialog, QTextEdit)
from PyQt6.QtGui import QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt


# Pomocnicza klasa płótna - przekazuje kliknięcia myszką do głównego okna
class MapCanvas(QGraphicsView):
    def __init__(self, parent_editor):
        super().__init__()
        self.editor = parent_editor

    def mousePressEvent(self, event):
        self.editor.handle_mouse(event, self)

    def mouseMoveEvent(self, event):
        self.editor.handle_mouse(event, self)

    def keyPressEvent(self, event):
        # Przekazujemy wciśnięcia klawiszy do głównego okna
        self.editor.keyPressEvent(event)


class LevelEditor(QWidget):
    def __init__(self, main_menu=None):
        super().__init__()
        self.main_menu = main_menu
        self.setWindowTitle("Ogień i Woda - Edytor Poziomów")

        self.cols = 40
        self.rows = 30
        self.tile_size = 20

        # --- GŁÓWNY UKŁAD (Lewa: Płótno, Prawa: Instrukcja) ---
        main_layout = QHBoxLayout(self)

        # 1. Płótno (Canvas)
        self.scene = QGraphicsScene(0, 0, 800, 600)
        self.scene.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.view = MapCanvas(self)
        self.view.setScene(self.scene)
        self.view.setFixedSize(802, 602)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(self.view)

        # 2. Panel Instrukcji
        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setFixedWidth(280)
        self.info_panel.setFont(QFont("Consolas", 10))
        # Ciemny motyw dla panelu bocznego
        self.info_panel.setStyleSheet("background-color: #2b2b2b; color: #ffffff; padding: 10px;")

        main_layout.addWidget(self.info_panel)

        # --- DANE EDYTORA ---
        self.map_data = [['.' for _ in range(self.cols)] for _ in range(self.rows)]
        self.rects = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_brush = 'X'

        self.colors = {
            'X': QColor("gray"),
            '-': QColor("lightgray"),
            'W': QColor("cyan"),
            'w': QColor("blue"),
            'L': QColor("orange"),
            'l': QColor("red"),
            'B': QColor("yellow"),
            'D': QColor("purple"),
            'C': QColor("darkgreen"),
            'O': QColor("saddlebrown"),
            '1': QColor("white"),
            '2': QColor("white")
        }

        self.draw_grid()
        self.update_instructions()  # Inicjalizacja tekstu instrukcji

    def update_instructions(self):
        # Ta funkcja odświeża tekst, żeby pokazywać aktualnie wybrany pędzel
        tekst = f"""=== EDYTOR POZIOMÓW ===
    
Aktywny pędzel: [ {self.current_brush} ]

--- STEROWANIE ---
LPM : Rysuj blok
PPM : Gumka (Usuń)
S   : Zapisz do pliku

--- WYBÓR BLOKÓW ---
X : Gruba ściana
- : Cienka kładka
W : Woda (Powierzchnia)
E : Woda (Głębia)
L : Lawa (Powierzchnia)
K : Lawa (Głębia)
B : Przycisk (Żółty)
D : Drzwi (Fioletowe)
C : Checkpoint (Zielony)
O : Skrzynka fizyczna
1 : Start Ogień (P1)
2 : Start Woda (P2)
"""
        self.info_panel.setText(tekst)

    def draw_grid(self):
        pen = QPen(QColor(50, 50, 50))
        for x in range(0, 800, self.tile_size):
            self.scene.addLine(x, 0, x, 600, pen)
        for y in range(0, 600, self.tile_size):
            self.scene.addLine(0, y, 800, y, pen)

    def handle_mouse(self, event, view_widget):
        pos = view_widget.mapToScene(event.pos())
        col = int(pos.x() // self.tile_size)
        row = int(pos.y() // self.tile_size)

        if 0 <= col < self.cols and 0 <= row < self.rows:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.place_tile(row, col, self.current_brush)
            elif event.buttons() & Qt.MouseButton.RightButton:
                self.place_tile(row, col, '.')

    def place_tile(self, row, col, char):
        self.map_data[row][col] = char
        if self.rects[row][col]:
            self.scene.removeItem(self.rects[row][col])
            self.rects[row][col] = None

        if char != '.':
            rect = QGraphicsRectItem(col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size)
            if char == '-':
                rect.setRect(col * self.tile_size, row * self.tile_size, self.tile_size, 10)
            elif char == 'B':
                rect.setRect(col * self.tile_size, row * self.tile_size + 15, self.tile_size, 5)

            rect.setBrush(QBrush(self.colors[char]))
            rect.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(rect)
            self.rects[row][col] = rect

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_X:
            self.current_brush = 'X'
        elif key == Qt.Key.Key_Minus:
            self.current_brush = '-'
        elif key == Qt.Key.Key_W:
            self.current_brush = 'W'
        elif key == Qt.Key.Key_E:
            self.current_brush = 'w'
        elif key == Qt.Key.Key_L:
            self.current_brush = 'L'
        elif key == Qt.Key.Key_K:
            self.current_brush = 'l'
        elif key == Qt.Key.Key_B:
            self.current_brush = 'B'
        elif key == Qt.Key.Key_D:
            self.current_brush = 'D'
        elif key == Qt.Key.Key_C:
            self.current_brush = 'C'
        elif key == Qt.Key.Key_O:
            self.current_brush = 'O'
        elif key == Qt.Key.Key_1:
            self.current_brush = '1'
        elif key == Qt.Key.Key_2:
            self.current_brush = '2'

        elif key == Qt.Key.Key_S:
            self.save_map()

        # Po każdym kliknięciu klawisza odświeżamy panel,
        # żeby pokazać użytkownikowi zmianę pędzla
        self.update_instructions()

    def save_map(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz poziom",
            "",
            "Pliki tekstowe (*.txt);;Wszystkie pliki (*)"
        )
        if file_path:
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            with open(file_path, "w") as file:
                for row in self.map_data:
                    file.write("".join(row) + "\n")
            print(f"Pomyślnie zapisano mapę jako: {file_path}")
        else:
            print("Zapisywanie anulowane.")

    def closeEvent(self, event):
        if self.main_menu:
            self.main_menu.show()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = LevelEditor()
    editor.show()
    sys.exit(app.exec())