"""Architecture question answering module for repository Q&A."""

import logging
import re
from enum import Enum
from typing import Dict, Optional, List, Tuple, NamedTuple
from google import genai
from src.utils.config import settings
from src.utils.prompt_budget import create_budget, trim_code_snippets, estimate_tokens
from src.modules.code_indexer import CodeChunk

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Intent categories for architecture questions."""
    PROJECT_OVERVIEW = "project_overview"      # What is this? What does it do?
    ARCHITECTURE = "architecture"               # How is it structured? Architecture diagram?
    TECH_STACK = "tech_stack"                  # What technologies? What frameworks?
    COMPONENTS = "components"                   # What are the components/modules?
    DATA_FLOW = "data_flow"                    # How does data flow? Request/response?
    DEPLOYMENT = "deployment"                  # How is it deployed? Scaling?
    DEPENDENCIES = "dependencies"               # What depends on what?
    GENERAL = "general"                        # Other questions


class IntentMatch(NamedTuple):
    """Result of intent matching."""
    intent: QueryIntent
    confidence: float  # 0.0 to 1.0



class ArchitectureQueryAnswerer:
    """Answers questions about repository architecture using AI or rule-based approaches."""
    
    def __init__(self):
        """Initialize the query answerer with AI capability detection."""
        # Check if AI is usable using the new helper
        self.ai_usable = settings.is_ai_usable()
        
        if self.ai_usable:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            self.google_model = getattr(settings, "GOOGLE_MODEL", "gemini-1.5-flash")
            self.google_temperature = getattr(settings, "GOOGLE_TEMPERATURE", 0.7)
            logger.info(f"✓ AI (Gemini) enabled. Model: {self.google_model}, Temperature: {self.google_temperature}")
        else:
            self.client = None
            # Log the specific reason for AI being unavailable
            reason = settings.get_ai_disabled_reason()
            logger.warning(f"⚠ AI disabled: {reason}. Using rule-based Q&A only.")
        
        # Initialize RAG for code-based context (available even with rule-based mode)
        self.rag_enabled = settings.ENABLE_RAG
        self.rag_store = None  # Will be set per question
        
        if self.rag_enabled:
            logger.debug("RAG (semantic search) is enabled for enhanced context retrieval")
    
    def _init_rag_for_repo(self, metadata: Dict) -> Optional['RAGVectorStore']:
        """Initialize RAG for a specific repository.
        
        Args:
            metadata: Repository metadata
            
        Returns:
            RAGVectorStore if available, None otherwise
        """
        if not self.rag_enabled:
            return None
        
        try:
            # Import RAG on-demand to avoid slow initialization at startup
            from src.modules.rag_vector_store import RAGVectorStore

            repo = metadata.get("repository", {})
            repo_name = repo.get("name")
            commit_sha = repo.get("git_commit")
            rag_store = RAGVectorStore(repo_name, commit_sha=commit_sha)

            if not rag_store.is_available():
                return None

            if commit_sha:
                if rag_store.vector_store.has_commit_index(repo_name, commit_sha):
                    return rag_store
                logger.debug(f"No commit-aware RAG index found for {repo_name}@{commit_sha[:8]}")
                return None

            if rag_store.load_index():
                return rag_store
        except Exception as e:
            repo_name = metadata.get("repository", {}).get("name", "unknown")
            logger.debug(f"Could not load RAG index for {repo_name}: {e}")
        
        return None
    
    def _detect_intent(self, question: str) -> IntentMatch:
        """Detect the intent of the user's question.
        
        Args:
            question: User's question about the codebase
            
        Returns:
            IntentMatch with detected intent and confidence score
        """
        q = question.lower().strip()
        
        # Project overview patterns
        overview_patterns = [
            r"^what\s+is\s+this",
            r"what\s+(does|can)\s+this",
            r"overview",
            r"what.*project",
            r"what.*repository"
        ]
        for pattern in overview_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.PROJECT_OVERVIEW, 0.95)
        
        # Architecture patterns
        arch_patterns = [
            r"how\s+is\s+it\s+(structured|organized|architected)",
            r"architecture",
            r"system\s+design",
            r"diagram",
            r"folder\s+structure"
        ]
        for pattern in arch_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.ARCHITECTURE, 0.95)
        
        # Tech stack patterns
        stack_patterns = [
            r"what.*technolog",
            r"what.*stack",
            r"tech\s+stack",
            r"built\s+with",
            r"uses?\s+(which|what)"
        ]
        for pattern in stack_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.TECH_STACK, 0.95)
        
        # Components/modules patterns
        component_patterns = [
            r"component",
            r"module",
            r"part",
            r"layer",
            r"service",
            r"what\s+does\s+each",
            r"what.*contain"
        ]
        for pattern in component_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.COMPONENTS, 0.90)
        
        # Data flow patterns
        flow_patterns = [
            r"data\s+flow",
            r"request.*response",
            r"how\s+data",
            r"flow\s+through",
            r"from.*to",
            r"process"
        ]
        for pattern in flow_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.DATA_FLOW, 0.85)
        
        # Deployment patterns
        deploy_patterns = [
            r"deploy",
            r"production",
            r"docker",
            r"kubernetes",
            r"scaling",
            r"how.*run"
        ]
        for pattern in deploy_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.DEPLOYMENT, 0.90)
        
        # Dependencies patterns
        depend_patterns = [
            r"depend",
            r"package",
            r"library",
            r"require",
            r"import",
            r"npm|pip|maven"
        ]
        for pattern in depend_patterns:
            if re.search(pattern, q):
                return IntentMatch(QueryIntent.DEPENDENCIES, 0.90)
        
        # Default to general
        return IntentMatch(QueryIntent.GENERAL, 0.5)
    
    def _answer_by_intent(self, intent: QueryIntent, metadata: Dict, 
                         question: str) -> str:
        """Generate answer based on detected intent.
        
        Args:
            intent: Detected query intent
            metadata: Repository metadata
            question: Original question
            
        Returns:
            Answer string tailored to the intent
        """
        repo_name = metadata['repository']['name']
        analysis = metadata['analysis']
        
        if intent == QueryIntent.PROJECT_OVERVIEW:
            return self._answer_project_overview(metadata)
        elif intent == QueryIntent.ARCHITECTURE:
            return self._answer_architecture(metadata)
        elif intent == QueryIntent.TECH_STACK:
            return self._answer_tech_stack(metadata)
        elif intent == QueryIntent.COMPONENTS:
            return self._answer_components(metadata)
        elif intent == QueryIntent.DATA_FLOW:
            return self._answer_data_flow(metadata, question)
        elif intent == QueryIntent.DEPLOYMENT:
            return self._answer_deployment(metadata)
        elif intent == QueryIntent.DEPENDENCIES:
            return self._answer_dependencies(metadata)
        else:
            return self._answer_general(metadata, question)
    
    def _answer_project_overview(self, metadata: Dict) -> str:
        """Answer 'What is this project?' type questions."""
        name = metadata['repository']['name']
        analysis = metadata['analysis']
        
        # Determine project type from components
        has_backend = analysis.get('has_backend', False)
        has_frontend = analysis.get('has_frontend', False)
        
        if has_backend and has_frontend:
            project_type = "a full-stack web application"
        elif has_frontend:
            project_type = "a frontend application"
        elif has_backend:
            project_type = "a backend service"
        else:
            project_type = "a library or utility"
        
        lang = analysis.get('primary_language', 'unknown')
        file_count = analysis.get('file_count', 0)
        
        frameworks = metadata.get('frameworks', {})
        framework_list = list(frameworks.keys())[:2]
        framework_text = f" built with {', '.join(framework_list)}" if framework_list else ""
        
        return f"{name} is {project_type}{framework_text} written in {lang}. " \
               f"It contains {file_count} files organized into logical modules with clear separation of concerns."
    
    def _answer_architecture(self, metadata: Dict) -> str:
        """Answer 'How is it structured?' type questions."""
        modules = metadata.get('modules', [])
        patterns = metadata.get('architecture_patterns', [])
        
        answer = f"**Architectural Structure:**\n\n"
        
        if modules:
            answer += "**Key Components:**\n"
            for module in modules[:5]:
                name = module.get('name', 'unknown')
                type_ = module.get('type', 'unknown')
                file_count = module.get('file_count', 0)
                extensions = module.get('extensions', [])
                exts_str = ', '.join(extensions[:2])
                answer += f"- **{name}** ({type_}): {file_count} files ({exts_str})\n"
            answer += "\n"
        
        if patterns:
            answer += f"**Architecture Patterns:** {', '.join(patterns)}\n"
        
        return answer.strip()
    
    def _answer_tech_stack(self, metadata: Dict) -> str:
        """Answer technology/framework questions."""
        frameworks = metadata.get('frameworks', {})
        tech_stack = metadata.get('tech_stack', [])
        
        answer = "**Technology Stack:**\n\n"
        
        lang = metadata['analysis'].get('primary_language', 'unknown')
        answer += f"**Language:** {lang}\n\n"
        
        if frameworks:
            answer += "**Frameworks:**\n"
            for fw, info in sorted(frameworks.items(), 
                                  key=lambda x: x[1].get('confidence', 0), 
                                  reverse=True)[:8]:
                conf = info.get('confidence', 0)
                answer += f"- {fw} ({conf:.0%})\n"
            answer += "\n"
        
        if tech_stack:
            answer += f"**Key Technologies:** {', '.join(tech_stack[:10])}\n"
        
        return answer.strip()
    
    def _answer_components(self, metadata: Dict) -> str:
        """Answer component/module questions."""
        modules = metadata.get('modules', [])
        
        if not modules:
            return "No distinct components could be identified. The project may use a flat structure."
        
        answer = "**Components & Modules:**\n\n"
        for module in modules:
            name = module.get('name')
            type_ = module.get('type')
            desc = module.get('purpose', 'Module')
            file_count = module.get('file_count', 0)
            answer += f"- **{name}** ({type_}, {file_count} files): {desc}\n"
        
        return answer.strip()
    
    def _answer_data_flow(self, metadata: Dict, question: str) -> str:
        """Answer data flow questions."""
        analysis = metadata['analysis']
        frameworks = metadata.get('frameworks', {})
        
        answer = "**Data Flow:**\n\n"
        
        if analysis.get('has_frontend') and analysis.get('has_backend'):
            answer += "1. **Client (Frontend)**: User interface layer that collects input\n"
            answer += "2. **API Gateway**: Routes requests from frontend to backend services\n"
            answer += "3. **Services**: Process business logic and data transformations\n"
            answer += "4. **Database**: Persists data and maintains state\n\n"
            answer += "Data typically flows: User Action → API Request → Service Processing → DB Query → Response → UI Update\n"
        elif analysis.get('has_frontend'):
            answer += "This is a frontend application with local state management or external API calls.\n"
            answer += "Data flow: User Interaction → Component State → API Call (if applicable) → Update View\n"
        elif analysis.get('has_backend'):
            answer += "This is a backend service that processes requests and manages data.\n"
            answer += "Data flow: Request → Route Handler → Business Logic → Database → Response\n"
        
        return answer.strip()
    
    def _answer_deployment(self, metadata: Dict) -> str:
        """Answer deployment/production questions."""
        answer = "**Deployment & Production:**\n\n"
        
        frameworks = metadata.get('frameworks', {})
        deps = metadata.get('dependencies', {})
        
        # Infer deployment info from frameworks
        if any(fw in str(frameworks.keys()).lower() for fw in ['docker', 'kubernetes']):
            answer += "- Container-based deployment detected (Docker/Kubernetes)\n"
        
        if any(fw in str(frameworks.keys()).lower() for fw in ['fastapi', 'django', 'flask', 'express']):
            answer += "- Can be deployed as a standalone web service\n"
        
        if metadata['analysis'].get('has_frontend'):
            answer += "- Frontend can be deployed to CDN (Vercel, Netlify, CloudFront, etc.)\n"
        
        answer += "- Check repository for: Dockerfile, docker-compose.yml, deployment configs, CI/CD pipeline\n"
        
        return answer.strip()
    
    def _answer_dependencies(self, metadata: Dict) -> str:
        """Answer dependency questions."""
        deps = metadata.get('dependencies', {})
        
        answer = "**Dependencies:**\n\n"
        
        prod = deps.get('production', {})
        dev = deps.get('development', {})
        
        if isinstance(prod, dict):
            answer += f"**Production:** {len(prod)} packages\n"
            if prod:
                answer += f"- Samples: {', '.join(list(prod.keys())[:5])}\n"
        
        if isinstance(dev, dict):
            answer += f"\n**Development:** {len(dev)} packages\n"
            if dev:
                answer += f"- Samples: {', '.join(list(dev.keys())[:5])}\n"
        
        return answer.strip()
    
    def _answer_general(self, metadata: Dict, question: str) -> str:
        """Answer general questions not fitting other categories."""
        name = metadata['repository']['name']
        analysis = metadata['analysis']
        modules = metadata.get('modules', [])
        
        answer = f"**About {name}:**\n\n"
        answer += f"This {analysis.get('primary_language', 'unknown')}-based project contains {analysis.get('file_count', 0)} files "
        answer += f"organized into {len(modules)} main components.\n\n"
        answer += "Key aspects you can explore:\n"
        answer += "- **Architecture**: How the system is structured\n"
        answer += "- **Components**: What modules/services exist\n"
        answer += "- **Tech Stack**: Technologies and frameworks used\n"
        answer += "- **Dependencies**: External libraries and packages\n"
        
        return answer.strip()
    
    def answer_question(
        self,
        metadata: Dict,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict:
        """
        Answer a question about the repository architecture.
        
        Uses intent detection, RAG (if available), and AI or rule-based methods.
        
        Args:
            metadata: Repository metadata from metadata builder
            question: User's question about the repository
            
        Returns:
            Dictionary with answer and metadata
        """
        if not question or not isinstance(question, str):
            raise ValueError("Question must be a non-empty string")
        
        repo_name = metadata['repository']['name']
        logger.info(f"Processing question about {repo_name}: {question}")
        
        # Detect the intent of the question
        intent_match = self._detect_intent(question)
        logger.debug(f"Detected intent: {intent_match.intent.value} (confidence: {intent_match.confidence:.1%})")
        
        # Initialize RAG for this repository
        self.rag_store = self._init_rag_for_repo(metadata)
        
        conversation_history = conversation_history or []

        # Route to AI or rule-based based on capability
        if self.ai_usable:
            return self._ai_answer_question(metadata, question, intent_match, conversation_history)
        else:
            return self._rule_based_answer(metadata, question, intent_match)
    
    def _ai_answer_question(self, metadata: Dict, question: str, 
                           intent_match: IntentMatch,
                           conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict:
        """Answer question using Google Gemini with RAG-enhanced context and proper token budgeting.
        
        Improvements:
        - Proper token budgeting to avoid truncation
        - Finish reason checking to detect truncation
        - Automatic context trimming if budget exceeded
        - Continuation retry if truncated
        - Comprehensive observability logging
        """
        try:
            repo_name = metadata['repository']['name']
            
            # Initialize code context
            code_context = ""
            rag_used = False
            ai_mode = "Gemini"
            snippet_count = 0
            
            # Try to retrieve code context using RAG
            if self.rag_store:
                logger.info("Attempting RAG retrieval for enhanced code context...")
                try:
                    code_snippets, search_observability = self.rag_store.search(question, k=settings.RAG_TOP_K)
                    
                    if code_snippets:
                        logger.info(f"✓ Retrieved {len(code_snippets)} relevant code chunks via RAG")
                        logger.debug(f"Search observability: {search_observability}")
                        code_context = self._build_code_context(code_snippets)
                        rag_used = True
                        ai_mode = "RAG + Gemini"
                        snippet_count = len(code_snippets)
                    else:
                        logger.debug("RAG search returned no results, using metadata-only context")
                except Exception as e:
                    logger.debug(f"RAG search failed ({type(e).__name__}): {e}. Continuing with metadata-only context.")
            else:
                logger.debug("RAG not available, using metadata-only context")
            
            # Build metadata context
            context = self._construct_context(metadata)
            conversation_context = self._build_conversation_context(conversation_history or [])
            
            # Build the prompt components
            system_prompt = """You are an expert software architect analyzing a codebase.
