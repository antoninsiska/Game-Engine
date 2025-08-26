# Game Engine 🎮
> Jednoduchý FPS engine v Pythonu s PyQt6 — s procedurálním generováním světa, kolizemi, minimapou a podporou vlastních objektů.

---

## ✨ Hlavní funkce
- 🕹 **FPS kamera** — plynulé pohyby, otáčení myší, sprint, skok, reset pozice  
- 🌍 **Procedurální generování světa** — svět rozdělený na chunky, dynamické načítání bodů  
- 🧱 **Statické objekty** — definované vzorem nebo generované automaticky  
- 🛡 **Kolizní systém** — podpora AABB kolizí pro statické objekty  
- 🗺 **Minimapa** — s možností rotace podle kamery, zobrazuje objekty a chunky  
- 🎨 **Podpora barev** — každý objekt může mít vlastní barvu  
- 🧩 **Jednoduché API** — snadné přidávání vlastních objektů, světů i chování  
- ⚡ **Optimalizace** — FOV filtr, načítání chunků v okolí kamery  

---

## 🛠 Instalace

### **1. Instalace z GitHubu**
```bash
pip install git+https://github.com/antoninsiska/Game-Engine.git@latest
```

### **2. Lokální vývoj**
```bash
git clone https://github.com/antoninsiska/Game-Engine.git
cd Game-Engine
pip install -e .
```

### **3. Požadavky**
- Python **3.9+**
- PyQt6 **6.5+**

---

## 🎮 Spuštění demo aplikace

Po instalaci můžeš spustit výchozí demo:

```bash
game-engine
```

---

## ⌨️ Ovládání

| Klávesa | Funkce |
|---------|--------|
| **W / A / S / D** | Pohyb |
| **Myš** | Otáčení kamery |
| **Shift** | Sprint |
| **Space** | Pohyb nahoru |
| **Ctrl** / **C** | Pohyb dolů |
| **B** | Reset pozice |
| **M** | Přepnutí rotace minimapy |
| **P** | Pauza hry |
| **ESC** | Uvolnění myši |

---

## 🧩 Struktura projektu

```
game_engine/
│── __init__.py      # veřejné API balíčku
│── gui.py           # FPSDemo třída — GUI logika a renderování
│── world.py         # ChunkWorld a StaticWorld — generování světa
│── objects.py       # StaticObject — definice objektů
│── main.py          # vstupní bod pro příkaz `game-engine`
```

---

## 🔹 Základní použití v Pythonu

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

## 🧱 Přidávání vlastních objektů

### **1. Statický objekt**
```python
from game_engine import StaticObject

cube = StaticObject.from_size(
    3, 3,
    pos=(5, 0, 5),
    color="blue",
    name="kostka",
    collision=True  # ✅ hráč nemůže projít
)
game.static_world.objects.append(cube)
```

---

## 🛡 Kolize

Kolize fungují automaticky pro všechny objekty, které mají **`collision=True`**.  
Engine používá **AABB kolize** (axis-aligned bounding box).

### **Jak nastavit kolizní objekt**
```python
tree = StaticObject.from_size(
    2, 5,
    pos=(10, 0, 5),
    color="green",
    name="strom",
    collision=True
)
game.static_world.objects.append(tree)
```

### **Jak vytvořit dekoraci bez kolizí**
```python
flower = StaticObject.from_size(
    1, 1,
    pos=(3, 0, 3),
    color="yellow",
    name="květina",
    collision=False  # ✅ hráč může projít
)
game.static_world.objects.append(flower)
```

---

## 🌍 Procedurální svět

### **ChunkWorld**
Generuje procedurální body do "chunků".

```python
from game_engine import ChunkWorld

world = ChunkWorld()
world.ensure_chunks_around(0, 0, 60)  # vytvoří chunky kolem kamery
points = world.points_near(0, 0, 30)
print(points)
```

---

## 🧩 StaticWorld API

### **StaticWorld**
Spravuje všechny statické objekty.

```python
from game_engine import StaticWorld, StaticObject

world = StaticWorld()
cube = StaticObject.from_size(3, 3, pos=(5, 0, 5))
world.objects.append(cube)
```

#### **Metody:**
| Metoda                | Popis |
|-----------------------|--------------------------|
| `points_near(x, z, radius)` | Vrátí body v okolí kamery |
| `solids_aabb()` | Vrátí AABB boxy všech kolizních objektů |

---

## 🎨 StaticObject API

### **Vytvoření vlastního objektu**
```python
obj = StaticObject(
    pattern=[[1,1,1],[1,1,1],[1,1,1]],
    pos=(5, 0, 5),
    name="kostka",
    color="red",
    cell_size=1.0,
    collision=True
)
```

#### **Parametry:**
| Parametr | Typ | Popis |
|----------|------|------------------------------|
| `pattern` | list[list[int]] | Vzor objektu |
| `pos` | tuple | Pozice (x,y,z) |
| `name` | str | Název objektu |
| `color` | QColor/str | Barva |
| `cell_size` | float | Velikost jedné buňky |
| `collision` | bool | Povolit kolize |

---

## 🕹 Vytvoření vlastní hry (`MyGame`)

```python
import sys
from PyQt6.QtWidgets import QApplication
from game_engine import FPSDemo, StaticObject

class MyGame(FPSDemo):
    def __init__(self):
        super().__init__()

        # Vlastní kolizní objekt
        cube = StaticObject.from_size(
            3, 3,
            pos=(5, 0, 5),
            color="blue",
            name="kostka",
            collision=True
        )
        self.static_world.objects.append(cube)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = MyGame()
    game.show()
    sys.exit(app.exec())
```

Spuštění:
```bash
python main.py
```

---

## 🧰 Debugování a tipy
- **Zobrazení kolizních boxů** – můžeme přidat debug overlay  
- **Úprava FOV** – změň `VFOV_DEG` v `gui.py`  
- **Úprava rychlosti hráče** – nastav `self.move_speed`  
- **Úprava chunků** – změň `CHUNK_SIZE` v `world.py`  
- **Přidání minimapy** – je vestavěná, zapíná se klávesou `M`

---

## 🛠 Vývoj

### **Aktualizace enginu**
```bash
pip install --upgrade git+https://github.com/antoninsiska/Game-Engine.git@latest
```

### **Lokální vývoj**
```bash
git clone https://github.com/antoninsiska/Game-Engine.git
cd Game-Engine
pip install -e .
```

---

## 📜 Licence
MIT © 2025 Antonín Šiška
