"""
Tests for LLM integration components
Tests summarizer, explainer, fix suggester, and chunking
"""
import pytest
from src.models.schemas import (
    ParsedLog, LogEntry, BuildStatus, Platform, 
    ErrorCategory, LogLevel, StageInfo
)
from src.llm import (
    LogSummarizer, ErrorExplainer, FixSuggester,
    LogChunker, chunk_log_for_llm, estimate_total_tokens
)


# Mock parsed log for testing
@pytest.fixture
def mock_parsed_log():
    """Create a mock parsed log with errors"""
    return ParsedLog(
        platform=Platform.JENKINS,
        job_name="test-build",
        build_number="42",
        status=BuildStatus.FAILED,
        raw_content="[ERROR] Build failed\n" * 50 + "[WARN] Deprecated API\n" * 50,
        total_lines=100,
        errors=[
            LogEntry(
                line_number=10,
                message="[ERROR] Could not resolve dependency: com.example:mylib:1.0.0",
                level=LogLevel.ERROR,
                raw_line="[ERROR] Could not resolve dependency: com.example:mylib:1.0.0",
                category=ErrorCategory.DEPENDENCY_ERROR
            ),
            LogEntry(
                line_number=25,
                message="[ERROR] Test failed: testCalculateTotal expected 100 but was 50",
                level=LogLevel.ERROR,
                raw_line="[ERROR] Test failed: testCalculateTotal expected 100 but was 50",
                category=ErrorCategory.TEST_FAILURE
            ),
        ],
        warnings=[
            LogEntry(
                line_number=60,
                message="[WARN] Using deprecated API",
                level=LogLevel.WARNING,
                raw_line="[WARN] Using deprecated API"
            )
        ],
        stages=[
            StageInfo(
                name="Checkout",
                status=BuildStatus.SUCCESS,
                start_line=1,
                end_line=10,
                error_count=0,
                warning_count=0
            ),
            StageInfo(
                name="Build",
                status=BuildStatus.FAILED,
                start_line=11,
                end_line=50,
                error_count=2,
                warning_count=0
            ),
        ]
    )
@pytest.fixture
def small_log():
    """Create a small parsed log that doesn't need chunking"""
    return ParsedLog(
        platform=Platform.GITHUB_ACTIONS,
        job_name="ci-test",
        status=BuildStatus.SUCCESS,
        raw_content="[INFO] Running tests\n" * 10,
        total_lines=10,
        errors=[],
        warnings=[]
    )


@pytest.fixture
def large_log():
    """Create a large log that needs chunking"""
    content = "\n".join([f"Line {i}: Some log content" for i in range(1000)])
    
    return ParsedLog(
        platform=Platform.JENKINS,
        job_name="large-build",
        status=BuildStatus.FAILED,
        raw_content=content,
        total_lines=1000,
        errors=[
            LogEntry(
                line_number=100,
                message="Error at line 100",
                level=LogLevel.ERROR,
                raw_line="Error at line 100"
            ),
            LogEntry(
                line_number=500,
                message="Error at line 500",
                level=LogLevel.ERROR,
                raw_line="Error at line 500"
            ),
        ],
        warnings=[]
    )
