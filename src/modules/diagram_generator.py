"""Architecture diagram generation module."""

import logging
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path
import json

from src.utils.config import settings

logger = logging.getLogger(__name__)


def sanitize_node_id(label: str) -> str:
    """
    Sanitize a node label to create a valid Mermaid identifier.
    
    Mermaid requires safe identifiers without spaces or special characters.
    This function converts spaces to underscores and removes problematic characters.
    
    Args:
        label: Original human-readable label (e.g., "FastAPI Backend")
        
    Returns:
        Sanitized identifier safe for Mermaid (e.g., "FastAPI_Backend")
    """
    # Replace spaces with underscores
    sanitized = label.replace(" ", "_")
    # Remove or replace special characters
    sanitized = re.sub(r"[^\w-]", "", sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip("-")
    return sanitized


def validate_mermaid_diagram(mermaid_code: str) -> Tuple[bool, List[str]]:
    """
    Validate Mermaid diagram syntax.
    
    Checks for:
    - Valid diagram declaration (graph, flowchart, etc.)
    - Unique node identifiers
    - Proper class assignments
    - Complete node references in connections
    
    Args:
        mermaid_code: Mermaid diagram source code
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    lines = mermaid_code.strip().split("\n")
    
    if not lines:
        return False, ["Empty diagram"]
    
    # Check for valid diagram declaration
    first_line = lines[0].strip()
    if not re.match(r"^(graph|flowchart|stateDiagram|sequenceDiagram|classDiagram|erDiagram)", first_line):
        errors.append(f"Missing or invalid diagram declaration. First line: '{first_line}'")
    
    # Extract all node IDs that are defined
    defined_nodes = set()
    node_pattern = r"^[\s]*([a-zA-Z_]\w*)"
    
    # Extract all node references in connections
    referenced_nodes = set()
    connection_pattern = r"(--+>?|-->|\||===+)|([\w_]+)"
    
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("classDef") or line.startswith("class "):
            continue
            
        # Check for node definitions
        if "[" in line or "(" in line or "{" in line or "(" in line:
            match = re.match(node_pattern, line)
            if match:
                defined_nodes.add(match.group(1))
        
        # Check for connections and extract referenced nodes
        if "-->" in line or "->" in line or "--" in line:
            parts = re.split(r"-+>?|-+", line)
            for part in parts:
                part = part.strip()
                if part and not part.startswith("|") and not part.startswith("["):
                    node_id = re.match(r"([a-zA-Z_]\w*)", part)
                    if node_id:
                        referenced_nodes.add(node_id.group(1))
    
    # Check for undefined node references
    for node in referenced_nodes:
        if node not in defined_nodes:
            errors.append(f"Referenced node '{node}' is not defined")
    
    return len(errors) == 0, errors


class DiagramNode:
    """Represents a component/node in the architecture diagram."""
    
    def __init__(self, node_id: str, label: str, node_type: str, module_name: str = None):
        """Initialize a diagram node."""
        self.id = node_id
        self.label = label
        self.type = node_type  # e.g., 'frontend', 'backend', 'database', 'config'
        self.module_name = module_name
    
    def __repr__(self):
        return f"DiagramNode({self.id}, {self.label}, {self.type})"


class DiagramEdge:
    """Represents a connection between components."""
    
    def __init__(self, source_id: str, target_id: str, label: str = ""):
        """Initialize a diagram edge."""
        self.source = source_id
        self.target = target_id
        self.label = label
    
    def __repr__(self):
        return f"DiagramEdge({self.source} -> {self.target})"


class ArchitectureGraph:
    """Represents the complete architecture graph."""
    
    def __init__(self, repo_name: str):
        """Initialize the architecture graph."""
        self.repo_name = repo_name
        self.nodes: List[DiagramNode] = []
        self.edges: List[DiagramEdge] = []
        self.node_map: Dict[str, DiagramNode] = {}
    
    def add_node(self, node: DiagramNode) -> None:
        """Add a node to the graph."""
        if node.id not in self.node_map:
            self.nodes.append(node)
            self.node_map[node.id] = node
    
    def add_edge(self, edge: DiagramEdge) -> None:
        """Add an edge to the graph."""
        # Only add edge if both nodes exist
        if edge.source in self.node_map and edge.target in self.node_map:
            self.edges.append(edge)
    
    def add_connection(self, source_id: str, target_id: str, label: str = "") -> None:
        """Add a connection between two nodes."""
        edge = DiagramEdge(source_id, target_id, label)
        self.add_edge(edge)


class ArchitectureDiagramGenerator:
    """Generates architecture diagrams from repository metadata."""
    
    def __init__(self):
        """Initialize the diagram generator."""
        self.output_path = Path(settings.DIAGRAM_OUTPUT_PATH)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_diagrams(self, metadata: Dict) -> Dict:
        """
        Generate architecture diagrams from repository metadata.
        
        Args:
            metadata: Repository metadata from metadata builder
            
        Returns:
            Dictionary containing generated diagrams
        """
        logger.info(f"Generating architecture diagrams for {metadata['repository']['name']}")
        
        try:
            # Build the architecture graph
            graph = self._build_graph(metadata)
            
            # Generate diagrams
            diagrams = {
                "mermaid": self._generate_mermaid(graph) if settings.GENERATE_MERMAID else None,
                "graphviz": self._generate_graphviz(graph) if settings.GENERATE_GRAPHVIZ else None,
                "json": self._generate_json(graph),
            }
            
            # Store diagrams
            self._store_diagrams(metadata['repository']['name'], diagrams)
            
            logger.info("Diagram generation completed successfully")
            return diagrams
        
        except Exception as e:
            logger.error(f"Error generating diagrams: {e}")
            raise ValueError(f"Failed to generate diagrams: {str(e)}")
    
    def _build_graph(self, metadata: Dict) -> ArchitectureGraph:
        """
        Build an architecture graph from metadata.
        
        Detects and creates nodes for:
        - Client/Frontend layer
        - API Gateway (if applicable)
        - Service/Business Logic layer
        - Data/Database layer
        - External Integrations
        
        Args:
            metadata: Repository metadata
            
        Returns:
            ArchitectureGraph instance
        """
        graph = ArchitectureGraph(metadata['repository']['name'])
        
        analysis = metadata['analysis']
        frameworks = metadata.get('frameworks', {})
        modules = metadata.get('modules', [])
        
        # === LAYER 1: CLIENT/FRONTEND ===
        if analysis.get('has_frontend'):
            client_node = DiagramNode(
                "client",
                "Client / UI",
                "frontend",
                "frontend"
            )
            graph.add_node(client_node)
            
            # Add specific frontend frameworks
            frontend_frameworks = self._get_frameworks_by_category(frameworks, ['react', 'vue', 'angular', 'next', 'svelte', 'nuxt'])
            for framework in frontend_frameworks:
                fw_node = DiagramNode(
                    f"fw_{framework.lower().replace('.', '_').replace('+', 'plus')}",
                    framework,
                    "framework",
                    framework
                )
                graph.add_node(fw_node)
                graph.add_connection("client", fw_node.id, "uses")
        
        # === LAYER 2: API GATEWAY ===
        if analysis.get('has_backend'):
            # Create API Gateway node only if we have both frontend and backend
            if analysis.get('has_frontend'):
                api_node = DiagramNode(
                    "api_gateway",
                    "API Gateway",
                    "backend",
                    "api_gateway"
                )
                graph.add_node(api_node)
                if "client" in graph.node_map:
                    graph.add_connection("client", "api_gateway", "HTTP/REST")
            
            # === LAYER 3: SERVICES/BUSINESS LOGIC ===
            backend_node = DiagramNode(
                "services",
                "Services & Logic",
                "backend",
                "services"
            )
            graph.add_node(backend_node)
            
            if analysis.get('has_frontend'):
                graph.add_connection("api_gateway", "services", "routes")
            
            # Add backend frameworks
            backend_frameworks = self._get_frameworks_by_category(
                frameworks, 
                ['fastapi', 'django', 'flask', 'express', 'spring', 'laravel', 'asp.net']
            )
            for framework in backend_frameworks:
                fw_node = DiagramNode(
                    f"bw_{framework.lower().replace('.', '_').replace('+', 'plus').replace(' ', '_')}",
                    framework,
                    "framework",
                    framework
                )
                graph.add_node(fw_node)
                graph.add_connection("services", fw_node.id, "uses")
            
            # Add service modules from metadata
            service_modules = [m for m in modules if 'service' in m.get('type', '').lower() or 'handler' in m.get('type', '').lower()]
            for i, svc_module in enumerate(service_modules[:4]):
                svc_id = f"service_{i+1}"
                svc_node = DiagramNode(
                    svc_id,
                    svc_module.get('name', f'Service {i+1}'),
                    "backend",
                    svc_module['name']
                )
                graph.add_node(svc_node)
                graph.add_connection("services", svc_id, "contains")
        
        # === LAYER 4: DATA/DATABASE ===
        if analysis.get('has_backend'):
            has_db = self._detect_database(metadata)
            if has_db:
                db_node = DiagramNode("database", "Database", "database", "database")
                graph.add_node(db_node)
                graph.add_connection("services", "database", "queries")
                
                # Add ORM/database frameworks
                db_frameworks = self._get_frameworks_by_category(
                    frameworks,
                    ['sqlalchemy', 'django orm', 'prisma', 'typeorm', 'mongodb', 'postgres', 'mysql', 'hibernate', 'jdbc']
                )
                for db_fw in db_frameworks:
                    db_fw_node = DiagramNode(
                        f"db_{db_fw.lower().replace(' ', '_')}",
                        db_fw,
                        "framework",
                        db_fw
                    )
                    graph.add_node(db_fw_node)
                    graph.add_connection("database", db_fw_node.id, "uses")
        
        # === LAYER 5: EXTERNAL INTEGRATIONS ===
        integrations = self._detect_integrations(metadata)
        for ext_service in integrations:
            ext_node = DiagramNode(
                f"ext_{ext_service.lower().replace(' ', '_')}",
                ext_service,
                "infrastructure",
                ext_service
            )
            graph.add_node(ext_node)
            
            # Connect to services if available
            if "services" in graph.node_map:
                graph.add_connection("services", ext_node.id, "calls")
        
        # === LAYER 6: INFRASTRUCTURE ===
        if self._detect_docker(metadata):
            docker_node = DiagramNode("docker", "Docker", "infrastructure", "docker")
            graph.add_node(docker_node)
            if "services" in graph.node_map:
                graph.add_connection("services", "docker", "containerized")
        
        if self._detect_kubernetes(metadata):
            k8s_node = DiagramNode("kubernetes", "Kubernetes", "infrastructure", "kubernetes")
            graph.add_node(k8s_node)
            if "docker" in graph.node_map:
                graph.add_connection("docker", "kubernetes", "orchestrates")
        
        if self._detect_ci_cd(metadata):
            cicd_node = DiagramNode("cicd", "CI/CD Pipeline", "infrastructure", "cicd")
            graph.add_node(cicd_node)
            if "services" in graph.node_map:
                graph.add_connection("services", "cicd", "builds")
        
        return graph
    
    def _get_frameworks_by_category(self, frameworks: Dict, category_keywords: List[str]) -> List[str]:
        """Get frameworks matching category keywords, sorted by confidence."""
        matching = []
        for framework, info in frameworks.items():
            conf = info.get('confidence', 0)
            if conf >= 0.5 and any(kw.lower() in framework.lower() for kw in category_keywords):
                matching.append(framework)
        
        # Sort by confidence descending
        return sorted(
            matching,
            key=lambda f: frameworks[f].get('confidence', 0),
            reverse=True
        )[:3]
    
    def _detect_integrations(self, metadata: Dict) -> List[str]:
        """Detect external service/API integrations."""
        integrations = []
        
        # Check for API integrations in dependencies
        api_keywords = ['requests', 'aiohttp', 'httpx', 'axios', 'fetch', 'stripe', 'twilio', 'sendgrid', 'aws', 'gcp']
        deps_text = json.dumps(metadata.get('dependencies', {})).lower()
        
        if 'stripe' in deps_text:
            integrations.append('Stripe')
        if 'twilio' in deps_text:
            integrations.append('Twilio')
        if 'sendgrid' in deps_text or 'mailgun' in deps_text:
            integrations.append('Email Service')
        if 'boto3' in deps_text or 's3' in deps_text:
            integrations.append('AWS S3')
        if 'firebase' in deps_text:
            integrations.append('Firebase')
        if 'redis' in deps_text:
            integrations.append('Redis Cache')
        
        return integrations
    
    def _detect_database(self, metadata: Dict) -> bool:
        """Detect if a database is likely used."""
        # Check for database-related frameworks
        db_indicators = [
            "SQLAlchemy", "Django ORM", "Prisma", "TypeORM",
            "Hibernate", "JDBC", "MongoDB", "PostgreSQL", "MySQL",
            "MariaDB", "Redis", "Cassandra", "DynamoDB"
        ]
        
        frameworks = metadata.get('frameworks', {})
        dependencies_text = json.dumps(metadata.get('dependencies', {})).lower()
        
        for indicator in db_indicators:
            if indicator.lower() in dependencies_text or any(
                ind.lower() in fwk.lower() for fwk in frameworks.keys() for ind in db_indicators
            ):
                return True
        
        # Check for common database files
        for file in metadata.get('root_files', []):
            if any(pattern in file.lower() for pattern in ['migration', 'schema', 'alembic', 'flyway']):
                return True
        
        return False
    
    def _detect_docker(self, metadata: Dict) -> bool:
        """Check if Docker is used in the project."""
        root_files = metadata.get('repository', {}).get('root_files', [])
        return any('dockerfile' in f.lower() for f in root_files)
    
    def _detect_kubernetes(self, metadata: Dict) -> bool:
        """Check if Kubernetes is used in the project."""
        root_files = metadata.get('repository', {}).get('root_files', [])
        return any(
            pattern in ' '.join(root_files).lower()
            for pattern in ['k8s', 'kubernetes', 'helm', 'kustomize']
        )
    
    def _detect_ci_cd(self, metadata: Dict) -> bool:
        """Check if CI/CD is configured in the project."""
        root_files = metadata.get('repository', {}).get('root_files', [])
        files_lower = [f.lower() for f in root_files]
        
        ci_patterns = [
            '.github/workflows',
            '.gitlab-ci.yml',
            'jenkinsfile',
            '.circleci',
            'travis.yml',
            'appveyor.yml',
            '.drone.yml',
            'azure-pipelines.yml'
        ]
        
        return any(pattern in ' '.join(files_lower) for pattern in ci_patterns)
    
    def _generate_mermaid(self, graph: ArchitectureGraph) -> str:
        """
        Generate Mermaid diagram syntax with proper styling.
        
        Creates a valid Mermaid diagram with:
        - Sanitized node identifiers
        - Human-readable labels
        - Applied style classes to all nodes
        - Proper class definitions
        
        Args:
            graph: ArchitectureGraph instance
            
        Returns:
            Mermaid diagram text (plain syntax, not wrapped in Markdown)
        """
        lines = ["graph TD"]
        
        # Track nodes and their sanitized IDs
        node_id_map = {}  # Maps original ID to sanitized ID
        node_types = {}   # Maps sanitized ID to node type
        
        # Add node definitions with sanitized IDs and readable labels
        node_styles = {
            "frontend": "[{}]",
            "backend": "[{}]",
            "database": "[{}]",
            "framework": "[{}]",
            "infrastructure": "[{}]",
            "application": "[{}]",
        }
        
        for node in graph.nodes:
            # Sanitize the node ID
            sanitized_id = sanitize_node_id(node.id)
            node_id_map[node.id] = sanitized_id
            node_types[sanitized_id] = node.type
            
            # Use node style or default
            style_template = node_styles.get(node.type, "[{}]")
            style = style_template.format(node.label)
            
            # Add node definition with sanitized ID and readable label
            lines.append(f"    {sanitized_id}{style}")
        
        # Add connections using sanitized IDs
        for edge in graph.edges:
            source_sanitized = node_id_map.get(edge.source, sanitize_node_id(edge.source))
            target_sanitized = node_id_map.get(edge.target, sanitize_node_id(edge.target))
            
            if edge.label:
                lines.append(f"    {source_sanitized} -->|{edge.label}| {target_sanitized}")
            else:
                lines.append(f"    {source_sanitized} --> {target_sanitized}")
        
        # Add style class definitions
        lines.append("")
        lines.append("    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px,color:#000")
        lines.append("    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000")
        lines.append("    classDef database fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000")
        lines.append("    classDef framework fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000")
        lines.append("    classDef infrastructure fill:#eceff1,stroke:#263238,stroke-width:2px,color:#000")
        lines.append("    classDef application fill:#f5f5f5,stroke:#424242,stroke-width:2px,color:#000")
        
        # Apply classes to nodes
        lines.append("")
        for sanitized_id, node_type in node_types.items():
            node_class = node_type if node_type in ["frontend", "backend", "database", "framework", "infrastructure", "application"] else "application"
            lines.append(f"    class {sanitized_id} {node_class}")
        
        mermaid_code = "\n".join(lines)
        
        # Validate the generated diagram
        is_valid, errors = validate_mermaid_diagram(mermaid_code)
        if not is_valid:
            logger.warning(f"Mermaid validation errors: {errors}")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return mermaid_code
    
    def _generate_graphviz(self, graph: ArchitectureGraph) -> str:
        """
        Generate Graphviz DOT diagram syntax.
        
        Args:
            graph: ArchitectureGraph instance
            
        Returns:
            Graphviz DOT format string
        """
        lines = [
            "digraph ArchitectureDiagram {",
            "    rankdir=TB;",
            '    node [shape=box, style="rounded,filled", fillcolor=lightblue];',
            ""
        ]
        
        # Define node styles
        node_colors = {
            "frontend": "lightblue",
            "backend": "lightpink",
            "database": "lightgreen",
            "framework": "lightyellow",
            "infrastructure": "lightcyan",
            "application": "white",
        }
        
        # Add node definitions
        for node in graph.nodes:
            color = node_colors.get(node.type, "lightgray")
            lines.append(f'    "{node.id}" [label="{node.label}", fillcolor={color}];')
        
        lines.append("")
        
        # Add edges
        for edge in graph.edges:
            if edge.label:
                lines.append(f'    "{edge.source}" -> "{edge.target}" [label="{edge.label}"];')
            else:
                lines.append(f'    "{edge.source}" -> "{edge.target}";')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_json(self, graph: ArchitectureGraph) -> str:
        """
        Generate JSON representation of the architecture graph.
        
        Args:
            graph: ArchitectureGraph instance
            
        Returns:
            JSON string representation
        """
        graph_dict = {
            "name": graph.repo_name,
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.type,
                    "module": node.module_name,
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                }
                for edge in graph.edges
            ],
        }
        
        return json.dumps(graph_dict, indent=2)
    
    def _store_diagrams(self, repo_name: str, diagrams: Dict) -> None:
        """
        Store generated diagrams to disk.
        
        Stores diagrams in plain format for API consumption:
        - Mermaid: Plain .mmd format (not Markdown wrapped)
        - Graphviz: Plain .dot format
        - JSON: Plain JSON format
        
        Args:
            repo_name: Name of the repository
            diagrams: Dictionary of generated diagrams
        """
        try:
            # Create repository-specific directory
            repo_dir = self.output_path / repo_name.replace("/", "_")
            repo_dir.mkdir(parents=True, exist_ok=True)
            
            # Store Mermaid diagram (plain syntax, not Markdown wrapped)
            if diagrams.get("mermaid"):
                mermaid_file = repo_dir / "architecture.mmd"
                with open(mermaid_file, "w") as f:
                    f.write(diagrams["mermaid"])
                logger.debug(f"Stored Mermaid diagram at {mermaid_file}")
            
            # Store Graphviz diagram
            if diagrams.get("graphviz"):
                graphviz_file = repo_dir / "architecture.dot"
                with open(graphviz_file, "w") as f:
                    f.write(diagrams["graphviz"])
                logger.debug(f"Stored Graphviz diagram at {graphviz_file}")
            
            # Store JSON representation
            if diagrams.get("json"):
                json_file = repo_dir / "architecture.json"
                with open(json_file, "w") as f:
                    f.write(diagrams["json"])
                logger.debug(f"Stored JSON diagram at {json_file}")
        
        except Exception as e:
            logger.warning(f"Failed to store diagrams: {e}")
    
    def get_stored_diagram(self, repo_name: str, format: str = "mermaid") -> str:
        """
        Retrieve a previously stored diagram.
        
        Returns plain diagram syntax (not wrapped in Markdown).
        
        Args:
            repo_name: Name of the repository
            format: Diagram format ('mermaid', 'graphviz', or 'json')
            
        Returns:
            Plain diagram content as string
            
        Raises:
            FileNotFoundError: If diagram file not found
            ValueError: If diagram validation fails
        """
        repo_dir = self.output_path / repo_name.replace("/", "_")
        
        if format == "mermaid":
            # Try new .mmd format first, fall back to .md for backwards compatibility
            file_path = repo_dir / "architecture.mmd"
            if not file_path.exists():
                file_path = repo_dir / "architecture.md"
        elif format == "graphviz":
            file_path = repo_dir / "architecture.dot"
        elif format == "json":
            file_path = repo_dir / "architecture.json"
        else:
            raise ValueError(f"Unknown diagram format: {format}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Diagram not found: {file_path}")
        
        with open(file_path, "r") as f:
            content = f.read()
        
        # For Mermaid format, extract plain syntax if Markdown-wrapped (backwards compatibility)
        if format == "mermaid" and file_path.suffix == ".md":
            # Extract from Markdown code block
            match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
            if match:
                content = match.group(1)
        
        # Validate Mermaid diagrams
        if format == "mermaid":
            is_valid, errors = validate_mermaid_diagram(content)
            if not is_valid:
                logger.warning(f"Retrieved Mermaid diagram has validation issues: {errors}")
        
        return content
