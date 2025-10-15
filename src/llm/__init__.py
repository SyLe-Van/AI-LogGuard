"""
LLM integration module for AI-LogGuard
Provides AI-powered log analysis, error explanation, and fix suggestions
"""
from .openai_client import OpenAIClient, get_openai_client
from .summarizer import LogSummarizer, summarize_log
from .explainer import ErrorExplainer, explain_error
from .fix_suggester import FixSuggester, suggest_fix, suggest_comprehensive_fix
from .chunker import LogChunker, chunk_log_for_llm, estimate_total_tokens

__all__ = [
    # Client
    "OpenAIClient",
    "get_openai_client",
    
    # Summarizer
    "LogSummarizer",
    "summarize_log",
    
    # Explainer
    "ErrorExplainer",
    "explain_error",
    
    # Fix Suggester
    "FixSuggester",
    "suggest_fix",
    "suggest_comprehensive_fix",
    
    # Chunker
    "LogChunker",
    "chunk_log_for_llm",
    "estimate_total_tokens",
]