class TestLogChunker:
    """Test log chunking functionality"""
    
    def test_estimate_tokens(self):
        """Test token estimation"""
        text = "Hello world! " * 100  # ~1300 chars
        chunker = LogChunker()
        tokens = chunker.estimate_tokens(text)
        
        assert tokens > 0
        assert tokens == len(text) // 4  # Rough estimate: 1 token = 4 chars
    
    def test_needs_chunking(self, small_log, large_log):
        """Test detection of logs needing chunking"""
        chunker = LogChunker(max_tokens=4096)
        
        assert not chunker.needs_chunking(small_log)
        assert chunker.needs_chunking(large_log)
    
    def test_chunk_by_errors(self, mock_parsed_log):
        """Test error-focused chunking"""
        chunker = LogChunker(max_tokens=4096)
        chunks = chunker.chunk_by_errors(mock_parsed_log, context_lines=5)
        
        assert len(chunks) > 0
        assert any(chunk.has_errors for chunk in chunks)
        
        # Check that error lines are included
        error_lines = {err.line_number for err in mock_parsed_log.errors}
        chunk_ranges = [
            set(range(chunk.start_line, chunk.end_line + 1))
            for chunk in chunks
        ]
        
        for error_line in error_lines:
            assert any(error_line in chunk_range for chunk_range in chunk_ranges)
    
    def test_chunk_by_stages(self, mock_parsed_log):
        """Test stage-based chunking"""
        chunker = LogChunker(max_tokens=4096)
        chunks = chunker.chunk_by_stages(mock_parsed_log)
        
        assert len(chunks) == len(mock_parsed_log.stages)
        
        # Failed stage should have higher priority
        failed_chunks = [c for c in chunks if c.has_errors]
        assert len(failed_chunks) > 0
        assert max(c.priority for c in chunks) == max(c.priority for c in failed_chunks)
    
    def test_chunk_sequential(self, large_log):
        """Test sequential chunking"""
        chunker = LogChunker(max_tokens=1000)  # Small token limit
        chunks = chunker.chunk_sequential(large_log)
        
        assert len(chunks) > 1
        assert all(chunk.token_estimate <= 1000 for chunk in chunks)
    
    def test_chunk_smart(self, mock_parsed_log):
        """Test smart chunking strategy selection"""
        chunker = LogChunker(max_tokens=4096)
        chunks = chunker.chunk_smart(mock_parsed_log)
        
        assert len(chunks) > 0
        # Should use stage-based chunking for this log
        assert len(chunks) == len(mock_parsed_log.stages)
    
    def test_get_priority_chunks(self, mock_parsed_log):
        """Test priority chunk selection"""
        chunker = LogChunker(max_tokens=4096)
        all_chunks = chunker.chunk_by_errors(mock_parsed_log)
        
        top_chunks = chunker.get_priority_chunks(all_chunks, max_chunks=1)
        
        assert len(top_chunks) == 1
        assert top_chunks[0].priority == max(c.priority for c in all_chunks)


class TestLogSummarizer:
    """Test log summarization"""
    
    def test_quick_summary_success(self, small_log):
        """Test quick summary for successful build"""
        # Don't initialize with API key - use quick_summary which doesn't need it
        summarizer = LogSummarizer.__new__(LogSummarizer)  # Skip __init__
        summarizer.model = "gpt-3.5-turbo"
        
        summary = summarizer.quick_summary(small_log)
        
        assert "✅" in summary
        assert "succeeded" in summary.lower()
        assert "GITHUB_ACTIONS" in summary or "GitHub Actions" in summary
    
    def test_quick_summary_failure(self, mock_parsed_log):
        """Test quick summary for failed build"""
        summarizer = LogSummarizer.__new__(LogSummarizer)  # Skip __init__
        summarizer.model = "gpt-3.5-turbo"
        
        summary = summarizer.quick_summary(mock_parsed_log)
        
        assert "❌" in summary
        assert "failed" in summary.lower()
        assert "2 errors" in summary.lower()
    
    def test_summarize_requires_api_key(self, mock_parsed_log):
        """Test that summarize method requires OpenAI API key"""
        # Just test that the methods exist - don't call them without API key
        assert hasattr(LogSummarizer, 'summarize')
        assert hasattr(LogSummarizer, '_summarize_direct')
        assert hasattr(LogSummarizer, '_summarize_chunked')


