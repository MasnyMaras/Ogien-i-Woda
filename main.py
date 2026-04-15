import sys
import json
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsObject
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPen, QBrush
from PyQt6.QtWidgets import QGraphicsPixmapItem
import math


class Engine(QGraphicsView):
    def __init__(self, main_menu=None):
        super().__init__()
        self.main_menu = main_menu

        # load json config
        self.config = self.load_config()

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
        self.start_p1 = tuple(self.config.get("spawn_ogien", [50, 50]))
        self.start_p2 = tuple(self.config.get("spawn_woda", [100, 50]))

        # checkpoints
        self.current_respawn_p1 = self.start_p1
        self.current_respawn_p2 = self.start_p2
        self.checkpoints = []

        #AI wrogie
        self.enemies = []
        self.players_moved = False
        self.movement_timer = 0

        map_file = self.config.get("plik_mapy", "level1.txt")
        self.load_level(map_file)

        self.player1 = Player(self.start_p1[0], self.start_p1[1], "fire.png", {
            'up': Qt.Key.Key_W, 'left': Qt.Key.Key_A, 'right': Qt.Key.Key_D
        }, "ogień", self.config)

        self.player2 = Player(self.start_p2[0], self.start_p2[1], "water.png", {
            'up': Qt.Key.Key_Up, 'left': Qt.Key.Key_Left, 'right': Qt.Key.Key_Right
        }, "woda", self.config)

        self.game_scene.addItem(self.player1)
        self.game_scene.addItem(self.player2)

        # Game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)
        self.keys = {}


    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("BŁĄD: Nie znaleziono config.json. Użyto domyślnych wartości.")
            return {
                "plik_mapy": "level1.txt",
                "grawitacja_gracza": 0.15,
                "predkosc_skoku": -4.5,
                "predkosc_ruchu": 2.4,
                "grawitacja_skrzyni": 0.8
            }

    def game_loop(self):
        self.player1.update_physics(self.keys, self.platforms)
        self.player2.update_physics(self.keys, self.platforms)

        for box in self.boxes:
            box.update_physics(self.platforms)

        #logika AI
        if self.players_moved:
            self.movement_timer += 1
        is_ai_active = self.movement_timer >= 60

        for enemy in self.enemies:
            enemy.update_ai(self.player1, self.player2, self.platforms, is_ai_active)

            #śmierć gracza przy kontakcie z wrogiem
            if enemy.sceneBoundingRect().intersects(self.player1.sceneBoundingRect()) or enemy.sceneBoundingRect().intersects(self.player2.sceneBoundingRect()):
                self.reset_level()
                break

        self.check_liquid_collisions()
        self.process_events()
        self.check_checkpoints()
        self.check_level_completion()

    def process_events(self):
        any_button_pressed = False
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        for btn in self.buttons:
            btn_rect = btn.sceneBoundingRect()

            # check players
            if p1_rect.intersects(btn_rect) or p2_rect.intersects(btn_rect):
                any_button_pressed = True
                break

            # check boxes
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
        elif event.key() == Qt.Key.Key_R:
            self.hot_reload()
        self.keys[event.key()] = True
        #Detekcja początku ruchu
        if event.key() in [Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_D, Qt.Key.Key_Up, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            self.players_moved = True

        self.keys[event.key()] = True

    def hot_reload(self):
        old_start_p1 = self.start_p1

        self.config = self.load_config()
        p_gravity = self.config.get("grawitacja_gracza", 0.15)
        p_jump = self.config.get("predkosc_skoku", -4.5)
        p_speed = self.config.get("predkosc_ruchu", 2.4)

        self.player1.gravity = p_gravity
        self.player1.jump_speed = p_jump
        self.player1.move_speed = p_speed
        self.player2.gravity = p_gravity
        self.player2.jump_speed = p_jump
        self.player2.move_speed = p_speed

        for box in self.boxes:
            box.gravity = self.config.get("grawitacja_skrzyni", 0.8)


        new_start_p1 = tuple(self.config.get("spawn_ogien", [50, 50]))
        new_start_p2 = tuple(self.config.get("spawn_woda", [100, 50]))

        self.start_p1 = new_start_p1
        self.start_p2 = new_start_p2

        if self.current_respawn_p1 == old_start_p1:
            self.current_respawn_p1 = self.start_p1
            self.current_respawn_p2 = self.start_p2
            print("checkpoint not reached")
        else:
            print("Checkpoint reached")

        self.reset_level()

    def keyReleaseEvent(self, event):
        self.keys[event.key()] = False

    def check_liquid_collisions(self):
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        needs_reset = False

        for liq in self.liquids:
            liq_rect = liq.sceneBoundingRect()

            # check p1 fire
            if p1_rect.intersects(liq_rect):
                if liq.liquid_type == "woda":  # fire enters water
                    needs_reset = True
                    break

            # check p2 water
            if p2_rect.intersects(liq_rect):
                if liq.liquid_type == "lawa":  # water enters lava
                    needs_reset = True
                    break

        # if anyone dies - reset
        if needs_reset:
            self.reset_level()

    def reset_level(self):
        self.player1.setPos(self.current_respawn_p1[0], self.current_respawn_p1[1])
        self.player1.vx = 0
        self.player1.vy = 0

        self.player2.setPos(self.current_respawn_p2[0], self.current_respawn_p2[1])
        self.player2.vx = 0
        self.player2.vy = 0

        self.players_moved = False
        self.movement_timer = 0
        for enemy in self.enemies:
            enemy.reset_pos()

    def load_level(self, filepath):
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
                    platform = QGraphicsRectItem(0, 0, tile_size, tile_size)
                    platform.setPos(x_pos, y_pos)
                    platform.setBrush(QColor("darkgray"))
                    platform.setPen(QPen(Qt.PenStyle.NoPen))
                    self.platforms.append(platform)
                    self.game_scene.addItem(platform)

                elif char == '-':

                    platform = QGraphicsRectItem(0, 0, tile_size, int(tile_size / 2))
                    platform.setPos(x_pos, y_pos)
                    platform.setBrush(QColor("darkgray"))
                    platform.setPen(QPen(Qt.PenStyle.NoPen))
                    self.platforms.append(platform)
                    self.game_scene.addItem(platform)


                elif char == 'W':
                    water = Liquid(x_pos, y_pos + 5, tile_size, tile_size - 5, "woda")
                    self.liquids.append(water)
                    self.game_scene.addItem(water)


                elif char == 'w':
                    water = Liquid(x_pos, y_pos, tile_size, tile_size, "woda")
                    self.liquids.append(water)
                    self.game_scene.addItem(water)


                elif char == 'L':
                    lawa = Liquid(x_pos, y_pos + 5, tile_size, tile_size - 5, "lawa")
                    self.liquids.append(lawa)
                    self.game_scene.addItem(lawa)

                elif char == 'l':
                    lawa = Liquid(x_pos, y_pos, tile_size, tile_size, "lawa")
                    self.liquids.append(lawa)
                    self.game_scene.addItem(lawa)

                #elif char == '1':
                    #self.start_p1 = (x_pos, y_pos)

                #elif char == '2':
                    #self.start_p2 = (x_pos, y_pos)

                elif char == 'D':
                    door = Door(x_pos, y_pos, tile_size, tile_size)
                    self.platforms.append(door)
                    self.doors.append(door)
                    self.game_scene.addItem(door)

                elif char == 'B':
                    btn = Button(x_pos, y_pos, tile_size)
                    self.buttons.append(btn)
                    self.game_scene.addItem(btn)


                elif char == 'O':
                    # Przekazanie konfiguracji do skrzyni
                    box = Box(x_pos, y_pos, tile_size, self.config)
                    self.platforms.append(box)
                    self.boxes.append(box)
                    self.game_scene.addItem(box)

                elif char == 'C':
                    cp = Checkpoint(x_pos, y_pos, tile_size, tile_size)
                    self.checkpoints.append(cp)
                    self.game_scene.addItem(cp)

                elif char == '3':
                    portal = ExitPortal(x_pos, y_pos, tile_size, tile_size, "ogień")
                    self.exits.append(portal)
                    self.game_scene.addItem(portal)
                elif char == '4':
                    portal = ExitPortal(x_pos, y_pos, tile_size, tile_size, "woda")
                    self.exits.append(portal)
                    self.game_scene.addItem(portal)
                elif char == 'A':
                    enemy = EnemyAI(x_pos, y_pos, self.config)
                    self.enemies.append(enemy)
                    self.game_scene.addItem(enemy)

        self.current_respawn_p1 = self.start_p1
        self.current_respawn_p2 = self.start_p2

    def check_checkpoints(self):
        p1_rect = self.player1.sceneBoundingRect()
        p2_rect = self.player2.sceneBoundingRect()

        for cp in self.checkpoints:
            if not cp.is_active:
                if p1_rect.intersects(cp.sceneBoundingRect()) or p2_rect.intersects(cp.sceneBoundingRect()):
                    cp.activate()
                    # new respawn
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
        if self.main_menu:
            self.main_menu.show()
        super().closeEvent(event)


class Player(QGraphicsRectItem):
    def __init__(self, x, y, image_path, controls, element, config):
        super().__init__()

        player_width = 15
        player_height = 25

        self.setRect(0, 0, player_width, player_height)
        self.setPos(x, y)
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.sprite = QGraphicsPixmapItem(self)
        pixmap = QPixmap(image_path)

        scaled_pixmap = pixmap.scaled(
            player_width, player_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.sprite.setPixmap(scaled_pixmap)

        self.element = element
        self.controls = controls

        self.vx = 0
        self.vy = 0
        self.on_ground = False

        # Pobieranie wartości z konfiguracji (lub ustawianie domyślnych, jeśli brakuje wpisu)
        self.gravity = config.get("grawitacja_gracza", 0.15)
        self.jump_speed = config.get("predkosc_skoku", -4.5)
        self.move_speed = config.get("predkosc_ruchu", 2.4)

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
        self.setX(self.x() + self.vx)
        self.check_collision(platforms, horizontal=True)

        if self.x() < 0:
            self.setX(0)
        elif self.x() > 800 - self.rect().width():
            self.setX(800 - self.rect().width())

        self.setY(self.y() + self.vy)
        self.on_ground = False
        self.check_collision(platforms, horizontal=False)

        if self.y() < 0:
            self.setY(0)
            self.vy = 0
        elif self.y() > 600 - self.rect().height():
            self.setY(600 - self.rect().height())
            self.vy = 0
            self.on_ground = True

    def check_collision(self, platforms, horizontal):
        p_rect = self.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)

        for platform in platforms:
            if not platform.isVisible():
                continue

            plat_rect = platform.sceneBoundingRect()

            if p_rect.intersects(plat_rect):
                if horizontal:
                    if hasattr(platform, 'is_pushable') and platform.is_pushable:
                        original_box_x = platform.x()

                        platform.setX(platform.x() + self.vx)

                        box_collides = False
                        b_rect = platform.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)
                        for other_plat in platforms:
                            if other_plat is not platform and other_plat.isVisible():
                                if b_rect.intersects(other_plat.sceneBoundingRect()):
                                    box_collides = True
                                    break

                        if box_collides:
                            platform.setX(original_box_x)
                            if self.vx > 0:
                                self.setX(plat_rect.left() - self.rect().width())
                            elif self.vx < 0:
                                self.setX(plat_rect.right())

                    else:
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
        self.setRect(0, 0, width, height)
        self.setPos(x, y)

        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.liquid_type = liquid_type

        if liquid_type == "lawa":
            self.setBrush(QBrush(QColor("orange")))
        elif liquid_type == "woda":
            self.setBrush(QBrush(QColor("blue")))


