from pathlib import Path

class StackDetector:
    STACK_SIGNATURES = {
        "React": [".jsx", ".tsx", "vite.config.", "react"],
        "Vue": [".vue", "vue.config."],
        "Angular": [".angular", "angular.json"],
        "Node.js": ["package.json", "node_modules"],
        "Python": ["requirements.txt", "pyproject.toml", ".py"],
        "Kotlin/Android": [".kt", "build.gradle", "AndroidManifest.xml"],
        "Java": [".java", "pom.xml"],
        "Go": [".go", "go.mod"],
        "Rust": [".rs", "Cargo.toml"],
        "Flutter": [".dart", "pubspec.yaml"],
        "HTML/CSS": [".html", ".css"],
    }
    
    @classmethod
    def detect(cls, directory: Path) -> str:
        if not directory.exists():
            return "Unknown"
        
        found = set()
        files = [p.name for p in directory.iterdir() if p.is_file()]
        extensions = set()
        
        for f in files:
            if "." in f:
                ext = f[f.rfind("."):]
                extensions.add(ext.lower())
        
        for stack, signatures in cls.STACK_SIGNATURES.items():
            for sig in signatures:
                if sig.startswith("."):
                    if sig in extensions:
                        found.add(stack)
                        break
                else:
                    if any(sig in name for name in files):
                        found.add(stack)
                        break
        
        return ", ".join(sorted(found)) if found else "Unknown"