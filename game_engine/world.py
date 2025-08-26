import math, random
from PyQt6.QtGui import QColor
from .objects import StaticObject

CHUNK_SIZE = 20
POINTS_PER_CHUNK = 18
WORLD_SEED = 1337

class StaticWorld:
    def __init__(self):
        self.objects: list[StaticObject] = []

    def points_near(self, x: float, z: float, radius: float) -> list[tuple]:
        r2 = radius * radius
        out = []
        for obj in self.objects:
            for (px, py, pz, col) in obj.to_points():
                dx = px - x
                dz = pz - z
                if dx*dx + dz*dz <= r2:
                    out.append((px, py, pz, col))
        return out

    def solids_aabb(self):
        return [obj.aabb() for obj in self.objects if obj.can_collide]

class ChunkWorld:
    def __init__(self, seed: int = WORLD_SEED):
        self.seed = seed
        self.chunks: dict[tuple[int, int], list[tuple[float, float, float]]] = {}

    def _chunk_seed(self, cx: int, cz: int) -> int:
        return (cx * 73856093) ^ (cz * 19349663) ^ self.seed

    def generate_chunk(self, cx: int, cz: int):
        key = (cx, cz)
        if key in self.chunks:
            return
        rng = random.Random(self._chunk_seed(cx, cz))
        pts = []
        for _ in range(POINTS_PER_CHUNK):
            lx = rng.uniform(0.5, CHUNK_SIZE - 0.5)
            lz = rng.uniform(0.5, CHUNK_SIZE - 0.5)
            x = cx * CHUNK_SIZE + lx
            z = cz * CHUNK_SIZE + lz
            y = rng.uniform(-1.0, 1.5)
            pts.append((x, y, z))
        self.chunks[key] = pts

    def has_chunk(self, cx: int, cz: int) -> bool:
        return (cx, cz) in self.chunks

    def iter_chunk_coords_in_radius(self, x: float, z: float, radius: float):
        min_cx = int(math.floor((x - radius) / CHUNK_SIZE))
        max_cx = int(math.floor((x + radius) / CHUNK_SIZE))
        min_cz = int(math.floor((z - radius) / CHUNK_SIZE))
        max_cz = int(math.floor((z + radius) / CHUNK_SIZE))
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                yield cx, cz

    def ensure_chunks_around(self, x: float, z: float, radius: float):
        for cx, cz in self.iter_chunk_coords_in_radius(x, z, radius):
            self.generate_chunk(cx, cz)

    def points_near(self, x: float, z: float, radius: float):
        self.ensure_chunks_around(x, z, radius)
        r2 = radius * radius
        pts = []
        for (_, _), chunk_pts in self.chunks.items():
            for (px, py, pz) in chunk_pts:
                dx = px - x
                dz = pz - z
                if dx*dx + dz*dz <= r2:
                    pts.append((px, py, pz))
        return pts

    @staticmethod
    def filter_points_by_fov(points, cam, forward, fov_rad):
        """
        Vrátí body, které leží v zorném poli kamery (FOV).
        Zachová barvu, pokud je součástí bodu.

        points: list (x,y,z) nebo (x,y,z,color)
        cam: pozice kamery (cx,cy,cz)
        forward: vektor dopředu
        fov_rad: zorný úhel v radiánech
        """
        cx, cy, cz = cam
        cos_half = math.cos(fov_rad / 2.0)
        out = []

        for p in points:
            # Rozbalení barvy, pokud existuje
            if len(p) == 4:
                x, y, z, col = p
            else:
                x, y, z = p
                col = None

            dx, dy, dz = x - cx, y - cy, z - cz
            d2 = dx * dx + dy * dy + dz * dz
            if d2 < 1e-12:
                continue

            inv = 1.0 / math.sqrt(d2)
            dirx, diry, dirz = dx * inv, dy * inv, dz * inv
            dot = forward[0] * dirx + forward[1] * diry + forward[2] * dirz

            if dot >= cos_half:
                out.append((x, y, z, col) if col is not None else (x, y, z))

        return out
