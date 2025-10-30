"""
Tests for Jenkins parser
"""
import pytest
from src.parsers import JenkinsParser, parse_log
from src.models import Platform, BuildStatus


def test_jenkins_parser_can_parse():
    """Test Jenkins parser can detect Jenkins logs"""
    parser = JenkinsParser()
    
    jenkins_log = "[Pipeline] Start of Pipeline\nRunning on Jenkins"
    assert parser.can_parse(jenkins_log) is True
    
    github_log = "##[group]Run actions/checkout"
    assert parser.can_parse(github_log) is False


def test_jenkins_parser_basic():
    """Test basic Jenkins log parsing"""
    log_content = """Started by user Sy Le
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/test-job
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Build)
[Pipeline] echo
Building...
[ERROR] Compilation failed
[WARNING] Deprecated API used
[Pipeline] }
Finished: FAILURE
"""
    
    parser = JenkinsParser()
    parsed = parser.parse(log_content, job_name="test-job")
    
    assert parsed.platform == Platform.JENKINS
    assert parsed.job_name == "test-job"
    assert parsed.status == BuildStatus.FAILED
    assert parsed.triggered_by == "Sy Le"
    assert parsed.error_count > 0
    assert parsed.warning_count > 0
    assert len(parsed.stages) > 0


def test_jenkins_parser_with_sample_logs():
    """Test with actual sample logs"""
    with open('tests/sample_logs.txt', 'r') as f:
        log_content = f.read()
    
    parsed = parse_log(log_content, job_name="test-job")
    
    assert parsed is not None
    assert parsed.platform == Platform.JENKINS
    assert parsed.error_count > 0
    assert parsed.warning_count > 0
    assert parsed.retry_count > 0


def test_jenkins_parser_stages():
    """Test stage parsing"""
    log_content = """[Pipeline] Start of Pipeline
[Pipeline] { (Stage 1)
[INFO] Starting stage 1
[ERROR] Stage 1 failed
[Pipeline] }
[Pipeline] { (Stage 2)
[INFO] Starting stage 2
[Pipeline] }
"""
    
    parser = JenkinsParser()
    parsed = parser.parse(log_content)
    
    assert len(parsed.stages) == 2
    assert parsed.stages[0].name == "Stage 1"
    assert parsed.stages[1].name == "Stage 2"


def test_auto_detect_platform():
    """Test automatic platform detection"""
    jenkins_log = "[Pipeline] Start\nRunning on Jenkins"
    github_log = "##[group]Setup\n::error::Failed"
    
    parsed_jenkins = parse_log(jenkins_log)
    parsed_github = parse_log(github_log)
    
    assert parsed_jenkins.platform == Platform.JENKINS
    assert parsed_github.platform == Platform.GITHUB_ACTIONS
