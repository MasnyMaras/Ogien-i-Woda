import sys
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QFileDialog, QSpacerItem, QSizePolicy)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
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

        # title
        title = QLabel("OGIEŃ I WODA")
        title.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffaa00; margin-bottom: 30px;")
        layout.addWidget(title)

        # button 1 play
        self.btn_play = self.create_button("Graj")
        self.btn_play.clicked.connect(self.play_default_level)
        layout.addWidget(self.btn_play)

        # button 2 load
        self.btn_load = self.create_button("Wczytaj")
        self.btn_load.clicked.connect(self.load_custom_level)
        layout.addWidget(self.btn_load)

        # button 3 editor
        self.btn_editor = self.create_button("Wejdź do edytora")
        self.btn_editor.clicked.connect(self.launch_editor)
        layout.addWidget(self.btn_editor)

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

    def update_config_and_launch(self, map_path):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)

            config["plik_mapy"] = map_path

            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            self.launch_game()
        except Exception as e:
            print(f"Błąd podczas aktualizacji config.json: {e}")
            self.launch_game()

    def play_default_level(self):
        # Domyślna mapa dla przycisku Graj
        self.update_config_and_launch("mapa.txt")

    def load_custom_level(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik z mapą", "", "Pliki tekstowe (*.txt);;Wszystkie pliki (*)"
        )
        if file_path:
            self.update_config_and_launch(file_path)

    def launch_game(self):
        try:
            self.game_window = Engine(main_menu=self)
            self.game_window.show()
            self.hide()
        except Exception as e:
            print(f"error while loading: {e}")

    def launch_editor(self):
        try:
            self.editor_window = LevelEditor(main_menu=self)
            self.editor_window.show()
            self.hide()
        except Exception as e:
            print(f"error while loading {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())