"""Project constants."""

# Framework and Language Detection
FRAMEWORK_PATTERNS = {
    "React": [
        "package.json:react",
        "package.json:React",
        "*.jsx",
        "*.tsx",
    ],
    "Vue": [
        "package.json:vue",
        "package.json:Vue",
        "*.vue",
    ],
    "Angular": [
        "package.json:@angular/core",
        "angular.json",
        "*.ts",
    ],
    "FastAPI": [
        "requirements.txt:fastapi",
        "setup.py:fastapi",
        "pyproject.toml:fastapi",
    ],
    "Django": [
        "requirements.txt:django",
        "setup.py:django",
        "manage.py",
    ],
    "Flask": [
        "requirements.txt:flask",
        "setup.py:flask",
    ],
    "Spring Boot": [
        "pom.xml:spring-boot",
        "build.gradle:spring-boot",
    ],
    "Next.js": [
        "package.json:next",
        "next.config.js",
    ],
    "Express": [
        "package.json:express",
    ],
    "Node.js": [
        "package.json",
        "*.js",
    ],
    "Python": [
        "*.py",
        "requirements.txt",
        "setup.py",
    ],
    "Java": [
        "*.java",
        "pom.xml",
        "build.gradle",
    ],
    "Go": [
        "*.go",
        "go.mod",
        "go.sum",
    ],
    "Rust": [
        "Cargo.toml",
        "*.rs",
    ],
    "Docker": [
        "Dockerfile",
        "docker-compose.yml",
    ],
}

# File importance weights
FILE_IMPORTANCE = {
    "README": 10,
    "package.json": 9,
    "requirements.txt": 9,
    "pom.xml": 9,
    "Dockerfile": 8,
    "setup.py": 8,
    "docker-compose.yml": 8,
    "Makefile": 7,
    ".github": 7,
    "go.mod": 9,
    "Cargo.toml": 9,
}

# Common backend markers
BACKEND_INDICATORS = [
    "main.py",
    "app.py",
    "server.py",
    "src/main",
    "src/server",
    "backend",
    "api",
    "service",
    "pom.xml",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "Dockerfile",
]

# Common frontend markers
FRONTEND_INDICATORS = [
    "package.json",
    "src/index.tsx",
    "src/index.jsx",
    "src/index.js",
    "src/App.tsx",
    "src/App.jsx",
    "src/App.js",
    "webpack.config.js",
    "vite.config.js",
    "next.config.js",
    "angular.json",
    "tsconfig.json:paths,compilerOptions,jsx",
]

# API Response Status Messages
STATUS_MESSAGES = {
    "analyzing": "Analyzing repository structure...",
    "cloning": "Cloning repository...",
    "scanning": "Scanning files...",
    "detecting": "Detecting frameworks...",
    "analyzing_ai": "Generating AI analysis...",
    "complete": "Analysis complete",
    "error": "Analysis failed",
}