Answer questions about repository architecture clearly and concisely.
Provide practical, actionable information based on the provided context."""
            
            # Calculate token budget and trim if needed
            budget = create_budget(
                model=self.google_model,
                system_prompt=system_prompt,
                user_question=question,
                context=context + code_context + conversation_context,
                reserved_output_tokens=1500,  # Reserve 1500 tokens for response
            )
            
            # Log budget info
            budget_stats = budget.to_dict()
            logger.info(f"Token budget: {budget_stats}")
            
            # Trim context if over budget
            if budget.is_over_budget:
                logger.warning(f"⚠ Over token budget by {budget.context_trim_ratio:.0%}. Trimming context...")
                code_context, trim_stats = trim_code_snippets(code_context, max_snippets=3, max_snippet_lines=20)
                logger.info(f"Code snippet trim stats: {trim_stats}")
                snippet_count = trim_stats.get("snippets_kept", snippet_count)
            
            # Build final prompt
            prompt = self._build_query_prompt_with_code(context, question, code_context)
            if conversation_context:
                prompt = self._inject_conversation_context(prompt, conversation_context)
            
            logger.info(f"Querying Gemini API ({ai_mode})...")
            logger.debug(f"Model: {self.google_model}, Temperature: {self.google_temperature}")
            logger.debug(f"Prompt estimated tokens: {estimate_tokens(prompt)}")
            
            # Use configured max tokens with safe minimum
            max_output_tokens = getattr(settings, "GOOGLE_MAX_TOKENS", 4000)
            max_output_tokens = max(2000, min(8000, max_output_tokens))  # Safe range: 2000-8000
            
            # Call Google Gemini API
            response = self.client.models.generate_content(
                model=self.google_model,
                contents=f"""{system_prompt}