class TestErrorExplainer:
    """Test error explanation"""
    
    def test_detect_dependency_error(self):
        """Test dependency error detection"""
        explainer = ErrorExplainer.__new__(ErrorExplainer)  # Skip __init__
        
        category = explainer._detect_category("Could not find dependency: com.example:lib:1.0")
        assert category == ErrorCategory.DEPENDENCY_ERROR
        
        category = explainer._detect_category("npm ERR! 404 Not Found")
        assert category == ErrorCategory.DEPENDENCY_ERROR
    
    def test_detect_test_failure(self):
        """Test test failure detection"""
        explainer = ErrorExplainer.__new__(ErrorExplainer)  # Skip __init__
        
        category = explainer._detect_category("Test failed: expected 10 but was 5")
        assert category == ErrorCategory.TEST_FAILURE
        
        category = explainer._detect_category("JUnit test assertion failed")
        assert category == ErrorCategory.TEST_FAILURE
    
    def test_detect_syntax_error(self):
        """Test syntax error detection"""
        explainer = ErrorExplainer.__new__(ErrorExplainer)  # Skip __init__
        
        category = explainer._detect_category("SyntaxError: unexpected token")
        assert category == ErrorCategory.SYNTAX_ERROR
        
        category = explainer._detect_category("Compilation failed: invalid syntax")
        assert category == ErrorCategory.SYNTAX_ERROR
    
    def test_extract_context(self, mock_parsed_log):
        """Test context extraction"""
        explainer = ErrorExplainer.__new__(ErrorExplainer)  # Skip __init__
        context = explainer._extract_context(
            mock_parsed_log.raw_content,
            line_number=10,
            context_lines=2
        )
        
        assert ">>>" in context  # Should mark error line
        assert len(context.split("\n")) <= 5  # 2 before + 1 error + 2 after
    
    def test_detect_package_manager(self):
        """Test package manager detection"""
        explainer = ErrorExplainer.__new__(ErrorExplainer)  # Skip __init__
        
        assert explainer._detect_package_manager("npm install failed") == "npm"
        assert explainer._detect_package_manager("pip install -r requirements.txt") == "pip"
        assert explainer._detect_package_manager("mvn clean install") == "maven"


class TestFixSuggester:
    """Test fix suggestion generation"""
    
    def test_detect_category_dependency(self):
        """Test category detection for dependency errors"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        category = suggester._detect_category("dependency not found")
        assert category == ErrorCategory.DEPENDENCY_ERROR
    
    def test_detect_category_test(self):
        """Test category detection for test failures"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        category = suggester._detect_category("test assertion failed")
        assert category == ErrorCategory.TEST_FAILURE
    
    def test_extract_test_name(self):
        """Test test name extraction"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        test_name = suggester._extract_test_name("test_calculate_total failed")
        assert "test_calculate_total" in test_name
    
    def test_detect_package_manager_npm(self):
        """Test npm detection"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        pm = suggester._detect_package_manager("npm ERR! code E404", Platform.GITHUB_ACTIONS)
        assert pm == "npm"
    
    def test_detect_package_manager_pip(self):
        """Test pip detection"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        pm = suggester._detect_package_manager("pip install failed", Platform.JENKINS)
        assert pm == "pip"
    
    def test_build_context_summary(self, mock_parsed_log):
        """Test context summary building"""
        suggester = FixSuggester.__new__(FixSuggester)  # Skip __init__
        
        summary = suggester._build_context_summary(mock_parsed_log)
        
        assert "100" in summary  # total lines
        assert "2" in summary  # errors
        assert "1" in summary  # warnings


# Integration tests (require API key, skip by default)
@pytest.mark.skip(reason="Requires OpenAI API key")
class TestLLMIntegration:
    """Integration tests with actual OpenAI API"""
    
    def test_end_to_end_summary(self, mock_parsed_log):
        """Test end-to-end summarization"""
        from src.llm import summarize_log
        
        result = summarize_log(mock_parsed_log, model="gpt-3.5-turbo")
        
        assert "summary" in result
        assert result["tokens_used"] > 0
        assert result["model"] == "gpt-3.5-turbo"
    
    def test_end_to_end_explain(self, mock_parsed_log):
        """Test end-to-end error explanation"""
        from src.llm import explain_error
        
        error = mock_parsed_log.errors[0]
        result = explain_error(error, mock_parsed_log)
        
        assert "explanation" in result
        assert result["tokens_used"] > 0
    
    def test_end_to_end_fix(self, mock_parsed_log):
        """Test end-to-end fix suggestion"""
        from src.llm import suggest_fix
        
        error = mock_parsed_log.errors[0]
        result = suggest_fix(error, mock_parsed_log)
        
        assert "fix_suggestions" in result
        assert result["tokens_used"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
