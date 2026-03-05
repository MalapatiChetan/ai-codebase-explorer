"""AI-powered architecture analysis module using Google Gemini API."""

import os
import json
import logging
from typing import Dict
from google import genai
from src.utils.config import settings

logger = logging.getLogger(__name__)


class AIArchitectureAnalyzer:
    """Provides architecture analysis using Google Gemini or rule-based fallback."""
    
    def __init__(self):
        """Initialize the AI analyzer.
        
        Provider behavior:
        1. Google Gemini (if GOOGLE_API_KEY is set)
        2. Rule-based fallback (no API key required)
        """
        self.provider = "rule-based"
        self.client = None
        
        # Check for Google Gemini
        if settings.GOOGLE_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                self.provider = "gemini"
                logger.info(f"✓ Gemini AI mode enabled ({settings.GOOGLE_MODEL})")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini: {e}. Falling back to rule-based analysis.")
                self.provider = "rule-based"
                self.client = None
        
        # Log final provider
        if self.provider == "rule-based":
            logger.info("✓ Rule-based mode enabled (no API key)")
    
    def analyze(self, metadata: Dict) -> Dict:
        """
        Generate AI analysis of the repository architecture.
        
        Args:
            metadata: Repository metadata from metadata builder
            
        Returns:
            Dictionary containing AI-generated analysis
        """
        if self.provider == "rule-based":
            logger.debug("Using rule-based analysis")
            return self._generate_fallback_analysis(metadata)
        
        try:
            logger.info(f"Generating Gemini AI analysis (model: {settings.GOOGLE_MODEL})...")
            prompt = self._build_analysis_prompt(metadata)
            analysis_text = self._call_gemini(prompt)
            
            # Parse the response
            analysis = self._parse_analysis_response(analysis_text, metadata)
            logger.info("Gemini analysis completed successfully")
            return analysis
        
        except Exception as e:
            logger.error(f"Gemini API error ({type(e).__name__}): {e}")
            logger.error(f"  Attempted model: {settings.GOOGLE_MODEL}")
            logger.error(f"  API key configured: {bool(settings.GOOGLE_API_KEY)}")
            logger.error("  Falling back to rule-based analysis...")
            return self._generate_fallback_analysis(metadata)
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API for analysis.
        
        Args:
            prompt: The analysis prompt
            
        Returns:
            The text response from Gemini
        """
        try:
            response = self.client.models.generate_content(
                model=settings.GOOGLE_MODEL,
                contents=prompt,
                config={
                    "temperature": settings.GOOGLE_TEMPERATURE,
                    "max_output_tokens": settings.GOOGLE_MAX_TOKENS,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _build_analysis_prompt(self, metadata: Dict) -> str:
        """Build the analysis prompt for Gemini API."""
        modules_text = "\n".join([
            f"- {m['name']}: {m['type']} ({m['file_count']} files, extensions: {', '.join(m['extensions'])})"
            for m in metadata.get("modules", [])
        ])
        
        frameworks_text = "\n".join([
            f"- {name}: confidence {info['confidence']:.0%}"
            for name, info in metadata.get("frameworks", {}).items()
        ])
        
        prompt = f"""
Analyze the following repository metadata and provide a comprehensive architecture explanation:

Repository: {metadata['repository']['name']}
URL: {metadata['repository']['url']}
Primary Language: {metadata['analysis']['primary_language']}
File Count: {metadata['analysis']['file_count']}

Detected Frameworks:
{frameworks_text}

Tech Stack: {', '.join(metadata['tech_stack'])}
Architecture Patterns: {', '.join(metadata['architecture_patterns'])}
Has Backend: {metadata['analysis']['has_backend']}
Has Frontend: {metadata['analysis']['has_frontend']}

Modules/Components:
{modules_text}

Root Files: {', '.join(metadata['root_files'])}

Based on this information, please provide:

1. **System Overview**: A 2-3 sentence high-level description of what this project is
2. **Core Components**: List the main components/services and their responsibilities
3. **Architecture Pattern**: Identify the architectural pattern(s) used
4. **Data Flow**: Describe how data flows through the system
5. **Technology Assessment**: Evaluate the technology choices
6. **Key Observations**: Any interesting architectural decisions or patterns
7. **Suggested Improvements**: If applicable, suggest architectural improvements