{prompt}""",
                config={
                    "temperature": self.google_temperature,
                    "max_output_tokens": max_output_tokens,
                }
            )
            
            answer_text = response.text
            finish_reason = getattr(response, 'finish_reason', 'UNKNOWN')
            output_chars = len(answer_text) if answer_text else 0
            output_tokens = estimate_tokens(answer_text)
            
            # Check if answer was truncated
            truncated_detected = finish_reason == "MAX_TOKENS" or (
                output_chars > 0 and not answer_text.strip().endswith((')', ']', '}', '.', '!', '?', '```'))
            )
            
            # Log observability metrics
            observability_log = {
                "prompt_estimated_tokens": estimate_tokens(prompt),
                "snippet_count": snippet_count,
                "context_chars": len(context) + len(code_context) + len(conversation_context),
                "requested_max_output_tokens": max_output_tokens,
                "finish_reason": finish_reason,
                "output_chars": output_chars,
                "output_tokens": output_tokens,
                "truncated_detected": truncated_detected,
            }
            logger.info(f"AI response metrics: {observability_log}")
            
            # Handle truncation with retry
            if truncated_detected and finish_reason == "MAX_TOKENS":
                logger.warning("✗ Response was truncated (finish_reason=MAX_TOKENS). Attempting second pass...")
                answer_text = self._continue_truncated_answer(answer_text, metadata, question)
                observability_log["retry_attempted"] = True
            elif truncated_detected:
                logger.warning(f"⚠ Possible truncation detected (finish_reason={finish_reason}). Response may be incomplete.")
                observability_log["truncation_likely"] = True
                # Add note to response
                answer_text += "\n\n[Note: Response may be incomplete due to length constraints. Consider splitting your question.]"
            else:
                observability_log["retry_attempted"] = False
                logger.info(f"✓ Answer generated successfully via Gemini ({ai_mode}) - fully complete")
            
            return {
                "status": "success",
                "answer": answer_text,
                "mode": "ai",
                "ai_mode": ai_mode,
                "question": question,
                "repository": repo_name,
                "used_rag": rag_used,
                "intent": intent_match.intent.value,
                "truncated": truncated_detected,
                "observability": observability_log,
            }
        
        except Exception as e:
            # CRITICAL ERROR: Log detailed diagnostics about why AI failed
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"✗ AI query failed with {error_type}: {error_msg}")
            logger.error(f"  Repository: {metadata.get('repository', {}).get('name', 'unknown')}")
            logger.error(f"  Model: {self.google_model}")
            logger.error(f"  API Key configured: {bool(settings.GOOGLE_API_KEY)}")
            
            # Provide detailed diagnostics based on error type
            if "ResourceExhausted" in error_type or "quota" in error_msg.lower():
                logger.error("  → Likely cause: Gemini API quota exceeded")
            elif "PermissionDenied" in error_type or "unauthenticated" in error_msg.lower():
                logger.error("  → Likely cause: Invalid or missing API key")
            elif "DeadlineExceeded" in error_type or "timeout" in error_msg.lower():
                logger.error("  → Likely cause: API call timed out")
            elif "NotFound" in error_type or "not found" in error_msg.lower():
                logger.error("  → Likely cause: Model not available or wrong model name")
            
            logger.error("  → Falling back to rule-based answering...")
            
            # Fallback to rule-based with error note
            result = self._rule_based_answer(metadata, question, intent_match)
            result["note"] = f"Gemini API error ({error_type}). Using fallback rule-based answer. Check logs for details."
            return result
    
    def _continue_truncated_answer(self, partial_answer: str, metadata: Dict, question: str) -> str:
        """Continue a truncated answer from a previous API call.
        
        Strategy: Use the partial answer as context to get the continuation.
        
        Args:
            partial_answer: The incomplete answer from the first call
            metadata: Repository metadata
            question: Original question
            
        Returns:
            Complete answer (partial + continuation)
        """
        try:
            logger.info("Making continuation call to Gemini...")
            
            continuation_prompt = f"""The following answer to a software architecture question was incomplete.
