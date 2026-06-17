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
        result = cls._run(["git", "rev-parse", "--show-toplevel"], cwd)
        if result["success"] and result["stdout"]:
            return result["stdout"].strip()
        return None

    @classmethod
    def is_repo(cls, cwd):
        """Проверяет, находится ли cwd внутри Git-репозитория"""
        return cls.get_repo_root(cwd) is not None

    @classmethod
    def pull(cls, cwd):
        if not cls.is_repo(cwd):
            return {
                "success": False,
                "stderr": "Git-репозиторий не найден. Выполните git init.",
            }
        root = cls.get_repo_root(cwd)
        return cls._run(["git", "pull"], root)

    @classmethod
    def push(cls, cwd, message="update: auto commit from Code Aggregator"):
        if not cls.is_repo(cwd):
            return {
                "success": False,
                "stderr": "Git-репозиторий не найден. Выполните git init.",
            }

        root = cls.get_repo_root(cwd)

        status = cls._run(["git", "status", "--porcelain"], root)
        if not status["success"]:
            return status

        has_changes = bool(status["stdout"].strip())

        if has_changes:
            add = cls._run(["git", "add", "."], root)
            if not add["success"]:
                return add

            commit = cls._run(["git", "commit", "-m", message], root)
            if not commit["success"]:
                return commit

        push = cls._run(["git", "push"], root)
        return push