Format your response in a clear, developer-friendly manner.
"""
        return prompt.strip()
    
    def _parse_analysis_response(self, response_text: str, metadata: Dict) -> Dict:
        """Parse Gemini response into structured format."""
        try:
            # Split response into sections
            sections = {
                "raw_analysis": response_text,
            }
            
            # Extract sections if they exist
            for section_name in [
                "System Overview",
                "Core Components",
                "Architecture Pattern",
                "Data Flow",
                "Technology Assessment",
                "Key Observations",
                "Suggested Improvements"
            ]:
                if section_name in response_text:
                    # Extract content after section header
                    start_idx = response_text.find(section_name)
                    next_section_idx = len(response_text)
                    
                    for other_section in [
                        "System Overview", "Core Components", "Architecture Pattern",
                        "Data Flow", "Technology Assessment", "Key Observations",
                        "Suggested Improvements"
                    ]:
                        if other_section != section_name:
                            idx = response_text.find(other_section, start_idx + 1)
                            if idx != -1 and idx < next_section_idx:
                                next_section_idx = idx
                    
                    content = response_text[start_idx:next_section_idx].strip()
                    # Remove the section header
                    content = content.replace(f"{section_name}:", "", 1).strip()
                    sections[section_name.lower().replace(" ", "_")] = content
            
            return {
                "status": "success",
                "analysis": sections
            }
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return {
                "status": "success",
                "analysis": {
                    "raw_analysis": response_text
                }
            }
    
    def _generate_fallback_analysis(self, metadata: Dict) -> Dict:
        """Generate rule-based analysis without AI provider.
        
        Args:
            metadata: Repository metadata from metadata builder
            
        Returns:
            Dictionary containing rule-based analysis
        """
        logger.info("Generating fallback analysis based on rules")
        
        # Determine system type
        if metadata['analysis']['has_backend'] and metadata['analysis']['has_frontend']:
            system_type = "Full-stack web application"
        elif metadata['analysis']['has_frontend']:
            system_type = "Frontend application"
        elif metadata['analysis']['has_backend']:
            system_type = "Backend service/API"
        else:
            system_type = "Library or utility project"
        
        # Build analysis
        analysis_text = f"""
**System Overview**
{metadata['repository']['name']} is a {system_type} built with {metadata['analysis']['primary_language']}.

**Detected Technology Stack**
The project uses: {', '.join(metadata['tech_stack'])}

**Architecture Style**
Indicated patterns: {', '.join(metadata['architecture_patterns']) if metadata['architecture_patterns'] else 'Not explicitly detected'}

**Components**
The repository contains {len(metadata['modules'])} main modules/components:
"""
        
        for module in metadata['modules'][:5]:
            analysis_text += f"\n- **{module['name']}**: {module['type']} component with {module['file_count']} files"
        
        analysis_text += f"""

**Key Information**
- Primary Language: {metadata['analysis']['primary_language']}
- Total Files Analyzed: {metadata['analysis']['file_count']}
- Backend Component: {'Yes' if metadata['analysis']['has_backend'] else 'No'}
- Frontend Component: {'Yes' if metadata['analysis']['has_frontend'] else 'No'}

**Framework Detection**
"""
        
        frameworks = metadata.get('frameworks', {})
        if frameworks:
            for framework, info in sorted(frameworks.items(), 
                                         key=lambda x: x[1]['confidence'], 
                                         reverse=True):
                analysis_text += f"\n- {framework}: {info['confidence']:.0%} confidence"
        else:
            analysis_text += "\nNo major frameworks explicitly detected."
        
        # Generate note about analysis mode
        note = "This is a rule-based analysis. "
        if settings.GOOGLE_API_KEY:
            note += "Gemini API is available but an error occurred. "
        else:
            note += "For AI-powered analysis, set GOOGLE_API_KEY in your .env file."
        
        return {
            "status": "success",
            "analysis": {
                "raw_analysis": analysis_text.strip(),
                "note": note
            }
        }
