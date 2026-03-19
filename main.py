import sys
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PyQt6.QtCore import Qt, QTimer

class Engine(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Scene settings
        self.scene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.scene)
        # Window settings
        self.setFixedSize(800,600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


        # Game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16) # +/- 60FPS

        #keys state
        self.keys = {}

        def game_loop(self):

            self.update_physics()

        def update_physics(self):

            pass

        def KeyPressEvent(self, event):
            self.keys[event.key()] = True

        def KeyReleaseEvent(self, event):
            self.keys[event.key()] = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = Engine()
    engine.show()
    sys.exit(app.exec())


