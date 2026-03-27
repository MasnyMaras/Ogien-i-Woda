import sys
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsObject
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPen, QBrush
from PyQt6.QtWidgets import QGraphicsPixmapItem

class Engine(QGraphicsView):
    def __init__(self, level_file="level1.txt", main_menu=None):
        super().__init__()
        self.main_menu = main_menu

        # Scene settings
        self.game_scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.game_scene)

        bg_pixmap = QPixmap("background.jpg")
        bg_scaled = bg_pixmap.scaled(800, 600, Qt.AspectRatioMode.IgnoreAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
        self.game_scene.setBackgroundBrush(QBrush(bg_scaled))

        # Window settings
        self.setFixedSize(800, 600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.platforms = []
        self.liquids = []
        self.start_p1 = (50, 50)
        self.start_p2 = (100, 50)

        # Nowe zmienne dla checkpointów
        self.current_respawn_p1 = self.start_p1
        self.current_respawn_p2 = self.start_p2
        self.checkpoints = []

        # JEDYNE WYWOŁANIE LOAD LEVEL
        self.load_level(level_file)

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

        for box in self.boxes:
            box.update_physics(self.platforms)

        self.check_liquid_collisions()
        self.process_events()  # <--- TO OŻYWI DRZWI
        self.check_checkpoints()
        self.check_level_completion()

    def process_events(self):
        any_button_pressed = False
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        for btn in self.buttons:
            btn_rect = btn.sceneBoundingRect()

            # 1. Sprawdzamy graczy
            if p1_rect.intersects(btn_rect) or p2_rect.intersects(btn_rect):
                any_button_pressed = True
                break

            # 2. Sprawdzamy skrzynki
            for box in self.boxes:
                if box.sceneBoundingRect().intersects(btn_rect):
                    any_button_pressed = True
                    break

            if any_button_pressed:
                break

        for door in self.doors:
            if any_button_pressed:
                door.open_door()
            else:
                door.close_door()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
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
        self.player1.setPos(self.current_respawn_p1[0], self.current_respawn_p1[1])
        self.player1.vx = 0
        self.player1.vy = 0

        self.player2.setPos(self.current_respawn_p2[0], self.current_respawn_p2[1])
        self.player2.vx = 0
        self.player2.vy = 0

    def load_level(self, filepath):
        # Nowy, mniejszy rozmiar kafelka
        tile_size = 20

        self.platforms = []
        self.liquids = []
        self.doors = []
        self.buttons = []
        self.boxes = []
        self.checkpoints = []
        self.exits = []

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
                    # Pełny blok (ściany, gruba podłoga)
                    platform = QGraphicsRectItem(0, 0, tile_size, tile_size)
                    platform.setPos(x_pos, y_pos)
                    platform.setBrush(QColor("gray"))
                    platform.setPen(QPen(Qt.PenStyle.NoPen))
                    self.platforms.append(platform)
                    self.game_scene.addItem(platform)

                elif char == '-':
                    # CIENKA PLATFORMA (połowa wysokości, wyrównana do góry)
                    # Idealna do robienia pomostów nad lawą
                    platform = QGraphicsRectItem(0, 0, tile_size, int(tile_size / 2))
                    platform.setPos(x_pos, y_pos)
                    platform.setBrush(QColor("darkgray"))  # Inny kolor dla rozróżnienia
                    platform.setPen(QPen(Qt.PenStyle.NoPen))
                    self.platforms.append(platform)
                    self.game_scene.addItem(platform)


                elif char == 'W':

                    # Powierzchnia wody (z obniżeniem)

                    water = Liquid(x_pos, y_pos + 5, tile_size, tile_size - 5, "woda")

                    self.liquids.append(water)

                    self.game_scene.addItem(water)


                elif char == 'w':

                    # Głębia wody (pełny blok, wypełnia lukę)

                    water = Liquid(x_pos, y_pos, tile_size, tile_size, "woda")

                    self.liquids.append(water)

                    self.game_scene.addItem(water)


                elif char == 'L':

                    # Powierzchnia lawy (z obniżeniem)

                    lawa = Liquid(x_pos, y_pos + 5, tile_size, tile_size - 5, "lawa")

                    self.liquids.append(lawa)

                    self.game_scene.addItem(lawa)


                elif char == 'l':

                    # Głębia lawy (pełny blok)

                    lawa = Liquid(x_pos, y_pos, tile_size, tile_size, "lawa")

                    self.liquids.append(lawa)

                    self.game_scene.addItem(lawa)

                elif char == '1':
                    self.start_p1 = (x_pos, y_pos)

                elif char == '2':
                    self.start_p2 = (x_pos, y_pos)

                elif char == 'D':
                    # Drzwi traktujemy jako platformę, żeby blokowały ruch
                    door = Door(x_pos, y_pos, tile_size, tile_size)
                    self.platforms.append(door)  # Ważne: dodajemy do platform!
                    self.doors.append(door)  # Ważne: dodajemy też do listy drzwi
                    self.game_scene.addItem(door)

                elif char == 'B':
                    # Przycisk to tylko element wyzwalający, nie blokuje ruchu
                    btn = Button(x_pos, y_pos, tile_size)
                    self.buttons.append(btn)
                    self.game_scene.addItem(btn)


                elif char == 'O':
                    box = Box(x_pos, y_pos, tile_size)
                    self.platforms.append(box)
                    self.boxes.append(box)
                    self.game_scene.addItem(box)

                elif char == 'C':
                    # Dodajemy tylko do sceny i listy checkpointów, NIE do platform (nie blokuje ruchu)
                    cp = Checkpoint(x_pos, y_pos, tile_size, tile_size)
                    self.checkpoints.append(cp)
                    self.game_scene.addItem(cp)

                elif char == 'F':
                    portal = ExitPortal(x_pos, y_pos, tile_size, tile_size, "ogień")
                    self.exits.append(portal)
                    self.game_scene.addItem(portal)
                elif char == 'S':
                    portal = ExitPortal(x_pos, y_pos, tile_size, tile_size, "woda")
                    self.exits.append(portal)
                    self.game_scene.addItem(portal)
        self.current_respawn_p1 = self.start_p1
        self.current_respawn_p2 = self.start_p2

    def check_checkpoints(self):
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        for cp in self.checkpoints:
            if not cp.is_active:
                # Wystarczy, że jeden gracz dotknie punktu, aby zapisać postęp dla obu
                if p1_rect.intersects(cp.sceneBoundingRect()) or p2_rect.intersects(cp.sceneBoundingRect()):
                    cp.activate()
                    # Ustawiamy nowe miejsce odrodzenia.
                    # Gracz 2 jest przesunięty o 20 pikseli w prawo, żeby postacie nie zablokowały się w sobie.
                    self.current_respawn_p1 = (cp.x(), cp.y())
                    self.current_respawn_p2 = (cp.x() + 20, cp.y())

    def check_level_completion(self):
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        p1_at_exit = False
        p2_at_exit = False

        for portal in self.exits:
            portal_rect = portal.sceneBoundingRect()

            if portal.element == "ogień" and p1_rect.intersects(portal_rect):
                p1_at_exit = True

            elif portal.element == "woda" and p2_rect.intersects(portal_rect):
                p2_at_exit = True

        if p1_at_exit and p2_at_exit:
            self.level_complete()

    def level_complete(self):
        self.timer.stop()

        from PyQt6.QtWidgets import QGraphicsTextItem
        from PyQt6.QtGui import QFont

        win_text = QGraphicsTextItem("POZIOM UKOŃCZONY!")
        win_text.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        win_text.setDefaultTextColor(QColor("white"))

        text_rect = win_text.boundingRect()
        win_text.setPos((800 - text_rect.width()) / 2, (600 - text_rect.height()) / 2)

        self.game_scene.addItem(win_text)

    def closeEvent(self, event):
        # Kiedy zamykamy grę, pokazujemy z powrotem menu główne
        if self.main_menu:
            self.main_menu.show()
        super().closeEvent(event)

class Player(QGraphicsRectItem):
    def __init__(self, x, y, image_path, controls, element):
        super().__init__()

        # Nowe, mniejsze wymiary postaci
        player_width = 15
        player_height = 25

        # Ustawiamy nowy rozmiar hitboxa
        self.setRect(0, 0, player_width, player_height)
        self.setPos(x, y)
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.sprite = QGraphicsPixmapItem(self)
        pixmap = QPixmap(image_path)

        # Skalujemy grafikę do nowych wymiarów
        scaled_pixmap = pixmap.scaled(
            player_width, player_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.sprite.setPixmap(scaled_pixmap)

        self.element = element

        # Fizyka (przeczytaj notatkę poniżej!)
        self.vx = 0
        self.vy = 0
        self.gravity = 0.15
        self.jump_speed = -4.5
        self.move_speed = 2.4
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
        p_rect = self.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)

        for platform in platforms:
            if not platform.isVisible():
                continue

            plat_rect = platform.sceneBoundingRect()

            if p_rect.intersects(plat_rect):
                if horizontal:
                    # --- LOGIKA PCHANIA SKRZYNKI ---
                    if hasattr(platform, 'is_pushable') and platform.is_pushable:
                        original_box_x = platform.x()

                        # Próbujemy przesunąć skrzynkę o prędkość gracza
                        platform.setX(platform.x() + self.vx)

                        # Sprawdzamy, czy przesunięta skrzynka nie wbiła się w inną ścianę
                        box_collides = False
                        b_rect = platform.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)
                        for other_plat in platforms:
                            if other_plat is not platform and other_plat.isVisible():
                                if b_rect.intersects(other_plat.sceneBoundingRect()):
                                    box_collides = True
                                    break

                        # Jeśli skrzynka w coś uderzyła, cofamy ją i blokujemy gracza
                        if box_collides:
                            platform.setX(original_box_x)
                            if self.vx > 0:
                                self.setX(plat_rect.left() - self.rect().width())
                            elif self.vx < 0:
                                self.setX(plat_rect.right())

                    # --- ZWYKŁA ŚCIANA ---
                    else:
                        if self.vx > 0:
                            self.setX(plat_rect.left() - self.rect().width())
                        elif self.vx < 0:
                            self.setX(plat_rect.right())
                else:
                    # ... (tutaj zostawiasz stary kod od self.vy > 0 i self.vy < 0)
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

class Door(QGraphicsRectItem):
    def __init__(self, x, y, width, height):
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        self.setBrush(QColor("purple")) # Wyróżniający się kolor
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.is_open = False

    def open_door(self):
        if not self.is_open:
            self.hide() # Ukrywamy wizualnie
            self.is_open = True

    def close_door(self):
        if self.is_open:
            self.show() # Pokazujemy z powrotem
            self.is_open = False

class Button(QGraphicsRectItem):
    def __init__(self, x, y, width):
        # Przycisk ma tylko 5 pikseli wysokości
        super().__init__(0, 0, width, 5)
        # Przesuwamy go na dół kafelka (20 - 5 = 15)
        self.setPos(x, y + 15)
        self.setBrush(QColor("yellow"))
        self.setPen(QPen(Qt.PenStyle.NoPen))

class Box(QGraphicsRectItem):
    def __init__(self, x, y, size):
        super().__init__(0, 0, size, size)
        self.setPos(x, y)
        self.setBrush(QColor("saddlebrown"))  # Kolor brązowy
        self.setPen(QPen(Qt.PenStyle.NoPen))

        # Flaga informująca gracza, że ten obiekt można pchać
        self.is_pushable = True

        self.vy = 0
        self.gravity = 0.8

    def update_physics(self, platforms):
        self.vy += self.gravity
        self.setY(self.y() + self.vy)

        # Sprawdzanie kolizji z podłogą dla skrzynki
        b_rect = self.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)
        for platform in platforms:
            # Ignorujemy samą siebie i ukryte obiekty (np. otwarte drzwi)
            if platform is self or not platform.isVisible():
                continue

            if b_rect.intersects(platform.sceneBoundingRect()):
                if self.vy > 0:  # Skrzynka spada na podłogę
                    self.setY(platform.sceneBoundingRect().top() - self.rect().height())
                    self.vy = 0

class Checkpoint(QGraphicsRectItem):
    def __init__(self, x, y, width, height):
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        # Ciemnoczerwony przed aktywacją
        self.setBrush(QColor("darkred"))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.is_active = False

    def activate(self):
        if not self.is_active:
            self.is_active = True
            # Zmienia kolor na zielony po aktywacji, dając graczowi wizualny feedback
            self.setBrush(QColor("darkgreen"))

class ExitPortal(QGraphicsRectItem):
    def __init__(self, x, y, width, height, element):
        super().__init__()
        self.setRect(0, 0, width, height)
        self.setPos(x, y)
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.element = element

        # Wizualizacja wyjścia (możesz podpiąć QPixmap jak przy graczach)
        if element == "ogień":
            self.setBrush(QBrush(QColor(139, 0, 0)))  # Ciemnoczerwony
        elif element == "woda":
            self.setBrush(QBrush(QColor(0, 0, 139)))  # Ciemnoniebieski

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Engine()
    game.show()
    sys.exit(app.exec())
