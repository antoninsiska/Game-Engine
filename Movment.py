import sys, math, time, random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QBrush

VFOV_DEG = 70  # vertikální FOV (60–80 je fajn)

# ----- Procedurální svět (chunky) -----
CHUNK_SIZE = 20         # velikost chunku v jednotkách světa (X/Z)
POINTS_PER_CHUNK = 18   # kolik "bodů-objektů" do jednoho chunku
WORLD_SEED = 1337       # master seed, ať je svět deterministický
LOAD_RADIUS = 60        # jak daleko (v jednotkách) generovat body kolem hráče

class ChunkWorld:
    """
    Jednoduchý procedurální svět: pro každý chunk (cx, cz) deterministicky vygeneruje body.
    Body mají tvar (x, y, z); tady y ~ výška, držíme +-1 pro variaci.
    """
    def __init__(self, seed: int = WORLD_SEED):
        self.seed = seed
        self.chunks: dict[tuple[int, int], list[tuple[float, float, float]]] = {}

    def _chunk_seed(self, cx: int, cz: int) -> int:
        # stabilní kombinace koordinát a master seeda
        return (cx * 73856093) ^ (cz * 19349663) ^ self.seed

    def generate_chunk(self, cx: int, cz: int):
        key = (cx, cz)
        if key in self.chunks:
            return
        rng = random.Random(self._chunk_seed(cx, cz))
        pts = []
        for _ in range(POINTS_PER_CHUNK):
            # pozice v rámci chunku (0..CHUNK_SIZE) posuneme do světových souřadnic
            lx = rng.uniform(0.5, CHUNK_SIZE - 0.5)
            lz = rng.uniform(0.5, CHUNK_SIZE - 0.5)
            x = cx * CHUNK_SIZE + lx
            z = cz * CHUNK_SIZE + lz
            # mírná výška pro variaci
            y = rng.uniform(-1.0, 1.5)
            pts.append((x, y, z))
        self.chunks[key] = pts

    def ensure_chunks_around(self, x: float, z: float, radius: float):
        min_cx = int(math.floor((x - radius) / CHUNK_SIZE))
        max_cx = int(math.floor((x + radius) / CHUNK_SIZE))
        min_cz = int(math.floor((z - radius) / CHUNK_SIZE))
        max_cz = int(math.floor((z + radius) / CHUNK_SIZE))
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                self.generate_chunk(cx, cz)

    def points_near(self, x: float, z: float, radius: float) -> list[tuple[float, float, float]]:
        self.ensure_chunks_around(x, z, radius)
        r2 = radius * radius
        pts = []
        for (cx, cz), chunk_pts in self.chunks.items():
            for (px, py, pz) in chunk_pts:
                dx = px - x
                dz = pz - z
                if dx*dx + dz*dz <= r2:
                    pts.append((px, py, pz))
        return pts


class FPSDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPS demo (procedurální minimapa, dt, fps, WASD)")
        self.resize(1280, 720)
        self.setMouseTracking(True)
        self.grabMouse()
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # kamera: pozice a úhly
        self.cam = [0.0, 0.0, 0.0]  # x, y, z
        self.yaw = 0.0
        self.pitch = 0.0

        # procedurální svět
        self.world = ChunkWorld(seed=WORLD_SEED)
        self.near = 0.1

        # vstup a pohyb
        self.keys_down = set()
        self.mouse_sens = 0.0022
        self.move_speed = 5.0  # jednotek/s
        self.v = []
        self.fwd = []
        self.right = []
        self.up = []
        self.paused = False

        # minimapa
        self.minimap_size = 220                # px (čtverec)
        self.minimap_radius = 60               # rozsah v jednotkách světa, který minimapa zobrazuje
        self.minimap_rotate_with_cam = True    # M přepíná režim

        # kurzor – globální střed
        self.center_global = self.mapToGlobal(self.rect().center())

        # timing
        self.last_time = time.perf_counter()
        self.fps = 0.0
        self._fps_accum = 0.0
        self._fps_frames = 0

        # loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)  # co to dá

    # ---------- pomocné výpočty ----------
    def size_params(self):
        w = self.width()
        h = self.height()
        aspect = w / h
        vfov = math.radians(VFOV_DEG)
        fy = (h / 2) / math.tan(vfov / 2)
        fx = fy * aspect
        cx, cy = w // 2, h // 2
        return w, h, fx, fy, cx, cy

    def update_center_global(self):
        self.center_global = self.mapToGlobal(self.rect().center())

    def recenter_mouse(self):
        QCursor.setPos(self.center_global)

    # ---------- lifecycle ----------
    def showEvent(self, e):
        super().showEvent(e)
        self.update_center_global()
        self.recenter_mouse()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update_center_global()

    # ---------- vstup ----------
    def keyPressEvent(self, e):
        self.keys_down.add(e.key())
        if e.key() == Qt.Key.Key_Right:  self.yaw += 0.03
        elif e.key() == Qt.Key.Key_Left: self.yaw -= 0.03
        elif e.key() == Qt.Key.Key_M:    self.minimap_rotate_with_cam = not self.minimap_rotate_with_cam
        elif e.key() == Qt.Key.Key_Escape:
            self.releaseMouse()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        e.accept()

    def keyReleaseEvent(self, e):
        self.keys_down.discard(e.key())
        e.accept()

    def mouseMoveEvent(self, e):
        if self.paused:
            return
        gp = e.globalPosition()
        dx = gp.x() - self.center_global.x()
        dy = gp.y() - self.center_global.y()

        self.yaw   += dx * self.mouse_sens
        self.pitch += dy * self.mouse_sens

        limit = math.radians(89.0)
        self.pitch = max(-limit, min(limit, self.pitch))

        self.recenter_mouse()

    # ---------- update ----------
    def tick(self):
        if self.paused:
            self.update()
        # delta time
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now

        # FPS průměr každých ~0.25 s
        self._fps_accum += dt
        self._fps_frames += 1
        if self._fps_accum >= 0.25:
            self.fps = self._fps_frames / self._fps_accum
            self._fps_accum = 0.0
            self._fps_frames = 0

        # pohyb kamery
        self.update_camera(dt)

        # před překreslením si zajisti body v okolí (procedurální generace)
        cx, cy, cz = self.cam
        self.near_points = self.world.points_near(cx, cz, LOAD_RADIUS)

        # překresli
        self.update()

    def update_camera(self, dt):
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)

        # forward/right/up
        fwd = [sy * cp, sp, cy * cp]
        right = [cy, 0.0, -sy]
        up = [0.0, 1.0, 0.0]
            # X    Y    Z
        v = [0.0, 0.0, 0.0]
        k = self.keys_down
        if Qt.Key.Key_W in k: v = [v[i] + fwd[i] for i in range(3)]
        if Qt.Key.Key_S in k: v = [v[i] - fwd[i] for i in range(3)]
        if Qt.Key.Key_D in k: v = [v[i] + right[i] for i in range(3)]
        if Qt.Key.Key_A in k: v = [v[i] - right[i] for i in range(3)]
        if Qt.Key.Key_Space in k: 
            v = [v[i] + up[i] for i in range(3)]
        if Qt.Key.Key_Control in k or Qt.Key.Key_C in k: v = [v[i] - up[i] for i in range(3)]
        if Qt.Key.Key_B in k: 
            self.cam[0] = 0
            self.cam[1] = 0
            self.cam[2] = 0
            self.yaw = 0
            self.pitch = 0
        if Qt.Key.Key_Escape in k:
            print("pause")
            self.toggle_pause()
        self.checkBorders()
        self.v = v
        self.up = up
        self.fwd = fwd
        self.right = right
        # normalizace, sprint
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if mag > 1e-6:
            v = [vi / mag for vi in v]
            spd = self.move_speed * (2.0 if Qt.Key.Key_Shift in k else 1.0)
            self.cam = [self.cam[i] + v[i] * spd * dt for i in range(3)]

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            # zapnout pauzu
            self.keys_down.clear()
            self.releaseMouse()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            # vypnout pauzu
            self.grabMouse()
            self.setCursor(Qt.CursorShape.BlankCursor)
            self.update_center_global()
            self.recenter_mouse()
            self.last_time = time.perf_counter()  # reset dt, at neskoci
        self.update()  # prekresli HUD (napr. "PAUSED")

    # ---------- render ----------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(0, 0, 0))

        w, h, fx, fy, _, _ = self.size_params()

        # pera/štětec
        p.setPen(QPen(QColor(255, 80, 80)))

        # předpočty rotace kamery (aplikujeme na svět – opačné otáčení)
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)

        cx, cy, cz = self.cam

        # --- 3D body (z procedurálních chunků v okolí) ---
        for (x, y, z) in getattr(self, "near_points", []):
            # do prostoru kamery: posun o -cam
            x -= cx; y -= cy; z -= cz

            # yaw (kolem Y)
            xz = x * cos_y - z * sin_y
            zz = x * sin_y + z * cos_y
            # pitch (kolem X)
            yz = y * cos_p - zz * sin_p
            zz = y * sin_p + zz * cos_p

            if zz <= self.near:
                continue  # za kamerou/za near plane

            # perspektivní projekce
            sx = int(w / 2 + (xz / zz) * fx)
            sy = int(h / 2 - (yz / zz) * fy)

            size = max(2, int(200 / zz))
            p.drawEllipse(QPoint(sx, sy), size, size)

        if self.paused:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawRect(self.rect())
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Menlo", 28))
            p.drawText(20, 95, "PAUSED  (P to resume)")

        # HUD text
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Menlo", 14))
        yaw_deg = (math.degrees(self.yaw) % 360.0)
        pitch_deg = math.degrees(self.pitch)
        hud1 = f"Yaw: {yaw_deg:6.1f}°   Pitch: {pitch_deg:6.1f}°   FPS: {self.fps:5.1f}"
        hud2 = f"Cam: x={self.cam[0]:.2f}  y={self.cam[1]:.2f}  z={self.cam[2]:.2f}  vectors={self.v} fwd={self.fwd} up={self.up} right={self.right}   [M] Map rotate: {'ON' if self.minimap_rotate_with_cam else 'OFF'}"
        p.drawText(20, 30, hud1)
        p.drawText(20, 55, hud2)

        # --- Minimap ---
        self.draw_minimap(p)

    # ---------- minimapa ----------
    def draw_minimap(self, p: QPainter):
        size = self.minimap_size
        margin = 16
        rect = QRect(self.width() - size - margin, margin, size, size)

        # panel pozadí
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 20, 25, 200))
        p.drawRoundedRect(rect, 12, 12)

        # okraj
        p.setPen(QPen(QColor(90, 90, 110), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)

        # transformace do místního souřadného systému minimapy
        p.setClipRect(rect.adjusted(4, 4, -4, -4))
        cx = rect.center().x()
        cy = rect.center().y()

        # svět → map: zvolíme scale tak, aby radius vyplnil ~90% napříč
        # mapRadius (px) ~ (size - padding)/2
        map_px_radius = (size - 20) * 0.5
        units_per_px = self.minimap_radius / map_px_radius
        scale = 1.0 / units_per_px

        # grid (volitelně po 10 jednotkách)
        p.setPen(QPen(QColor(60, 60, 80, 160), 1))
        grid_step_units = 10
        # vykreslíme jen pár kruhových kroužků pro orientaci
        for r_units in (10, 20, 30, 40, 50, 60):
            r_px = r_units * scale
            p.drawEllipse(QPoint(cx, cy), int(r_px), int(r_px))

        # rotace: buď se točí s kamerou, nebo “north-up”
        p.translate(cx, cy)
        if self.minimap_rotate_with_cam:
            p.rotate(-math.degrees(self.yaw))  # ať "dopředu" je nahoru

        # body – top-down projekce z near_points (X,Z)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 120, 120))
        camx, camy, camz = self.cam

        for (x, y, z) in getattr(self, "near_points", []):
            dx = x - camx
            dz = z - camz
            # jen co se vejde na mapu
            if abs(dx) > self.minimap_radius or abs(dz) > self.minimap_radius:
                continue
            mx = dx * scale
            mz = dz * scale
            p.drawEllipse(QPoint(int(mx), int(mz)), 3, 3)

        # FOV kužel
        p.setBrush(QColor(100, 180, 255, 120))
        p.setPen(Qt.PenStyle.NoPen)
        fwd_len = 30 * scale  # vizuální délka kužele
        half_fov = math.radians(60)  # šířka kužele na minimapě, nezávisle na VFOV
        # trojúhelník
        a = QPoint(0, 0)
        b = QPoint(int(math.sin(+half_fov) * fwd_len), int(-math.cos(+half_fov) * fwd_len))
        c = QPoint(int(math.sin(-half_fov) * fwd_len), int(-math.cos(-half_fov) * fwd_len))
        p.drawPolygon(a, b, c)

        # hráč (šipka)
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.setBrush(QBrush(QColor(0, 0, 0)))
        p.drawEllipse(QPoint(0, 0), 5, 5)
        p.drawLine(0, 0, 0, -14)

        p.restore()
    
    def checkBorders(self):
        if self.cam[1] != 0:
            self.cam[1] = 0
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FPSDemo()
    w.show()
    w.update_center_global()
    w.recenter_mouse()
    sys.exit(app.exec())