class Door(QGraphicsRectItem):
    def __init__(self, x, y, width, height):
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        self.setBrush(QColor("purple"))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.is_open = False

    def open_door(self):
        if not self.is_open:
            self.hide()
            self.is_open = True

    def close_door(self):
        if self.is_open:
            self.show()
            self.is_open = False


class Button(QGraphicsRectItem):
    def __init__(self, x, y, width):
        super().__init__(0, 0, width, 5)
        self.setPos(x, y + 15)
        self.setBrush(QColor("yellow"))
        self.setPen(QPen(Qt.PenStyle.NoPen))


class Box(QGraphicsRectItem):
    def __init__(self, x, y, size, config):
        super().__init__(0, 0, size, size)
        self.setPos(x, y)
        self.setBrush(QColor("saddlebrown"))
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.is_pushable = True

        self.vy = 0
        # Pobieranie grawitacji z konfiguracji
        self.gravity = config.get("grawitacja_skrzyni", 0.8)

    def update_physics(self, platforms):
        self.vy += self.gravity
        self.setY(self.y() + self.vy)

        b_rect = self.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)
        for platform in platforms:
            if platform is self or not platform.isVisible():
                continue

            if b_rect.intersects(platform.sceneBoundingRect()):
                if self.vy > 0:
                    self.setY(platform.sceneBoundingRect().top() - self.rect().height())
                    self.vy = 0


