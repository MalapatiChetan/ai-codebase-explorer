"""Prompt and token budgeting utilities for LLM API calls.

This module provides utilities to:
1. Estimate token usage for prompts and responses
2. Dynamically trim context to stay within budget
3. Manage response buffer to avoid truncation
4. Track and log token usage for observability
"""

import logging
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Rough token estimation (1 token ≈ 4 characters for English text)
# More accurate: use actual tokenizer, but this gives 80-90% accuracy
CHARS_PER_TOKEN = 4.0

# Token limits for different Gemini models
MODEL_LIMITS = {
    "gemini-2.5-flash": {
        "input_max": 1_000_000,
        "output_max": 8_000,
    },
    "gemini-2.5-pro": {
        "input_max": 1_000_000,
        "output_max": 8_000,
    },
    "gemini-2.0-flash": {
        "input_max": 1_000_000,
        "output_max": 8_000,
    },
    "gemini-1.5-flash": {
        "input_max": 1_000_000,
        "output_max": 8_000,
    },
    "gemini-1.5-pro": {
        "input_max": 2_000_000,
        "output_max": 8_000,
    },
}


@dataclass
class TokenBudget:
    """Token budget tracking."""
    model: str
    input_max: int
    output_max: int
    system_prompt_tokens: int
    user_question_tokens: int
    context_tokens: int
    reserved_output_tokens: int = 1200  # Minimum response buffer
    
    @property
    def available_for_context(self) -> int:
        """Calculate how many tokens available for context."""
        used = self.system_prompt_tokens + self.user_question_tokens
        reserved = self.reserved_output_tokens
        return max(0, self.input_max - used - reserved)
    
    @property
    def is_over_budget(self) -> bool:
        """Check if context exceeds available budget."""
        return self.context_tokens > self.available_for_context
    
    @property
    def context_trim_ratio(self) -> float:
        """Calculate how much context needs to be trimmed (0.0 to 1.0)."""
        if self.context_tokens == 0:
            return 0.0
        ratio = self.context_tokens / self.available_for_context
        return min(1.0, max(0.0, ratio - 1.0))
    
    def to_dict(self) -> Dict:
        """Export as dictionary for logging."""
        return {
            "model": self.model,
            "system_prompt_tokens": self.system_prompt_tokens,
            "user_question_tokens": self.user_question_tokens,
            "context_tokens": self.context_tokens,
            "available_for_context": self.available_for_context,
            "reserved_output_tokens": self.reserved_output_tokens,
            "is_over_budget": self.is_over_budget,
        }


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation).
    
    For production, use actual tokenizer:
    - pip install tiktoken
    - But sentence-transformers already has it as dependency
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Rough estimate: 1 token ≈ 4 characters
    # Adjust for punctuation and special chars
    estimated = len(text) / CHARS_PER_TOKEN
    return max(1, int(math.ceil(estimated)))


def create_budget(
    model: str,
    system_prompt: str,
    user_question: str,
    context: str = "",
    reserved_output_tokens: int = 1200,
) -> TokenBudget:
    """Create a token budget for a query.
    
    Args:
        model: Model name (e.g., "gemini-2.5-flash")
        system_prompt: System prompt text
        user_question: User's question
        context: Context (metadata + code snippets)
        reserved_output_tokens: Tokens to reserve for response
        
    Returns:
        TokenBudget object with allocation info
    """
    limits = MODEL_LIMITS.get(model, MODEL_LIMITS["gemini-2.5-flash"])
    
    system_tokens = estimate_tokens(system_prompt)
    question_tokens = estimate_tokens(user_question)
    context_tokens = estimate_tokens(context)
    
    budget = TokenBudget(
        model=model,
        input_max=limits["input_max"],
        output_max=limits["output_max"],
        system_prompt_tokens=system_tokens,
        user_question_tokens=question_tokens,
        context_tokens=context_tokens,
        reserved_output_tokens=reserved_output_tokens,
    )
    
    return budget


