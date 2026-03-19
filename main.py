import sys
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsObject
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class Engine(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Scene settings
        self.game_scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.game_scene)

        # Window settings
        self.setFixedSize(800, 600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)  # Teraz zadziała
        self.timer.start(16)

        self.keys = {}

        self.platforms = []
        floor = QGraphicsRectItem(0, 0, 800, 20)
        floor.setPos(0, 500)
        self.platforms.append(floor)

        # Platforma
        platform = QGraphicsRectItem(0, 0, 100, 20)
        platform.setPos(200, 400)
        self.platforms.append(platform)

        for p in self.platforms:
            p.setBrush(QColor("gray"))
            self.game_scene.addItem(p)

        self.player1 = Player(50, 450, "red", {
            'up': Qt.Key.Key_W, 'left': Qt.Key.Key_A, 'right': Qt.Key.Key_D
        })
        self.player2 = Player(100, 450, "blue", {
            'up': Qt.Key.Key_Up, 'left': Qt.Key.Key_Left, 'right': Qt.Key.Key_Right
        })

        # POPRAWKA: Używamy self.game_scene
        self.game_scene.addItem(self.player1)
        self.game_scene.addItem(self.player2)

    # --- TE METODY MUSZĄ BYĆ POZA __init__ ---

    def game_loop(self):
        self.player1.update_physics(self.keys, self.platforms)
        self.player2.update_physics(self.keys, self.platforms)

    def keyPressEvent(self, event):
        self.keys[event.key()] = True

    def keyReleaseEvent(self, event):
        self.keys[event.key()] = False


class Player(QGraphicsRectItem): # Zmiana na QGraphicsRectItem
    def __init__(self, x, y, color, controls):
        super().__init__()
        self.setRect(0, 0, 30, 50)
        self.setPos(x, y)
        self.setBrush(QColor(color))
        self.vx = 0
        self.vy = 0
        self.gravity = 0.8
        self.jump_speed = -15
        self.move_speed = 5
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
        # Ruch poziomy
        self.setX(self.x() + self.vx)
        self.check_collision(platforms, horizontal=True)

        # Ruch pionowy
        self.setY(self.y() + self.vy)
        self.on_ground = False
        self.check_collision(platforms, horizontal=False)

    def check_collision(self, platforms, horizontal):
        # Pobieramy dokładny prostokąt gracza na scenie
        p_rect = self.sceneBoundingRect()

        for platform in platforms:
            plat_rect = platform.sceneBoundingRect()

            # 1. Sprawdzamy, czy w ogóle nastąpiło przecięcie prostokątów (AABB)
            if p_rect.intersects(plat_rect):

                if horizontal:
                    # 2. HORIZONTAL: Dodajemy bufor tolerancji (np. 5px).
                    # Uznajemy kolizję za poziomą TYLKO jeśli dół gracza jest
                    # przynajmniej 5 pikseli NIŻEJ niż góra platformy.
                    # To zapobiega 'chwytaniu' kolizji poziomej gdy stoisz na podłodze.
                    is_colliding_sideways = (p_rect.bottom() > plat_rect.top() + 5)

                    if is_colliding_sideways:
                        if self.vx > 0:  # W prawo (uderzenie w ścianę z prawej)
                            # Cofamy do lewej krawędzi platformy
                            self.setX(plat_rect.left() - self.rect().width())
                        elif self.vx < 0:  # W lewo (uderzenie w ścianę z lewej)
                            # Przesuwamy do prawej krawędzi platformy
                            self.setX(plat_rect.right())
                else:
                    # 3. VERTICAL: Standardowa logika grawitacji
                    if self.vy > 0:  # Lądowanie (ruch w dół)
                        self.setY(plat_rect.top() - self.rect().height())
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:  # Uderzenie głową w sufit (ruch w górę)
                        self.setY(plat_rect.bottom())
                        self.vy = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = Engine()
    engine.show()
    sys.exit(app.exec())
