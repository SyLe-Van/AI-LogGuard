"""
Data models for AI-LogGuard
Unified schema for log analysis across different CI/CD platforms
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log entry severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BuildStatus(str, Enum):
    """Build execution status"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNSTABLE = "UNSTABLE"
    TIMEOUT = "TIMEOUT"
    ABORTED = "ABORTED"
    UNKNOWN = "UNKNOWN"


class ErrorCategory(str, Enum):
    """Common error categories for ML classification"""
    DEPENDENCY_ERROR = "dependency_error"
    SYNTAX_ERROR = "syntax_error"
    TEST_FAILURE = "test_failure"
    TIMEOUT = "timeout"
    ENVIRONMENT_ERROR = "environment_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class Platform(str, Enum):
    """Supported CI/CD platforms"""
    JENKINS = "jenkins"
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"
    UNKNOWN = "unknown"


class LogEntry(BaseModel):
    """Individual log line/entry"""
    timestamp: Optional[datetime] = None
    level: LogLevel = LogLevel.INFO
    message: str
    line_number: int
    raw_line: str
    
    class Config:
        use_enum_values = True


class StageInfo(BaseModel):
    """Information about a build stage/step"""
    name: str
    status: BuildStatus = BuildStatus.UNKNOWN
    error_count: int = 0
    warning_count: int = 0
    retry_count: int = 0
    critical_count: int = 0
    duration_seconds: Optional[float] = None
    
    class Config:
        use_enum_values = True


class ParsedLog(BaseModel):
    """
    Unified parsed log structure
    Works across Jenkins, GitHub Actions, GitLab CI, etc.
    """
    # Source metadata
    platform: Platform
    job_name: Optional[str] = None
    build_number: Optional[str] = None
    build_url: Optional[str] = None
    
    # Build information
    status: BuildStatus = BuildStatus.UNKNOWN
    duration_seconds: Optional[float] = None
    triggered_by: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    
    # Parsed content
    stages: List[StageInfo] = Field(default_factory=list)
    errors: List[LogEntry] = Field(default_factory=list)
    warnings: List[LogEntry] = Field(default_factory=list)
    
    # Statistics
    total_lines: int = 0
    error_count: int = 0
    warning_count: int = 0
    retry_count: int = 0
    
    # Raw content (for reference)
    raw_content: str = ""
    
    # ML prediction (will be populated later)
    predicted_error_category: Optional[ErrorCategory] = None
    prediction_confidence: Optional[float] = None
    
    class Config:
        use_enum_values = True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a quick summary of the parsed log"""
        return {
            "platform": self.platform,
            "status": self.status,
            "job_name": self.job_name,
            "build_number": self.build_number,
            "duration": self.duration_seconds,
            "stages": len(self.stages),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "retries": self.retry_count,
        }
    
    def get_critical_errors(self) -> List[LogEntry]:
        """Get only critical/high-priority errors"""
        return [e for e in self.errors if e.level == LogLevel.CRITICAL]
    
    def get_failed_stages(self) -> List[StageInfo]:
        """Get stages that failed"""
        return [s for s in self.stages if s.status == BuildStatus.FAILED]


class AnalysisResult(BaseModel):
    """
    Complete analysis result (will be used in later phases)
    Combines parsing + ML prediction + LLM analysis
    """
    parsed_log: ParsedLog
    
    # ML Model prediction
    ml_prediction: Optional[ErrorCategory] = None
    ml_confidence: Optional[float] = None
    
    # LLM Analysis (Phase 2)
    llm_summary: Optional[str] = None
    llm_explanation: Optional[str] = None
    llm_fix_suggestions: Optional[List[str]] = None
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = None
    
    class Config:
        use_enum_values = True
