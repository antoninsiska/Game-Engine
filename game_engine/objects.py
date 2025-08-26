from PyQt6.QtGui import QColor

class StaticObject:
    """
    Staticky objekt definovany 2D sablonou (matrix 0/1).
    Kazda 1 v sablone znaci, ze se tam vykresli bod (ctverec) o velikosti cell_size.
    Vystup: body (x, y, z, color).
    """
    def __init__(self,
                 pattern: list[list[int]],
                 pos: tuple[float, float, float] = (0.0, 0.0, 0.0),
                 name: str = "",
                 color = QColor(0, 255, 0),
                 cell_size: float = 1.0,
                 collision: bool = False,
                 y: float = 0.0):
        self.pattern = pattern
        self.pos = pos
        self.name = name
        self.color = QColor(color) if not isinstance(color, QColor) else color
        self.cell_size = cell_size
        self.can_collide = collision
        self.y_fixed = y

    @classmethod
    def from_size(cls, w: int, h: int, **kwargs):
        pattern = [[1]*w for _ in range(h)]
        return cls(pattern, **kwargs)

    def to_points(self) -> list[tuple[float, float, float, QColor]]:
        x0, _, z0 = self.pos
        pts = []
        rows = len(self.pattern)
        cols = len(self.pattern[0]) if rows > 0 else 0
        for r in range(rows):
            for c in range(cols):
                if self.pattern[r][c]:
                    x = x0 + c * self.cell_size
                    z = z0 + r * self.cell_size
                    pts.append((x, self.y_fixed, z, self.color))
        return pts

    def aabb(self):
        rows = len(self.pattern)
        cols = len(self.pattern[0]) if rows > 0 else 0
        width = cols * self.cell_size
        depth = rows * self.cell_size
        x0, _, z0 = self.pos
        return (x0, z0, x0 + width, z0 + depth)
