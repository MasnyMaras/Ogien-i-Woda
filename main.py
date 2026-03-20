import sys
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsObject
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPen, QBrush
from PyQt6.QtWidgets import QGraphicsPixmapItem

class Engine(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Scene settings
        self.game_scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.game_scene)

        bg_pixmap = QPixmap("background.jpg")
        bg_scaled = bg_pixmap.scaled(800, 600, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.game_scene.setBackgroundBrush(QBrush(bg_scaled))
        # Window settings
        self.setFixedSize(800, 600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.platforms = []
        self.liquids = []
        self.start_p1 = (50, 50)  # Zostaną nadpisane, ale muszą tu być
        self.start_p2 = (100, 50)
        self.load_level("level1.txt")

        self.player1 = Player(self.start_p1[0], self.start_p1[1], "fire.png", {
            'up': Qt.Key.Key_W, 'left': Qt.Key.Key_A, 'right': Qt.Key.Key_D
        }, element="ogień")

        self.player2 = Player(self.start_p2[0], self.start_p2[1], "water.png", {
            'up': Qt.Key.Key_Up, 'left': Qt.Key.Key_Left, 'right': Qt.Key.Key_Right
        }, element="woda")

        self.game_scene.addItem(self.player1)
        self.game_scene.addItem(self.player2)

        # Game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)
        self.keys = {}

    def game_loop(self):
        self.player1.update_physics(self.keys, self.platforms)
        self.player2.update_physics(self.keys, self.platforms)
        self.check_liquid_collisions()

    def keyPressEvent(self, event):
        self.keys[event.key()] = True

    def keyReleaseEvent(self, event):
        self.keys[event.key()] = False

    def check_liquid_collisions(self):
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        needs_reset = False

        for liq in self.liquids:
            liq_rect = liq.sceneBoundingRect()

            # SPRAWDZANIE DLA GRACZA 1 (Ogień)
            if p1_rect.intersects(liq_rect):
                if liq.liquid_type == "woda":  # Ogień wchodzi do wody
                    needs_reset = True
                    break  # Wystarczy jeden gracz martwy, żeby zresetować poziom

            # SPRAWDZANIE DLA GRACZA 2 (Woda)
            if p2_rect.intersects(liq_rect):
                if liq.liquid_type == "lawa":  # Woda wchodzi do lawy
                    needs_reset = True
                    break

        # Jeśli ktoś zginął, resetujemy poziom
        if needs_reset:
            self.reset_level()

    def reset_level(self):
        # Proste przeniesienie na pozycje startowe
        self.player1.setPos(self.start_p1[0], self.start_p1[1])
        # Należy też wyzerować prędkości, żeby nie spadały po respie
        self.player1.vx = 0
        self.player1.vy = 0

        self.player2.setPos(self.start_p2[0], self.start_p2[1])
        self.player2.vx = 0
        self.player2.vy = 0

    def load_level(self, filepath):
        # Rozmiar pojedynczego bloku (zostawiamy 50)
        tile_size = 50

        # 1. Upewnij się, że lista jest pusta na początku wczytywania
        self.platforms = []
        self.liquids = []

        try:
            with open(filepath, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            print(f"BŁĄD: Nie znaleziono pliku mapy: {filepath}")
            return

        for row_idx, line in enumerate(lines):
            line = line.strip()
            for col_idx, char in enumerate(line):
                x_pos = col_idx * tile_size
                y_pos = row_idx * tile_size

                if char == 'X':
                    platform = QGraphicsRectItem(0, 0, tile_size, tile_size)
                    platform.setPos(x_pos, y_pos)
                    # Używamy gray, jak na twoim screenie (image_2.png)
                    platform.setBrush(QColor("gray"))
                    # Wyłączamy pióro (pen), żeby nie psuło obrysu kolizji
                    platform.setPen(QPen(Qt.PenStyle.NoPen))

                    # --- KLUCZOWA POPRAWKA: MUSISZ DODAĆ DO OBU ---
                    self.platforms.append(platform)  # Logika (pętla fizyki)
                    self.game_scene.addItem(platform)  # Wizualizacja (renderowanie)
                    # ---------------------------------------------

                elif char == 'W':
                    # Pamiętasz obniżenie? (y_pos + 20)
                    water = Liquid(x_pos, y_pos + 20, tile_size, tile_size - 20, "woda")
                    self.liquids.append(water)  # Logika (ciecze sprawdzamy w Engine)
                    self.game_scene.addItem(water)  # Wizualizacja

                elif char == 'L':
                    lawa = Liquid(x_pos, y_pos + 20, tile_size, tile_size - 20, "lawa")
                    self.liquids.append(lawa)
                    self.game_scene.addItem(lawa)

                elif char == '1':
                    self.start_p1 = (x_pos, y_pos)

                elif char == '2':
                    self.start_p2 = (x_pos, y_pos)

class Player(QGraphicsRectItem):
    def __init__(self, x, y, image_path, controls, element):
        super().__init__()
        self.setRect(0, 0, 30, 50)
        self.setPos(x, y)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.sprite = QGraphicsPixmapItem(self)
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(
            30, 50,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.element = element
        self.sprite.setPixmap(scaled_pixmap)
        self.vx = 0
        self.vy = 0
        self.gravity = 0.7
        self.jump_speed = -13
        self.move_speed = 3.5
        self.on_ground = False
        self.controls = controls

    def update_physics(self, keys, platforms):
        if keys.get(self.controls['left']):
            self.vx = -self.move_speed
        elif keys.get(self.controls['right']):
            self.vx = self.move_speed
        else:
            self.vx = 0

        self.vy += self.gravity

        if keys.get(self.controls['up']) and self.on_ground:
            self.vy = self.jump_speed
            self.on_ground = False

        self.apply_movement(platforms)

    def apply_movement(self, platforms):
        # 1. Ruch poziomy
        self.setX(self.x() + self.vx)
        self.check_collision(platforms, horizontal=True)

        # Ograniczenie ekranu w poziomie (0 do 800 minus szerokość gracza)
        if self.x() < 0:
            self.setX(0)
        elif self.x() > 800 - self.rect().width():
            self.setX(800 - self.rect().width())

        # 2. Ruch pionowy
        self.setY(self.y() + self.vy)
        self.on_ground = False
        self.check_collision(platforms, horizontal=False)

        # Ograniczenie ekranu w pionie (sufit i podłoga zapasowa)
        if self.y() < 0:
            self.setY(0)
            self.vy = 0  # Uderzenie w górną krawędź okna
        elif self.y() > 600 - self.rect().height():
            self.setY(600 - self.rect().height())
            self.vy = 0
            self.on_ground = True  # Zabezpieczenie, by podłoga ekranu też działała jak grunt

    def check_collision(self, platforms, horizontal):
        p_rect = self.sceneBoundingRect()

        for platform in platforms:
            plat_rect = platform.sceneBoundingRect()

            if p_rect.intersects(plat_rect):
                if horizontal:
                    # Dodany obustronny bufor tolerancji (5 pikseli).
                    # Kolizja boczna działa tylko, jeśli postać nie jest w trakcie minimalnego
                    # styku z podłogą (top platformy) ani z sufitem (bottom platformy).
                    is_colliding_sideways = (
                            p_rect.bottom() > plat_rect.top() + 5 and
                            p_rect.top() < plat_rect.bottom() - 5
                    )

                    if is_colliding_sideways:
                        if self.vx > 0:
                            self.setX(plat_rect.left() - self.rect().width())
                        elif self.vx < 0:
                            self.setX(plat_rect.right())
                else:
                    if self.vy > 0:
                        self.setY(plat_rect.top() - self.rect().height())
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:
                        self.setY(plat_rect.bottom())
                        self.vy = 0


class Liquid(QGraphicsRectItem):
    def __init__(self, x, y, width, height, liquid_type):
        super().__init__()
        # Definiujemy prostokąt od (0,0) i przesuwamy setPos (ważne dla kolizji!)
        self.setRect(0, 0, width, height)
        self.setPos(x, y)

        # Wyłączamy obramowanie
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.liquid_type = liquid_type

        # Ustawiamy kolory z przezroczystością (Alpha = 150/255)
        if liquid_type == "lawa":
            # Czerwono-pomarańczowy
            self.setBrush(QBrush(QColor(255, 69, 0, 150)))
        elif liquid_type == "woda":
            # Niebieski
            self.setBrush(QBrush(QColor(30, 144, 255, 150)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = Engine()
    engine.show()
    sys.exit(app.exec())
