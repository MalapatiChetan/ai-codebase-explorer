"""Framework and technology detection module."""

import json
import logging
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Dict, List, Set
from src.utils.constants import FRAMEWORK_PATTERNS

logger = logging.getLogger(__name__)


class FrameworkDetector:
    """Detects frameworks, languages, and technologies in a repository."""
    
    def __init__(self):
        """Initialize the detector."""
        self.detected_frameworks = {}
        self.detected_languages = {}
    
    def _parse_package_json(self, repo_path: Path) -> Set[str]:
        """Parse package.json and extract dependency names."""
        packages = set()
        package_file = repo_path / "package.json"
        
        if not package_file.exists():
            return packages
        
        try:
            with open(package_file, "r") as f:
                data = json.load(f)
                # Check both dependencies and devDependencies
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                packages.update(deps.keys())
                packages.update(dev_deps.keys())
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        
        return packages
    
    def _parse_requirements_txt(self, repo_path: Path) -> Set[str]:
        """Parse requirements.txt and extract package names."""
        packages = set()
        req_file = repo_path / "requirements.txt"
        
        if not req_file.exists():
            return packages
        
        try:
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Extract package name (before ==, >=, <=, >, <, etc.)
                    package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("[")[0].strip()
                    if package_name:
                        packages.add(package_name.lower())
        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")
        
        return packages
    
    def _parse_pyproject_toml(self, repo_path: Path) -> Set[str]:
        """Parse pyproject.toml and extract dependencies."""
        packages = set()
        pyproject_file = repo_path / "pyproject.toml"
        
        if not pyproject_file.exists():
            return packages
        
        try:
            import toml
            with open(pyproject_file, "r") as f:
                data = toml.load(f)
                # Check poetry dependencies
                if "tool" in data and "poetry" in data["tool"]:
                    deps = data["tool"]["poetry"].get("dependencies", {})
                    for key in deps.keys():
                        if key != "python":
                            packages.add(key.lower())
                # Check setuptools dependencies
                if "project" in data:
                    deps = data["project"].get("dependencies", [])
                    for dep in deps:
                        pkg_name = dep.split(";")[0].split("[")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("==")[0].split("!=")[0].strip()
                        if pkg_name:
                            packages.add(pkg_name.lower())
        except ImportError:
            logger.debug("toml module not available, skipping pyproject.toml parsing")
        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml: {e}")
        
        return packages
    
    def _parse_pom_xml(self, repo_path: Path) -> Set[str]:
        """Parse pom.xml and extract dependency artifact IDs."""
        packages = set()
        pom_file = repo_path / "pom.xml"
        
        if not pom_file.exists():
            return packages
        
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            # Handle XML namespaces
            namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
            
            # Find all dependency artifactIds
            for dep in root.findall(".//m:artifactId", namespace):
                if dep.text:
                    packages.add(dep.text.lower())
            # Also try without namespace
            if not packages:
                for dep in root.findall(".//artifactId"):
                    if dep.text:
                        packages.add(dep.text.lower())
        except Exception as e:
            logger.debug(f"Error parsing pom.xml: {e}")
        
        return packages
    
    def _parse_build_gradle(self, repo_path: Path) -> Set[str]:
        """Parse build.gradle and extract dependencies using regex."""
        packages = set()
        gradle_file = repo_path / "build.gradle"
        
        if not gradle_file.exists():
            return packages
        
        try:
            with open(gradle_file, "r") as f:
                content = f.read()
                # Find dependencies block and extract artifacts
                # Pattern: 'groupId:artifactId' or "groupId:artifactId"
                matches = re.findall(r'[\'"]([a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+)[\'"]', content)
                for match in matches:
                    artifact = match.split(":")[-1].lower()  # Take artifact part after last :
                    packages.add(artifact)
        except Exception as e:
            logger.debug(f"Error parsing build.gradle: {e}")
        
        return packages
    
    def _parse_go_mod(self, repo_path: Path) -> Set[str]:
        """Parse go.mod and extract module names."""
        packages = set()
        gomod_file = repo_path / "go.mod"
        
        if not gomod_file.exists():
            return packages
        
        try:
            with open(gomod_file, "r") as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    if line.startswith("require"):
                        in_require = True
                        continue
                    if in_require:
                        if line.startswith("("):
                            continue
                        if line.startswith(")"):
                            break
                        if line:
                            # Extract module name (before version)
                            parts = line.split()
                            if parts:
                                packages.add(parts[0].lower())
        except Exception as e:
            logger.debug(f"Error parsing go.mod: {e}")
        
        return packages
    
    def detect_frameworks(self, repo_path: Path, repo_metadata: Dict) -> Dict:
        """
        Detect frameworks and technologies by parsing dependency files.
        
        Args:
            repo_path: Path to the repository  
            repo_metadata: Dictionary containing repository scan metadata
            
        Returns:
            Dictionary with detected frameworks and confidence scores
        """
        detected = {}
        
        # Parse all dependency files
        npm_packages = self._parse_package_json(repo_path)
        python_packages = self._parse_requirements_txt(repo_path) | self._parse_pyproject_toml(repo_path)
        maven_packages = self._parse_pom_xml(repo_path)
        gradle_packages = self._parse_build_gradle(repo_path)
        go_modules = self._parse_go_mod(repo_path)
        
        # Combine all packages
        all_packages = npm_packages | python_packages | maven_packages | gradle_packages | go_modules
        
        # Prepare file data for extension/file name matching
        files = {f["name"].lower(): f for f in repo_metadata.get("files", [])}
        root_files = {f.lower(): f for f in repo_metadata.get("root_files", [])}
        file_paths = {f["path"].lower(): f for f in repo_metadata.get("files", [])}
        languages = repo_metadata.get("languages", {})
        
        # Check each framework pattern
        for framework, patterns in FRAMEWORK_PATTERNS.items():
            confidence = 0
            matched_patterns = []
            
            for pattern in patterns:
                if ":" in pattern:
                    # Dependency pattern (e.g., "package.json:react")
                    file_type, package_name = pattern.split(":", 1)
                    package_name_lower = package_name.lower()
                    
                    # Check if package was found in parsed dependencies
                    if package_name_lower in all_packages:
                        confidence = 0.8  # High confidence for actual dependency match
                        matched_patterns.append(pattern)
                
                elif pattern.startswith("*."):
                    # File extension pattern
                    ext = pattern[1:].lower()
                    if ext in languages or any(f["extension"].lower() == pattern.lower() 
                                              for f in repo_metadata.get("files", [])):
                        confidence += 0.15
                        matched_patterns.append(pattern)
                
                else:
                    # File name pattern
                    if pattern.lower() in root_files or pattern.lower() in files:
                        confidence += 0.3
                        matched_patterns.append(pattern)
                    elif any(pattern.lower() in path for path in file_paths.keys()):
                        confidence += 0.15
                        matched_patterns.append(pattern)
            
            if confidence > 0:
                detected[framework] = {
                    "confidence": min(confidence, 1.0),
                    "matched_patterns": matched_patterns,
                }
        
        return detected
    
    def get_primary_language(self, repo_metadata: Dict) -> str:
        """
        Determine the primary programming language of the repository.
        
        Args:
            repo_metadata: Repository metadata
            
        Returns:
            Primary language name
        """
        languages = repo_metadata.get("languages", {})
        
        if not languages:
            return "Unknown"
        
        # Language to extension mapping
        lang_map = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "jsx": "JavaScript/React",
            "tsx": "TypeScript/React",
            "java": "Java",
            "go": "Go",
            "rs": "Rust",
            "php": "PHP",
            "rb": "Ruby",
            "cs": "C#",
            "cpp": "C++",
            "c": "C",
            "sh": "Shell",
            "scala": "Scala",
            "kt": "Kotlin",
        }
        
        sorted_langs = sorted(
            languages.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        if sorted_langs:
            primary_ext = sorted_langs[0][0]
            return lang_map.get(primary_ext, primary_ext.upper())
        
        return "Unknown"
    
    def detect_architecture_patterns(self, repo_metadata: Dict) -> List[str]:
        """
        Detect potential architecture patterns.
        
        Args:
            repo_metadata: Repository metadata
            
        Returns:
            List of detected architecture patterns
        """
        patterns = []
        files = {f["path"].lower(): f for f in repo_metadata.get("files", [])}
        root_files_lower = {f.lower(): f for f in repo_metadata.get("root_files", [])}
        
        # Microservices patterns
        if any(f in root_files_lower for f in 
               ["docker-compose.yml", "docker-compose.yaml", "docker-compose.json"]):
            patterns.append("Microservices/Docker-based")
        
        # API-first patterns
        if any("api" in path for path in files.keys()):
            patterns.append("API-First")
        
        # MVC pattern
        if any("controller" in path or "model" in path or "view" in path 
               for path in files.keys()):
            patterns.append("MVC")
        
        # Monolithic pattern
        if repo_metadata.get("has_backend") and repo_metadata.get("has_frontend"):
            patterns.append("Monolithic")
        
        # Serverless patterns
        if any("serverless.yml" in path or "lambda" in path for path in files.keys()):
            patterns.append("Serverless")
        
        # Plugin architecture
        if any("plugin" in path for path in files.keys()):
            patterns.append("Plugin-based")
        
        return patterns
    
    def get_tech_stack(self, detected_frameworks: Dict, primary_language: str) -> List[str]:
        """
        Build a technology stack from detected frameworks.
        
        Args:
            detected_frameworks: Dictionary of detected frameworks
            primary_language: Primary programming language
            
        Returns:
            List of technologies in the stack
        """
        stack = [primary_language] if primary_language != "Unknown" else []
        
        # Add frameworks sorted by confidence
        sorted_frameworks = sorted(
            detected_frameworks.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        )
        
        for framework, info in sorted_frameworks:
            if info["confidence"] >= 0.3:
                stack.append(framework)
        
        return stack
    
    def analyze_dependencies(self, repo_path: Path, repo_metadata: Dict) -> Dict:
        """
        Analyze dependency files to get more insight into tech stack.
        
        Args:
            repo_path: Path to repository
            repo_metadata: Repository metadata
            
        Returns:
            Dictionary with dependency information
        """
        dependencies = {
            "package.json": [],
            "requirements.txt": [],
            "pom.xml": [],
            "go.mod": [],
            "Cargo.toml": [],
        }
        
        root_files = {f.lower(): repo_path / f for f in repo_metadata.get("root_files", [])}
        
        # Parse package.json
        if "package.json" in root_files:
            try:
                with open(root_files["package.json"], "r") as f:
                    data = json.load(f)
                    deps = list(data.get("dependencies", {}).keys())[:5]
                    dependencies["package.json"] = deps
            except Exception as e:
                logger.warning(f"Error parsing package.json: {e}")
        
        # Parse requirements.txt
        if "requirements.txt" in root_files:
            try:
                with open(root_files["requirements.txt"], "r") as f:
                    deps = [line.strip().split("==")[0] for line in f.readlines() 
                           if line.strip() and not line.startswith("#")][:5]
                    dependencies["requirements.txt"] = deps
            except Exception as e:
                logger.warning(f"Error parsing requirements.txt: {e}")
        
        return {k: v for k, v in dependencies.items() if v}
    
    def get_service_count_estimate(self, repo_metadata: Dict) -> int:
        """
        Estimate number of services based on structure.
        
        Args:
            repo_metadata: Repository metadata
            
        Returns:
            Estimated number of services
        """
        services = 0
        files = {f["path"].lower(): f for f in repo_metadata.get("files", [])}
        
        # Look for service indicators
        service_indicators = ["service", "handler", "main", "server"]
        found_services = set()
        
        for path in files.keys():
            for indicator in service_indicators:
                if indicator in path and path.startswith("src/"):
                    # Extract potential service name from path
                    parts = path.split("/")
                    if len(parts) >= 3:
                        found_services.add(parts[1])
        
        return max(1, len(found_services))
