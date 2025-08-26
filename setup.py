from setuptools import setup, find_packages

try:
    with open("README.md", encoding="utf-8") as f:
        long_desc = f.read()
except FileNotFoundError:
    long_desc = ""

setup(
    name="game-engine",
    version="0.2.0",
    author="Antonín Šiška",
    author_email="siska.antonin.mail@example.com",
    description="3D FPS demo s PyQt6, kolizemi a minimapou",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/antoninsiska/Game-Engine",
    packages=find_packages(),
    install_requires=["PyQt6>=6.5.0"],
    entry_points={
        "console_scripts": [
            "game-engine=game_engine.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
)