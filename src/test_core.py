import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.project_manager import ProjectManager, Source

pm = ProjectManager()

# Создаём тестовый проект
project = pm.create(
    name="TestApp",
    description="Тестовый проект",
    sources=[
        Source(type="directory", path="src", recursive=True, exclude=["node_modules", ".git"]),
        Source(type="file", path="src/main.py")
    ],
    extensions=[".py", ".txt"],
    output_path="output/result.txt",
    backup_dir="output/backups"
)

print(f"Создан проект: {project.name}")
print(f"ID: {project.id}")
print(f"Стек: {project.stack_detected}")
print(f"Sources: {project.sources}")

# Загружаем обратно
loaded = pm.load(project.id)
print(f"\nЗагружен: {loaded.name}, стек: {loaded.stack_detected}")

# Список всех
all_projects = pm.list_all()
print(f"\nВсего проектов: {len(all_projects)}")
for p in all_projects:
    print(f"  - {p.name} ({p.id})")

print("\n✅ Ядро работает.")