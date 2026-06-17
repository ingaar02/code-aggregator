import subprocess
from pathlib import Path


class GitManager:
    @staticmethod
    def _run(cmd, cwd, timeout=30):
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Таймаут команды",
                "code": -1,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "code": -1}

    @classmethod
    def get_repo_root(cls, cwd):
        """Находит корень Git-репозитория от любой папки внутри"""
        result = cls._run(["git", "rev-parse", "--show-toplevel"], cwd)
        if result["success"] and result["stdout"]:
            return result["stdout"].strip()
        return None

    @classmethod
    def pull(cls, cwd):
        root = cls.get_repo_root(cwd)
        if not root:
            return {"success": False, "stderr": "Git-репозиторий не найден"}
        return cls._run(["git", "pull"], root)

    @classmethod
    def push(cls, cwd, message="update: auto commit from Code Aggregator"):
        root = cls.get_repo_root(cwd)
        if not root:
            return {"success": False, "stderr": "Git-репозиторий не найден"}

        # Проверяем, есть ли изменения
        status = cls._run(["git", "status", "--porcelain"], root)
        if not status["success"]:
            return status

        has_changes = bool(status["stdout"].strip())

        if has_changes:
            # Add → Commit → Push
            add = cls._run(["git", "add", "."], root)
            if not add["success"]:
                return add

            commit = cls._run(["git", "commit", "-m", message], root)
            if not commit["success"]:
                return commit

        # Push (если есть что пушить или незапушенные коммиты)
        push = cls._run(["git", "push"], root)
        return push
