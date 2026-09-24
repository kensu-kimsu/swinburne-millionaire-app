"""Build compact animation frames from the checked-in illustrated sources.

Run `python scripts/build_dungeon_animation.py` after replacing a source asset.
The original character frames remain untouched so this build is repeatable.
"""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1] / 'static/assets/dungeon'
SOURCE = ROOT / 'fire-source.webp'


def save(image, path):
    image.save(path, 'WEBP', quality=82, method=5)


def build_fire():
    flame = Image.open(SOURCE).convert('RGBA')
    for frame in range(8):
        # Fix the wick in place while the upper silhouette bends and flickers.
        width = (67, 70, 73, 69, 65, 68, 72, 69)[frame]
        height = (99, 103, 106, 102, 97, 101, 104, 100)[frame]
        shape = flame.resize((width, height), Image.Resampling.LANCZOS)
        shape = ImageEnhance.Brightness(shape).enhance((.93, .98, 1.04, 1.0, .94, .99, 1.03, .97)[frame])
        canvas = Image.new('RGBA', (80, 110))
        canvas.alpha_composite(shape, ((80 - width) // 2 + (frame % 3 - 1), 108 - height))
        save(canvas, ROOT / f'fx-flame-{frame}.webp')


def motion_frames(frames):
    """Motion-compensated inbetweens, with alpha estimated independently."""
    size = frames[0].size
    working = (min(size[0], 192), min(size[1], 256))
    matte = np.array([22, 19, 22], dtype=np.float32)
    with TemporaryDirectory() as temp:
        root = Path(temp)
        for sub in ('color_in', 'alpha_in', 'color_out', 'alpha_out'):
            (root / sub).mkdir()
        # Two extra poses permit interpolation of the final -> first pair.
        for i in range(len(frames) + 2):
            frame = frames[i % len(frames)].resize(working, Image.Resampling.LANCZOS)
            background = Image.new('RGBA', working, (22, 19, 22, 255))
            background.alpha_composite(frame)
            background.convert('RGB').save(root / 'color_in' / f'{i:03}.png')
            frame.getchannel('A').convert('RGB').save(root / 'alpha_in' / f'{i:03}.png')
        for kind in ('color', 'alpha'):
            subprocess.run([
                'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '10',
                '-i', str(root / f'{kind}_in' / '%03d.png'), '-vf',
                'minterpolate=fps=20:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
                '-frames:v', str(2 * len(frames) + 1),
                str(root / f'{kind}_out' / '%03d.png')], check=True)
        for i, original in enumerate(frames):
            yield original
            rgb = np.asarray(Image.open(root / 'color_out' / f'{2*i+2:03}.png').convert('RGB'), dtype=np.float32)
            alpha = np.asarray(Image.open(root / 'alpha_out' / f'{2*i+2:03}.png').convert('L'), dtype=np.float32)
            fraction = alpha[..., None] / 255
            restored = np.clip((rgb - matte * (1 - fraction)) / np.maximum(fraction, .08), 0, 255)
            rgba = np.dstack((restored, np.where(alpha < 10, 0, alpha))).astype('uint8')
            yield Image.fromarray(rgba, 'RGBA').resize(size, Image.Resampling.LANCZOS)


def build_characters():
    for name, count, target in [('hero-run', 8, 'hero-smooth')]:
        frames = [Image.open(ROOT / f'{name}-{i}.webp').convert('RGBA') for i in range(count)]
        for i, frame in enumerate(motion_frames(frames)):
            save(frame, ROOT / f'{target}-{i}.webp')

    for source in sorted(ROOT.glob('run-*.webp')):
        name = source.stem[4:]
        originals = [ROOT / f'run-{name}-{i}.webp' for i in range(4)]
        if not all(path.exists() for path in originals):
            continue
        frames = [Image.open(path).convert('RGBA') for path in originals]
        for i, frame in enumerate(motion_frames(frames)):
            save(frame, ROOT / f'move-{name}-{i}.webp')


if __name__ == '__main__':
    build_fire()
    build_characters()