def trim_context(
    context: str,
    max_chars: int,
    priority_sections: List[str] = None,
) -> Tuple[str, Dict]:
    """Trim context to fit budget while preserving important sections.
    
    Trimming strategy (in order of reduction):
    1. Remove code snippets (keep count below 3)
    2. Shorten code snippets (keep first 200 chars)
    3. Remove less important metadata sections
    4. Trim all remaining sections proportionally
    
    Args:
        context: Full context string to trim
        max_chars: Maximum characters allowed
        priority_sections: Section headers to preserve (in order of importance)
        
    Returns:
        Tuple of (trimmed_context, trim_stats)
    """
    if len(context) <= max_chars:
        return context, {"status": "no_trim_needed", "original_chars": len(context)}
    
    if priority_sections is None:
        priority_sections = [
            "RELEVANT CODE SNIPPETS",
            "REPOSITORY ARCHITECTURE",
            "QUESTION",
        ]
    
    sections = context.split("\n\n")
    trimmed_sections = []
    current_chars = 0
    
    # First pass: keep high-priority sections
    priority_indices = set()
    for priority in priority_sections:
        for i, section in enumerate(sections):
            if priority in section and i not in priority_indices:
                trimmed_sections.append(section)
                current_chars += len(section) + 2  # +2 for \n\n
                priority_indices.add(i)
                if current_chars >= max_chars:
                    break
        if current_chars >= max_chars:
            break
    
    # Second pass: add remaining sections if space
    for i, section in enumerate(sections):
        if i not in priority_indices:
            if current_chars + len(section) <= max_chars:
                trimmed_sections.append(section)
                current_chars += len(section) + 2
            else:
                break
    
    trimmed = "\n\n".join(trimmed_sections)
    
    # Final proportional trim if still over budget
    if len(trimmed) > max_chars:
        ratio = max_chars / len(trimmed)
        trimmed = trimmed[: max_chars - 100]  # Leave 100 chars for incomplete words
        trimmed += "\n\n[CONTEXT TRIMMED FOR TOKEN LIMIT]"
    
    stats = {
        "status": "trimmed",
        "original_chars": len(context),
        "trimmed_chars": len(trimmed),
        "trim_ratio": 1.0 - (len(trimmed) / len(context)),
        "sections_kept": len(trimmed_sections),
    }
    
    return trimmed, stats


def trim_code_snippets(
    context: str,
    max_snippets: int = 3,
    max_snippet_lines: int = 20,
) -> Tuple[str, Dict]:
    """Trim code snippets while preserving summary context.
    
    Args:
        context: Context with code snippets
        max_snippets: Maximum snippets to keep
        max_snippet_lines: Maximum lines per snippet
        
    Returns:
        Tuple of (trimmed_context, trim_stats)
    """
    lines = context.split("\n")
    trimmed_lines = []
    snippet_count = 0
    in_snippet = False
    snippet_lines = 0
    
    stats = {"snippets_found": 0, "snippets_kept": 0, "lines_removed": 0}
    
    for i, line in enumerate(lines):
        # Detect snippet markers
        if line.startswith("RELEVANT CODE SNIPPETS"):
            trimmed_lines.append(line)
            continue
        if "[Snippet" in line:
            in_snippet = True
            stats["snippets_found"] += 1
            
            if snippet_count < max_snippets:
                trimmed_lines.append(line)
                snippet_count += 1
                snippet_lines = 0
            else:
                stats["lines_removed"] += 1
                continue
        elif in_snippet and ("=" * 20 in line or line.startswith("QUESTION")):
            in_snippet = False
            snippet_lines = 0
            trimmed_lines.append(line)
        elif in_snippet:
            if snippet_count <= max_snippets and snippet_lines < max_snippet_lines:
                trimmed_lines.append(line)
                snippet_lines += 1
            else:
                stats["lines_removed"] += 1
        else:
            trimmed_lines.append(line)
    
    stats["snippets_kept"] = snippet_count
    
    return "\n".join(trimmed_lines), stats
