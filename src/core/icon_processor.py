from pathlib import Path
from PIL import Image


class IconProcessor:
    @staticmethod
    def process(input_path: str, output_path: str, size: int = 512) -> str:
        """
        Кадрирует в квадрат по центру, ресайзит до size×size, сохраняет PNG.
        """
        img = Image.open(input_path)

        # Конвертируем в RGBA если нужно
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # Кадрирование в квадрат по центру
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        img = img.crop((left, top, right, bottom))

        # Ресайз с высоким качеством
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Сохранение с оптимизацией
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(output, "PNG", optimize=True)

        return str(output)