class Checkpoint(QGraphicsRectItem):
    def __init__(self, x, y, width, height):
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        self.setBrush(QColor("darkred"))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.is_active = False

    def activate(self):
        if not self.is_active:
            self.is_active = True
            self.setBrush(QColor("darkgreen"))


class ExitPortal(QGraphicsRectItem):
    def __init__(self, x, y, width, height, element):
        super().__init__()
        self.setRect(0, 0, width, height)
        self.setPos(x, y)
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.element = element

        if element == "ogień":
            self.setBrush(QBrush(QColor(139, 0, 0)))
        elif element == "woda":
            self.setBrush(QBrush(QColor(0, 0, 139)))


class EnemyAI(QGraphicsRectItem):
    def __init__(self, x, y, config):
        super().__init__(0, 0, 15, 25)
        self.start_x = x
        self.start_y = y
        self.setPos(x, y)
        self.setBrush(QColor("magenta"))
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self.vx = 0
        self.vy = 0
        self.speed = 1.5
        self.gravity = config.get("grawitacja_gracza", 0.16)
        self.state = "IDLE"

    def reset_pos(self):
        self.setPos(self.start_x, self.start_y)
        self.vx = 0
        self.vy = 0
        self.state = "IDLE"

    def update_ai(self, p1, p2, platforms, is_active):
        self.vy += self.gravity

        if is_active:
            dist_fire = math.hypot(self.x() - p1.x(), self.y() - p1.y())
            dist_water = math.hypot(self.x() - p2.x(), self.y() - p2.y())

            # Mechanizm decyzyjny (Drabina priorytetów)
            if dist_water < 180:
                # Najwyzszy priorytet: Ucieczka przed woda
                self.state = "FLEE"
                if p2.x() < self.x():
                    self.vx = self.speed  # Uciekaj w prawo
                else:
                    self.vx = -self.speed  # Uciekaj w lewo
            elif dist_fire < 250:
                # Nizszy priorytet: Gonienie ognia
                self.state = "CHASE"
                if p1.x() < self.x():
                    self.vx = -self.speed  # Gon w lewo
                else:
                    self.vx = self.speed  # Gon w prawo
            else:
                self.state = "PATROL"
                # Jesli nikogo nie ma, idzie przed siebie
                if self.vx == 0:
                    self.vx = self.speed

        else:
            # Agent spi (dziala tylko grawitacja)
            self.vx = 0

        self.apply_movement(platforms)

    def apply_movement(self, platforms):
        # Oś X
        self.setX(self.x() + self.vx)
        self.check_collision(platforms, horizontal=True)

        # Blokada granic ekranu (Oś X)
        if self.x() < 0:
            self.setX(0)
            self.vx *= -1  # Odbicie od lewej krawędzi
        elif self.x() > 800 - self.rect().width():
            self.setX(800 - self.rect().width())
            self.vx *= -1  # Odbicie od prawej krawędzi

        # Oś Y
        self.setY(self.y() + self.vy)
        self.check_collision(platforms, horizontal=False)

        # Blokada granic ekranu (Oś Y - podłoga i sufit)
        if self.y() < 0:
            self.setY(0)
            self.vy = 0
        elif self.y() > 600 - self.rect().height():
            self.setY(600 - self.rect().height())
            self.vy = 0
            # Można tu zresetować stan skoku, jeśli dodasz go w przyszłości

    def check_collision(self, platforms, horizontal):
        p_rect = self.sceneBoundingRect().adjusted(0.1, 0.1, -0.1, -0.1)

        for platform in platforms:
            if not platform.isVisible():
                continue

            if p_rect.intersects(platform.sceneBoundingRect()):
                if horizontal:
                    if self.vx > 0:
                        self.setX(platform.sceneBoundingRect().left() - self.rect().width())
                    elif self.vx < 0:
                        self.setX(platform.sceneBoundingRect().right())

                    self.vx *= -1

                    break
                else:
                    if self.vy > 0:
                        self.setY(platform.sceneBoundingRect().top() - self.rect().height())
                        self.vy = 0
                    elif self.vy < 0:
                        self.setY(platform.sceneBoundingRect().bottom())
                        self.vy = 0
                    break

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Engine()
    game.show()
    sys.exit(app.exec())
