# Game Engine 🎮
> A simple FPS engine in Python with PyQt6 — featuring procedural world generation, collisions, minimap, and custom objects support.

---

## ✨ Main Features
- 🕹 **FPS camera** — smooth movement, mouse look, sprint, jump, reset position  
- 🌍 **Procedural world generation** — world divided into chunks, dynamic point loading  
- 🧱 **Static objects** — defined by pattern or generated automatically  
- 🛡 **Collision system** — supports AABB collisions for static objects  
- 🗺 **Minimap** — can rotate with the camera, displays objects and chunks  
- 🎨 **Color support** — every object can have its own color  
- 🧩 **Simple API** — easy to add custom objects, worlds, and behaviors  
- ⚡ **Optimizations** — FOV filter, loading chunks around the camera  

---

## 🛠 Installation

### **1. From GitHub**
```bash
pip install git+https://github.com/antoninsiska/Game-Engine.git@latest
```

### **2. Local Development**
```bash
git clone https://github.com/antoninsiska/Game-Engine.git
cd Game-Engine
pip install -e .
```

### **3. Requirements**
- Python **3.9+**
- PyQt6 **6.5+**

---

## 🎮 Running the Demo App

After installation you can run the default demo:

```bash
game-engine
```

---

## ⌨️ Controls

| Key | Action |
|-----|--------|
| **W / A / S / D** | Move |
| **Mouse** | Camera rotation |
| **Shift** | Sprint |
| **Space** | Move up |
| **Ctrl** / **C** | Move down |
| **B** | Reset position |
| **M** | Toggle minimap rotation |
| **P** | Pause |
| **ESC** | Release mouse |

---

## 🧩 Project Structure

```
game_engine/
│── __init__.py      # public package API
│── gui.py           # FPSDemo class — GUI logic & rendering
│── world.py         # ChunkWorld and StaticWorld — world generation
│── objects.py       # StaticObject — object definitions
│── main.py          # entry point for `game-engine` command
```

---

## 🔹 Basic Usage in Python

```python
import sys
from PyQt6.QtWidgets import QApplication
from game_engine import FPSDemo

app = QApplication(sys.argv)
demo = FPSDemo()
demo.show()
sys.exit(app.exec())
```

---

## 🧱 Adding Custom Objects

### **1. Static Object**
```python
from game_engine import StaticObject

cube = StaticObject.from_size(
    3, 3,
    pos=(5, 0, 5),
    color="blue",
    name="cube",
    collision=True  # ✅ player cannot pass through
)
game.static_world.objects.append(cube)
```

---

## 🛡 Collisions

Collisions work automatically for all objects with **`collision=True`**.  
The engine uses **AABB collisions** (axis-aligned bounding boxes).

### **How to add a collidable object**
```python
tree = StaticObject.from_size(
    2, 5,
    pos=(10, 0, 5),
    color="green",
    name="tree",
    collision=True
)
game.static_world.objects.append(tree)
```

### **How to add decoration without collisions**
```python
flower = StaticObject.from_size(
    1, 1,
    pos=(3, 0, 3),
    color="yellow",
    name="flower",
    collision=False  # ✅ player can pass through
)
game.static_world.objects.append(flower)
```

---

## 🌍 Procedural World

### **ChunkWorld**
Generates procedural points into "chunks".

```python
from game_engine import ChunkWorld

world = ChunkWorld()
world.ensure_chunks_around(0, 0, 60)  # create chunks around the camera
points = world.points_near(0, 0, 30)
print(points)
```

---

## 🧩 StaticWorld API

### **StaticWorld**
Manages all static objects.

```python
from game_engine import StaticWorld, StaticObject

world = StaticWorld()
cube = StaticObject.from_size(3, 3, pos=(5, 0, 5))
world.objects.append(cube)
```

#### **Methods:**
| Method | Description |
|--------|-------------|
| `points_near(x, z, radius)` | Returns points near the camera |
| `solids_aabb()` | Returns AABB boxes of all collidable objects |

---

## 🎨 StaticObject API

### **Creating a custom object**
```python
obj = StaticObject(
    pattern=[[1,1,1],[1,1,1],[1,1,1]],
    pos=(5, 0, 5),
    name="cube",
    color="red",
    cell_size=1.0,
    collision=True
)
```

#### **Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | list[list[int]] | Object pattern |
| `pos` | tuple | Position (x,y,z) |
| `name` | str | Object name |
| `color` | QColor/str | Color |
| `cell_size` | float | Size of one cell |
| `collision` | bool | Enable collisions |

---

## 🕹 Creating Your Own Game (`MyGame`)

```python
import sys
from PyQt6.QtWidgets import QApplication
from game_engine import FPSDemo, StaticObject

class MyGame(FPSDemo):
    def __init__(self):
        super().__init__()

        # Custom collidable object
        cube = StaticObject.from_size(
            3, 3,
            pos=(5, 0, 5),
            color="blue",
            name="cube",
            collision=True
        )
        self.static_world.objects.append(cube)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = MyGame()
    game.show()
    sys.exit(app.exec())
```

Run:
```bash
python main.py
```

---

## 🧰 Debugging & Tips
- **Show collision boxes** – add a debug overlay  
- **Adjust FOV** – change `VFOV_DEG` in `gui.py`  
- **Change player speed** – set `self.move_speed`  
- **Adjust chunks** – modify `CHUNK_SIZE` in `world.py`  
- **Toggle minimap** – built-in, press `M`  

---

## 🛠 Development

### **Update the engine**
```bash
pip install --upgrade git+https://github.com/antoninsiska/Game-Engine.git@latest
```

### **Local Development**
```bash
git clone https://github.com/antoninsiska/Game-Engine.git
cd Game-Engine
pip install -e .
```

---

## 📜 License
MIT © 2025 Antonín Šiška
