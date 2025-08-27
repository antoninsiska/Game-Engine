import sys, math, time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QBrush

from .world import ChunkWorld, CHUNK_SIZE, WORLD_SEED
from .world import ChunkWorld, StaticWorld  

# VFOV pro kameru
VFOV_DEG = 70
LOAD_RADIUS = 60

class FPSDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPS demo (static objects, FOV, pause, collisions)")
        self.resize(1280, 720)
        self.setMouseTracking(True)
        self.grabMouse()
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # kamera
        self.cam = [0.0, 0.0, 0.0]
        self.yaw = 0.0
        self.pitch = 0.0
        self.near = 0.1

        # hrac (kolize)
        self.player_radius = 0.45  # „tloustka“ hrace v XZ pro kolizi

        # svety
        self.world = ChunkWorld(seed=WORLD_SEED)
        self.static_world = StaticWorld()

        # vstupy
        self.keys_down = set()
        self.mouse_sens = 0.0022
        self.move_speed = 5.0
        self.paused = False
        self._pause_key_down = False  # proti autorepeat toggle

        # minimapa
        self.minimap_size = 220
        self.minimap_radius = 60
        self.minimap_rotate_with_cam = True
        self.show_chunk_grid = True
        self.highlight_loaded_chunks = True

        # kurzor center
        self.center_global = self.mapToGlobal(self.rect().center())

        # timing
        self.last_time = time.perf_counter()
        self.fps = 0.0
        self._fps_accum = 0.0
        self._fps_frames = 0

        # runtime cache
        self.fwd = (0.0, 0.0, 1.0)
        self.right = (1.0, 0.0, 0.0)
        self.up = (0.0, 1.0, 0.0)
        self.render_points = []      # list (x,y,z) nebo (x,y,z,color)

        # loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)

    # --- utils ---
    def size_params(self):
        w = self.width()
        h = self.height()
        aspect = w / h if h else 1.0
        vfov = math.radians(VFOV_DEG)
        fy = (h / 2) / math.tan(vfov / 2) if h else 1.0
        fx = fy * aspect
        cx, cy = w // 2, h // 2
        return w, h, fx, fy, cx, cy

    def update_center_global(self):
        self.center_global = self.mapToGlobal(self.rect().center())

    def recenter_mouse(self):
        QCursor.setPos(self.center_global)

    # --- events ---
    def showEvent(self, e):
        super().showEvent(e)
        self.update_center_global()
        self.recenter_mouse()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update_center_global()

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        self.keys_down.add(e.key())
        if e.key() == Qt.Key.Key_M:
            self.minimap_rotate_with_cam = not self.minimap_rotate_with_cam
        elif e.key() == Qt.Key.Key_P:
            self._pause_key_down = True  # toggle az na release
        elif e.key() == Qt.Key.Key_Escape:
            # jen uvolni mys, nepauzuje
            self.releaseMouse()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        e.accept()

    def keyReleaseEvent(self, e):
        if e.isAutoRepeat():
            return
        self.keys_down.discard(e.key())
        if e.key() == Qt.Key.Key_P and self._pause_key_down:
            self._pause_key_down = False
            self.toggle_pause()
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

    # --- pause ---
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.keys_down.clear()
            self.releaseMouse()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.grabMouse()
            self.setCursor(Qt.CursorShape.BlankCursor)
            self.update_center_global()
            self.recenter_mouse()
            self.last_time = time.perf_counter()  # reset dt
        self.update()

    # --- math dirs ---
    def compute_dirs(self):
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        fwd = (sy * cp, sp, cy * cp)
        right = (cy, 0.0, -sy)
        up = (0.0, 1.0, 0.0)
        return fwd, right, up

    # --- kolizni pomocne ---
    @staticmethod
    def _overlaps_expanded_z(cam_z: float, box, r: float) -> bool:
        minx, minz, maxx, maxz = box
        return (cam_z >= (minz - r)) and (cam_z <= (maxz + r))

    @staticmethod
    def _overlaps_expanded_x(cam_x: float, box, r: float) -> bool:
        minx, minz, maxx, maxz = box
        return (cam_x >= (minx - r)) and (cam_x <= (maxx + r))

    def resolve_collision_axis(self, cam_x: float, cam_z: float, dx: float, dz: float, boxes, r: float):
        """
        Pohyb rozdelene po osach. Nejdřív X, pak Z.
        Clampne pozici na hrany AABB rozsirenych o polomer hrace.
        """
        # X osa
        if abs(dx) > 0.0:
            next_x = cam_x + dx
            for (minx, minz, maxx, maxz) in boxes:
                if not self._overlaps_expanded_z(cam_z, (minx, minz, maxx, maxz), r):
                    continue
                # pohyb doprava: naraz do leve hrany boxu
                if dx > 0 and cam_x <= (minx - r) and next_x > (minx - r):
                    next_x = (minx - r)
                # pohyb doleva: naraz do prave hrany boxu
                if dx < 0 and cam_x >= (maxx + r) and next_x < (maxx + r):
                    next_x = (maxx + r)
            cam_x = next_x

        # Z osa
        if abs(dz) > 0.0:
            next_z = cam_z + dz
            for (minx, minz, maxx, maxz) in boxes:
                if not self._overlaps_expanded_x(cam_x, (minx, minz, maxx, maxz), r):
                    continue
                # pohyb dopredu (z++): naraz do horni hrany boxu (minz)
                if dz > 0 and cam_z <= (minz - r) and next_z > (minz - r):
                    next_z = (minz - r)
                # pohyb dozadu (z--): naraz do spodni hrany boxu (maxz)
                if dz < 0 and cam_z >= (maxz + r) and next_z < (maxz + r):
                    next_z = (maxz + r)
            cam_z = next_z

        return cam_x, cam_z

    def move_with_collisions(self, spd_vec, dt):
        """
        Aplikuje pohyb s kolizi (AABB). spd_vec = (vx, vy, vz) v jednotkach/s po normalizaci a nasobeni rychlosti.
        Y je drzeno 0.
        """
        vx, vy, vz = spd_vec
        # solid boxy jen ze statickych objektu (proceduralni body jsou jen „vizualni“)
        boxes = self.static_world.solids_aabb()
        r = self.player_radius

        cam_x, cam_y, cam_z = self.cam
        dx = vx * dt
        dz = vz * dt

        # rozdelene po osach s clampem
        cam_x, cam_z = self.resolve_collision_axis(cam_x, cam_z, dx, dz, boxes, r)

        # zpet do kamery
        self.cam[0] = cam_x
        self.cam[2] = cam_z
        # drzim po „zemi“
        if self.cam[1] != 0.0:
            self.cam[1] = 0.0

    # --- update loop ---
    def tick(self):
        if self.paused:
            self.update()
            return
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now

        self._fps_accum += dt; self._fps_frames += 1
        if self._fps_accum >= 0.25:
            self.fps = self._fps_frames / self._fps_accum
            self._fps_accum = 0.0; self._fps_frames = 0

        self.update_camera(dt)

        # 1) vygeneruj/projdi proceduralni chunky v radiusu
        cx, cy, cz = self.cam
        self.world.ensure_chunks_around(cx, cz, LOAD_RADIUS)

        proc_pts = self.world.points_near(cx, cz, LOAD_RADIUS)             # (x,y,z)
        stat_pts = self.static_world.points_near(cx, cz, LOAD_RADIUS)      # (x,y,z,color)

        # 2) sloucime zdroje a FOV-filtrujeme (barvy zachovame)
        merged = proc_pts + stat_pts
        fov_rad = math.radians(VFOV_DEG)
        self.render_points = ChunkWorld.filter_points_by_fov(merged, self.cam, self.fwd, fov_rad)

        self.update()

    def update_camera(self, dt):
        fwd, right, up = self.compute_dirs()
        v = [0.0, 0.0, 0.0]
        k = self.keys_down
        if Qt.Key.Key_W in k: v = [v[i] + fwd[i] for i in range(3)]
        if Qt.Key.Key_S in k: v = [v[i] - fwd[i] for i in range(3)]
        if Qt.Key.Key_D in k: v = [v[i] + right[i] for i in range(3)]
        if Qt.Key.Key_A in k: v = [v[i] - right[i] for i in range(3)]
        if Qt.Key.Key_Space in k: v = [v[i] + up[i] for i in range(3)]
        if Qt.Key.Key_Control in k or Qt.Key.Key_C in k: v = [v[i] - up[i] for i in range(3)]
        if Qt.Key.Key_B in k:
            self.cam[:] = [0.0, 0.0, 0.0]; self.yaw = 0.0; self.pitch = 0.0

        # normalizace + sprint -> rychlost v jednotkach/s
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
        if mag > 1e-6:
            v = [vi / mag for vi in v]
            spd = self.move_speed * (2.0 if Qt.Key.Key_Shift in k else 1.0)
            vx, vy, vz = (v[0]*spd, v[1]*spd, v[2]*spd)
            # aplikuj pohyb PRES KOLIZNI RESOLVER
            self.move_with_collisions((vx, vy, vz), dt)
        else:
            # bez pohybu jen udrz y=0
            if self.cam[1] != 0.0:
                self.cam[1] = 0.0

        # cache pro dalsi faze
        self.fwd, self.right, self.up = fwd, right, up

    # --- render ---
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor(0, 0, 0))

        w, h, fx, fy, _, _ = self.size_params()
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)
        cx, cy, cz = self.cam

        # Kreslime JEN render_points (po FOV filtru).
        # priprav si polozky s hloubkou a serad je (far -> near)
        items = []
        for pt in self.render_points:
            if len(pt) == 4:
                x, y, z, col = pt
            else:
                x, y, z = pt
                col = QColor(255, 120, 120)

            # do prostoru kamery
            x -= cx; y -= cy; z -= cz
            xz = x * cos_y - z * sin_y
            zz = x * sin_y + z * cos_y
            yz = y * cos_p - zz * sin_p
            zz = y * sin_p + zz * cos_p
            if zz <= self.near:
                continue

            sx = int(w / 2 + (xz / zz) * fx)
            sy = int(h / 2 - (yz / zz) * fy)
            size = max(2, int(220 / zz))
            items.append((zz, sx, sy, size, col))

        # serazeno podle hloubky: nejdriv dal, pak blizko
        items.sort(key=lambda t: t[0], reverse=True)

        # ted teprve kresli (blizsi prekresli vzdalene)
        for zz, sx, sy, size, col in items:
            half = size // 2
            p.fillRect(sx - half, sy - half, size, size, col)

        # HUD
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Menlo", 14))
        yaw_deg = (math.degrees(self.yaw) % 360.0); pitch_deg = math.degrees(self.pitch)
        p.drawText(20, 30, f"Yaw: {yaw_deg:6.1f} deg   Pitch: {pitch_deg:6.1f} deg   FPS: {self.fps:5.1f}")
        p.drawText(20, 55, f"Player radius: {self.player_radius:.2f}")

        # minimapa
        self.draw_minimap(p)

        # overlay pri pauze
        if self.paused:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawRect(self.rect())
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Menlo", 28))
            p.drawText(20, 95, "PAUSED  (P to resume)")

    def draw_minimap(self, p: QPainter):
        size = self.minimap_size
        margin = 16
        rect = QRect(self.width() - size - margin, margin, size, size)

        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 20, 25, 200))
        p.drawRoundedRect(rect, 12, 12)

        p.setPen(QPen(QColor(90, 90, 110), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)

        p.setClipRect(rect.adjusted(4, 4, -4, -4))
        cx_px = rect.center().x()
        cy_px = rect.center().y()

        map_px_radius = (size - 20) * 0.5
        units_per_px = self.minimap_radius / map_px_radius
        scale = 1.0 / units_per_px

        p.translate(cx_px, cy_px)
        if self.minimap_rotate_with_cam:
            p.rotate(-math.degrees(self.yaw))

        # orientacni kruhy
        p.setPen(QPen(QColor(60, 60, 80, 160), 1))
        for r_units in (10, 20, 30, 40, 50, 60):
            r_px = r_units * scale
            p.drawEllipse(QPoint(0, 0), int(r_px), int(r_px))

        camx, _, camz = self.cam

        # proced. chunky (obrys)
        if self.show_chunk_grid:
            thin = QPen(QColor(80, 100, 140, 140), 1)
            bold_loaded = QPen(QColor(110, 170, 255, 200), 2)

            for (gx, gz) in self.world.iter_chunk_coords_in_radius(camx, camz, self.minimap_radius):
                x0 = gx * CHUNK_SIZE
                z0 = gz * CHUNK_SIZE
                x1 = x0 + CHUNK_SIZE
                z1 = z0 + CHUNK_SIZE

                def to_px(xw, zw):
                    dx = (xw - camx) * scale
                    dz = (zw - camz) * scale
                    return QPoint(int(dx), int(-dz))

                a = to_px(x0, z0); b = to_px(x1, z0); c = to_px(x1, z1); d = to_px(x0, z1)
                p.setPen(bold_loaded if self.world.has_chunk(gx, gz) else thin)
                p.drawLine(a, b); p.drawLine(b, c); p.drawLine(c, d); p.drawLine(d, a)

        # body na minimape (pouzivame render_points, tedy uz FOV-filterovane)
        for pt in self.render_points:
            if len(pt) == 4:
                x, y, z, col = pt
            else:
                x, y, z = pt
                col = QColor(255, 120, 120)
            dx = x - camx; dz = z - camz
            if abs(dx) > self.minimap_radius or abs(dz) > self.minimap_radius: continue
            mx = dx * scale; mz = -dz * scale
            p.fillRect(int(mx)-2, int(mz)-2, 4, 4, col)

        # hrac + smer
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.setBrush(QBrush(QColor(0, 0, 0)))
        p.drawEllipse(QPoint(0, 0), 5, 5)
        p.drawLine(0, 0, 0, -14)

        p.restore()