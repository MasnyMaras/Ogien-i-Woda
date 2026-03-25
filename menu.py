import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QFileDialog, QSpacerItem, QSizePolicy)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

# Importujemy oba moduły!
from main import Engine
from editor import LevelEditor

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ogień i Woda")
        self.setFixedSize(400, 450)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tytuł
        title = QLabel("OGIEŃ I WODA")
        title.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffaa00; margin-bottom: 30px;")
        layout.addWidget(title)

        # Przycisk 1: Graj (domyślny poziom)
        self.btn_play = self.create_button("Graj")
        self.btn_play.clicked.connect(lambda: self.launch_game("level1.txt"))
        layout.addWidget(self.btn_play)

        # Przycisk 2: Wczytaj (własny poziom)
        self.btn_load = self.create_button("Wczytaj")
        self.btn_load.clicked.connect(self.load_custom_level)
        layout.addWidget(self.btn_load)

        # Przycisk 3: Edytor
        self.btn_editor = self.create_button("Wejdź do edytora")
        self.btn_editor.clicked.connect(self.launch_editor)
        layout.addWidget(self.btn_editor)

        # Wypełniacz dołu
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 15px;
                margin: 5px 20px;
            }
            QPushButton:hover {
                background-color: #555555;
                border: 2px solid #ffaa00;
            }
        """)
        return btn

    def load_custom_level(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik z mapą", "", "Pliki tekstowe (*.txt);;Wszystkie pliki (*)"
        )
        if file_path:
            self.launch_game(file_path)

    def launch_game(self, level_file):
        try:
            # Przekazujemy self (czyli to menu) do silnika gry
            self.game_window = Engine(level_file, main_menu=self)
            self.game_window.show()
            self.hide() # Ukrywamy menu
        except Exception as e:
            print(f"Błąd podczas ładowania poziomu: {e}")

    def launch_editor(self):
        try:
            # Przekazujemy self do edytora
            self.editor_window = LevelEditor(main_menu=self)
            self.editor_window.show()
            self.hide() # Ukrywamy menu
        except Exception as e:
            print(f"Błąd podczas ładowania edytora: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())