Please continue from exactly where you stopped. Continue naturally without repetition.

ORIGINAL QUESTION:
{question}

INCOMPLETE ANSWER (end was cut off):
{partial_answer}

CONTINUATION:
"""
            
            # Make continuation call with lower max tokens to be more conservative
            response = self.client.models.generate_content(
                model=self.google_model,
                contents=continuation_prompt,
                config={
                    "temperature": self.google_temperature,
                    "max_output_tokens": 2000,  # Conservative for continuation
                }
            )
            
            continuation = response.text
            complete_answer = partial_answer + "\n" + continuation
            
            logger.info(f"✓ Continuation successful. Original: {len(partial_answer)} chars, Continuation: {len(continuation)} chars")
            return complete_answer
        
        except Exception as e:
            logger.error(f"Continuation call failed ({type(e).__name__}): {e}. Returning partial answer.")
            partial_answer += "\n\n[Note: Unable to retrieve complete answer. The above may be truncated. Please ask a more specific question.]"
            return partial_answer
    
    def _rule_based_answer(self, metadata: Dict, question: str,
                          intent_match: IntentMatch) -> Dict:
        """Answer question using intent-driven rule-based logic."""
        logger.info(f"Rule-based mode: Answering with intent {intent_match.intent.value}")
        
        answer = self._answer_by_intent(intent_match.intent, metadata, question)
        
        ai_mode = "Rule-based"
        if not self.ai_usable:
            ai_mode = f"Rule-based ({settings.get_ai_disabled_reason()})"
        
        return {
            "status": "success",
            "answer": answer,
            "mode": "rule-based",
            "ai_mode": ai_mode,
            "question": question,
            "repository": metadata['repository']['name'],
            "used_rag": False,
            "intent": intent_match.intent.value,
            "note": "This answer was generated using pattern matching and architectural analysis."
        }
    
    def _construct_context(self, metadata: Dict) -> str:
        """Construct context string from metadata for AI queries."""
        context_parts = []
        
        # Repository info
        context_parts.append(f"Repository: {metadata['repository']['name']}")
        context_parts.append(f"URL: {metadata['repository']['url']}")
        
        # Analysis info
        analysis = metadata['analysis']
        context_parts.append(f"\nBasic Info:")
        context_parts.append(f"- Primary Language: {analysis['primary_language']}")
        context_parts.append(f"- Total Files: {analysis['file_count']}")
        
        # Fix: languages is a dict, convert to list of keys
        languages_dict = analysis.get('languages', {})
        languages_list = list(languages_dict.keys())[:5] if isinstance(languages_dict, dict) else []
        if languages_list:
            context_parts.append(f"- Languages: {', '.join(languages_list)}")
        
        context_parts.append(f"- Has Backend: {analysis.get('has_backend', False)}")
        context_parts.append(f"- Has Frontend: {analysis.get('has_frontend', False)}")
        
        # Frameworks
        if metadata.get('frameworks'):
            context_parts.append(f"\nFrameworks:")
            for framework, info in sorted(
                metadata['frameworks'].items(),
                key=lambda x: x[1].get('confidence', 0),
                reverse=True
            )[:5]:
                conf = info.get('confidence', 0)
                context_parts.append(f"- {framework}: {conf:.0%} confidence")
        
        # Tech stack
        if metadata.get('tech_stack'):
            context_parts.append(f"\nTech Stack: {', '.join(metadata['tech_stack'][:10])}")
        
        # Architecture patterns
        if metadata.get('architecture_patterns'):
            context_parts.append(f"Architecture Patterns: {', '.join(metadata['architecture_patterns'])}")
        
        # Modules/Components
        if metadata.get('modules'):
            context_parts.append(f"\nKey Components:")
            for module in metadata['modules'][:8]:
                context_parts.append(
                    f"- {module.get('name', 'unknown')}: {module.get('type', 'module')} "
                    f"({module.get('file_count', 0)} files, "
                    f"extensions: {', '.join(module.get('extensions', [])[:3])})"
                )
        
        # Important files - Fix: important_files is a list, not dict
        if metadata.get('important_files'):
            important_files = metadata['important_files']
            if isinstance(important_files, list) and important_files:
                context_parts.append(f"\nImportant Files:")
                for file_name in important_files[:8]:
                    context_parts.append(f"- {file_name}")
        
        # Dependencies info
        if metadata.get('dependencies'):
            deps = metadata['dependencies']
            context_parts.append(f"\nDependencies:")
            for dep_type, dep_list in deps.items():
                if isinstance(dep_list, dict):
                    context_parts.append(f"- {dep_type}: {len(dep_list)} packages")
                elif isinstance(dep_list, list):
                    context_parts.append(f"- {dep_type}: {len(dep_list)} packages")
        
        return "\n".join(context_parts)
    
    def _build_code_context(self, code_snippets: List[Tuple[CodeChunk, float]]) -> str:
        """Format code snippets into readable context for the prompt.
        
        Args:
            code_snippets: List of (CodeChunk, similarity_score) tuples from RAG search
            
        Returns:
            Formatted string with code context
        """
        if not code_snippets:
            return ""
        
        context_parts = ["RELEVANT CODE SNIPPETS:"]
        context_parts.append("=" * 60)
        
        for idx, (chunk, similarity) in enumerate(code_snippets, 1):
            # File and location information
            context_parts.append(f"\n[Snippet {idx}] {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})")
            context_parts.append(f"Language: {chunk.language} | Relevance: {similarity:.1%}")
            context_parts.append("-" * 60)
            
            # Code content with line numbers
            lines = chunk.code_content.split('\n')
            for line_offset, line in enumerate(lines):
                actual_line_num = chunk.start_line + line_offset
                # Truncate very long lines
                display_line = line[:120] + "..." if len(line) > 120 else line
                context_parts.append(f"{actual_line_num:4d} | {display_line}")
            
            context_parts.append("")
        
        context_parts.append("=" * 60)
        return "\n".join(context_parts)
    
    def _build_query_prompt_with_code(self, context: str, question: str,
                                     code_context: str) -> str:
        """Build enhanced prompt that includes both metadata and code context."""
        prompt_parts = [
            "REPOSITORY ARCHITECTURE:",
            context,
            ""
        ]
        
        if code_context:
            prompt_parts.extend([
                code_context,
                ""
            ])
        
        prompt_parts.extend([
            "QUESTION:",
            question,
            "",
            "INSTRUCTIONS:",
            "1. Reference code snippets with file paths when relevant",
            "2. Provide practical insights about the architecture",
            "3. For design decisions, explain the reasoning",
            "4. Be concise but comprehensive"
        ])
        
        return "\n".join(prompt_parts)

    def _build_conversation_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """Format recent conversation history for conversational AI responses."""
        if not conversation_history:
            return ""

        recent_messages = conversation_history[-8:]
        lines = ["RECENT CONVERSATION:"]
        for message in recent_messages:
            role = (message.get("role") or "user").strip().lower()
            if role not in {"user", "assistant"}:
                continue
            content = (message.get("content") or "").strip()
            if not content:
                continue
            speaker = "User" if role == "user" else "Assistant"
            lines.append(f"{speaker}: {content}")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    def _inject_conversation_context(self, prompt: str, conversation_context: str) -> str:
        """Append prior chat turns to the prompt while keeping current question primary."""
        return "\n".join([
            prompt,
            "",
            conversation_context,
            "",
            "Use the conversation history only to maintain continuity and resolve follow-up references.",
        ])

