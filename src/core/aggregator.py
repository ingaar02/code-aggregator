import hashlib
from pathlib import Path
from typing import List, Dict, Optional


class Aggregator:
    def __init__(self):
        self.file_cache: Dict[str, str] = {}
        self.file_hashes: Dict[str, str] = {}

    def _is_text_file(self, file_path: Path) -> bool:
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return False
            return True
        except Exception:
            return False

    def _read_file(self, file_path: Path) -> Optional[str]:
        encodings = ["utf-8", "cp1252", "latin-1", "cp1251"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, PermissionError):
                continue
        return None

    def _collect_files(
        self, sources: List[dict], extensions: List[str], exclude_ext: List[str]
    ) -> List[Path]:
        files = []
        seen = set()

        for src in sources:
            src_path = Path(src["path"])
            if not src_path.exists():
                continue

            if src["type"] == "file":
                if str(src_path) not in seen:
                    files.append(src_path)
                    seen.add(str(src_path))
            elif src["type"] == "directory":
                recursive = src.get("recursive", True)
                exclude_dirs = set(src.get("exclude", []))
                pattern = "**/*" if recursive else "*"

                for file_path in src_path.glob(pattern):
                    if not file_path.is_file():
                        continue

                    rel_parts = file_path.relative_to(src_path).parts
                    if any(part in exclude_dirs for part in rel_parts):
                        continue

                    ext = file_path.suffix.lower()
                    if extensions and ext not in extensions:
                        continue
                    if exclude_ext and ext in exclude_ext:
                        continue

                    if str(file_path) not in seen:
                        files.append(file_path)
                        seen.add(str(file_path))

        return sorted(files)

    def aggregate(
        self,
        sources: List[dict],
        extensions: List[str],
        exclude_ext: List[str],
        output_path: str,
    ) -> dict:
        files = self._collect_files(sources, extensions, exclude_ext)

        if not files:
            return {
                "success": False,
                "error": "Нет файлов для обработки",
                "files_count": 0,
            }

        output_lines = []
        processed = 0
        skipped = 0

        for file_path in files:
            if not self._is_text_file(file_path):
                skipped += 1
                continue

            content = self._read_file(file_path)
            if content is None:
                skipped += 1
                continue

            # Экранируем содержимое: кавычки, слэши, переносы строк
            escaped = (
                content.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
            )

            # Формат: имя_файла:"содержимое" — всё в одной строке
            line = f'{file_path.name}:"{escaped}"'
            output_lines.append(line)
            output_lines.append("")  # пустая строка между блоками

            processed += 1

        if output_lines and output_lines[-1] == "":
            output_lines.pop()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        result_text = "\n".join(output_lines)
        with open(output, "w", encoding="utf-8") as f:
            f.write(result_text)

        result_hash = hashlib.md5(result_text.encode("utf-8")).hexdigest()

        return {
            "success": True,
            "files_count": processed,
            "skipped": skipped,
            "output_path": str(output),
            "hash": result_hash,
        }
