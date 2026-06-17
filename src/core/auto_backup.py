import time
import threading
from core.backup_manager import BackupManager
from core.aggregator import Aggregator
from core.project_manager import ProjectManager


class AutoBackupThread(threading.Thread):
    def __init__(self, project, interval=15, callback=None):
        super().__init__(daemon=True)
        self.project = project
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()
        self._last_hash = project.last_output_hash

    def stop(self):
        self._stop_event.set()

    def update_project(self, project):
        self.project = project
        self.interval = project.auto_backup_interval

    def run(self):
        while not self._stop_event.is_set():
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    return
                time.sleep(1)

            try:
                # Пересобираем проект, бееееееееее
                agg = Aggregator()
                result = agg.aggregate(
                    sources=self.project.sources,
                    extensions=self.project.extensions,
                    exclude_ext=self.project.exclude_extensions,
                    output_path=self.project.output_path,
                )

                if not result["success"]:
                    continue

                current_hash = result["hash"]

                # Если изменился — бекапим
                if current_hash != self._last_hash:
                    bm = BackupManager(
                        backup_dir=self.project.backup_dir,
                        project_name=self.project.name,
                        max_auto=self.project.max_auto_backups,
                    )

                    backup = bm.create_auto(
                        source_path=self.project.output_path,
                        current_hash=current_hash,
                        last_hash=self._last_hash,
                    )

                    if backup:
                        self._last_hash = current_hash
                        self.project.last_output_hash = current_hash

                        pm = ProjectManager()
                        pm.save(self.project)

                        if self.callback:
                            self.callback(backup)
            except Exception as e:
                print(f"[AutoBackup] Error: {e}")
