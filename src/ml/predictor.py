import joblib
import numpy as np
import re
from pathlib import Path
from scipy.sparse import hstack


class ErrorClassifier:
    """
    ML error classifier for CI/CD logs (Random Forest + TF-IDF)
    
    Usage:
        clf = ErrorClassifier()
        result = clf.predict(log_text, platform)
    """
    
    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = Path(__file__).parent.parent.parent / 'models'
        
        self.model = joblib.load(model_dir / 'error_classifier_rf.pkl')
        self.vectorizer = joblib.load(model_dir / 'tfidf_vectorizer.pkl')
        self.label_encoder = joblib.load(model_dir / 'label_encoder.pkl')
        self.feature_info = joblib.load(model_dir / 'feature_info.pkl')
    
    def _preprocess_text(self, text):
        """Clean and preprocess log text (same as training)"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove timestamps
        text = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '', text)
        text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', 'URL', text)
        
        # Remove file paths (but keep file names)
        text = re.sub(r'/[a-z0-9_\-/]+/', ' ', text)
        
        # Remove build numbers
        text = re.sub(r'#\d+', '', text)
        
        # Remove version numbers (keep semantic meaning)
        text = re.sub(r'\d+\.\d+\.\d+', 'VERSION', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_structural_features(self, content):
        """Extract structural features from log (enhanced version)"""
        features = {
            # Length features
            'log_length': len(content),
            'num_lines': content.count('\n'),
            
            # Error patterns
            'has_error_keyword': int(bool(re.search(r'\berror\b', content, re.I))),
            'has_failed_keyword': int(bool(re.search(r'\bfailed\b', content, re.I))),
            'has_exception': int(bool(re.search(r'\bexception\b', content, re.I))),
            'has_timeout': int(bool(re.search(r'\btimeout\b|\btimed out\b', content, re.I))),
            
            # Error code patterns
            'has_npm_error': int(bool(re.search(r'\bERR!|\bE[A-Z]+\b', content))),
            'has_pip_error': int(bool(re.search(r'\bERROR:', content))),
            'has_ts_error': int(bool(re.search(r'\bTS\d+\b', content))),
            'has_syntax_error': int(bool(re.search(r'SyntaxError|IndentationError', content))),
            
            # Test patterns
            'has_test_failed': int(bool(re.search(r'\btest.*failed\b|\bfailed.*test\b', content, re.I))),
            'has_assertion_error': int(bool(re.search(r'AssertionError|expect.*received', content))),
            
            # Stack trace
            'has_stack_trace': int(bool(re.search(r'\s+at\s+.*\(.*:\d+:\d+\)', content))),
            
            # Exit codes
            'has_exit_code': int(bool(re.search(r'exit code|exit status', content, re.I))),
            
            # === NEW ENHANCED FEATURES ===
            
            # Dependency-specific patterns (STRONGEST signal for dependency_error)
            'has_module_not_found': int(bool(re.search(r'module not found|cannot find module|modulenotfounderror', content, re.I))),
            'has_package_not_found': int(bool(re.search(r'package.*not found|no such file or directory', content, re.I))),
            'has_shared_library': int(bool(re.search(r'shared librar|\.so\.\d+|cannot open shared object', content, re.I))),
            'has_dependency_conflict': int(bool(re.search(r'conflict|incompatible|peer dep', content, re.I))),
            'has_npm_install': int(bool(re.search(r'npm (install|i\b)|npm ERR!', content, re.I))),
            'has_pip_install': int(bool(re.search(r'pip install|No module named', content, re.I))),
            
            # Syntax-specific patterns
            'has_unexpected_token': int(bool(re.search(r'unexpected token|unexpected identifier', content, re.I))),
            'has_expected_bracket': int(bool(re.search(r'expected.*[\{\}\[\]\(\)]', content, re.I))),
            'has_indentation_error': int(bool(re.search(r'indentation|unexpected indent', content, re.I))),
            'has_unterminated': int(bool(re.search(r'unterminated|unmatched', content, re.I))),
            
            # Test-specific patterns
            'has_test_assertion': int(bool(re.search(r'assert|expected.*but (got|received)', content, re.I))),
            'has_test_timeout': int(bool(re.search(r'test.*timeout|jasmine|mocha|jest', content, re.I))),
            
            # Docker-specific
            'has_docker_error': int(bool(re.search(r'docker|dockerfile|container|image', content, re.I))),
            'has_docker_build': int(bool(re.search(r'docker build|building.*image', content, re.I))),
            
            # Network/deployment
            'has_connection_error': int(bool(re.search(r'connection.*refused|network.*error|ECONNREFUSED', content, re.I))),
            'has_auth_error': int(bool(re.search(r'authentication|unauthorized|403|401', content, re.I))),
            
            # Environment
            'has_env_var': int(bool(re.search(r'environment variable|env.*not (set|defined)', content, re.I))),
            'has_permission': int(bool(re.search(r'permission denied|access denied|EACCES', content, re.I))),
            
            # Count features (stronger signals)
            'error_count': len(re.findall(r'\berror\b', content, re.I)),
            'failed_count': len(re.findall(r'\bfailed\b', content, re.I)),
            'warning_count': len(re.findall(r'\bwarn(ing)?\b', content, re.I)),
        }
        
        return np.array([[
            features['log_length'],
            features['num_lines'],
            features['has_error_keyword'],
            features['has_failed_keyword'],
            features['has_exception'],
            features['has_timeout'],
            features['has_npm_error'],
            features['has_pip_error'],
            features['has_ts_error'],
            features['has_syntax_error'],
            features['has_test_failed'],
            features['has_assertion_error'],
            features['has_stack_trace'],
            features['has_exit_code'],
            # New features
            features['has_module_not_found'],
            features['has_package_not_found'],
            features['has_shared_library'],
            features['has_dependency_conflict'],
            features['has_npm_install'],
            features['has_pip_install'],
            features['has_unexpected_token'],
            features['has_expected_bracket'],
            features['has_indentation_error'],
            features['has_unterminated'],
            features['has_test_assertion'],
            features['has_test_timeout'],
            features['has_docker_error'],
            features['has_docker_build'],
            features['has_connection_error'],
            features['has_auth_error'],
            features['has_env_var'],
            features['has_permission'],
            features['error_count'],
            features['failed_count'],
            features['warning_count'],
        ]])
    
    def extract_features(self, log_text, platform):
        """
        Extract features from log text
        
        Args:
            log_text: Raw log content
            platform: CI/CD platform (jenkins, github-actions, gitlab-ci)
            
        Returns:
            Feature matrix ready for model.predict()
        """
        # Preprocess text
        clean_text = self._preprocess_text(log_text)
        
        # TF-IDF features
        X_tfidf = self.vectorizer.transform([clean_text])
        
        # Structural features
        X_struct_full = self._extract_structural_features(log_text)
        
        # Check if model expects old (14) or new (35) features
        # By checking the trained model's n_features_in_
        expected_features = getattr(self.model, 'n_features_in_', None)
        tfidf_features = X_tfidf.shape[1]
        
        platforms = self.feature_info['platform_feature_names']
        platform_features = len(platforms)
        
        # Calculate expected structural features
        if expected_features:
            expected_structural = expected_features - tfidf_features - platform_features
        else:
            expected_structural = 14  # Old default
        
        # Use only the first N features if model expects fewer
        if X_struct_full.shape[1] > expected_structural:
            # Backward compatibility: use only old features
            X_struct = X_struct_full[:, :expected_structural]
        else:
            X_struct = X_struct_full
        
        # Platform one-hot encoding
        plat_vec = np.zeros((1, len(platforms)))
        
        # Map platform name to feature name
        platform_normalized = platform.lower().replace('_', '-')
        platform_feature = f'platform_{platform_normalized}'
        
        if platform_feature in platforms:
            idx = platforms.index(platform_feature)
            plat_vec[0, idx] = 1
        
        # Combine all features: TF-IDF + Structural + Platform
        X = hstack([X_tfidf, X_struct, plat_vec])
        
        return X, X_struct_full  # Return both for rule-based boosting
    
    def predict(self, log_text, platform='github-actions'):
        """
        Predict error category from log text with enhanced confidence
        
        Args:
            log_text: Raw log content
            platform: CI/CD platform
            
        Returns:
            Dictionary with error_type, confidence, and probabilities
        """
        # Extract features (returns both compatible and full features)
        X, X_struct_full = self.extract_features(log_text, platform)
        
        # Predict with Random Forest
        proba = self.model.predict_proba(X)[0]
        idx = np.argmax(proba)
        
        error_type = self.label_encoder.classes_[idx]
        base_confidence = float(proba[idx])
        
        # === AGGRESSIVE PATTERN-BASED RE-CLASSIFICATION ===
        # Override ML prediction if very clear patterns detected
        # This fixes cases where ML model was trained on insufficient data
        # Note: Only reclassify to error types that exist in the model
        log_lower = log_text.lower()
        
        reclassification_patterns = {
            'environment_error': [
                ('exit code 127' in log_lower, 0.95, 'Exit code 127 = command not found'),
                ('exit code 126' in log_lower, 0.92, 'Exit code 126 = permission denied'),
                ('docker: not found' in log_lower or 'node: not found' in log_lower or 'python: not found' in log_lower, 0.90, 'Command not found pattern'),
                ('command not found' in log_lower and any(cmd in log_lower for cmd in ['docker', 'node', 'python', 'java', 'npm', 'git', 'gcc']), 0.88, 'Specific command not found'),
                # Docker errors also go to environment_error (since docker_error not in model)
                ('failed to pull' in log_lower and 'docker' in log_lower, 0.90, 'Docker pull failed (environment issue)'),
                ('manifest' in log_lower and 'not found' in log_lower and ('docker' in log_lower or 'image' in log_lower), 0.88, 'Docker manifest error (environment issue)'),
            ],
            'network_error': [
                ('connection timed out' in log_lower, 0.92, 'Connection timeout'),
                ('could not resolve host' in log_lower, 0.90, 'DNS resolution failed'),
                # Chỉ reclassify network_error nếu KHÔNG PHẢI Python/NPM import errors
                ('econnrefused' in log_lower and 'modulenotfounderror' not in log_lower and 'cannot find module' not in log_lower, 0.88, 'Network error codes (ECONNREFUSED)'),
                ('etimedout' in log_lower and 'import' not in log_lower, 0.88, 'Network error codes (ETIMEDOUT)'),
                ('enotfound' in log_lower and 'module' not in log_lower and 'import' not in log_lower, 0.88, 'Network error codes (ENOTFOUND)'),
                ('connection refused' in log_lower and 'network' not in log_lower and 'import' not in log_lower, 0.85, 'Connection refused'),
            ],
            'dependency_error': [
                ('modulenotfounderror' in log_lower or 'module not found' in log_lower, 0.92, 'Python module not found'),
                ('cannot find module' in log_lower, 0.90, 'NPM module not found'),
                ('importerror' in log_lower and 'no module named' in log_lower, 0.90, 'Python import error'),
                ('shared librar' in log_lower and '.so' in log_lower, 0.88, 'Shared library missing'),
            ],
            'syntax_error': [
                ('syntaxerror' in log_lower and 'unexpected' in log_lower, 0.92, 'SyntaxError with unexpected token'),
                ('parse error' in log_lower or 'parsing failed' in log_lower, 0.88, 'Parse error'),
            ],
            'test_failure': [
                ('assertionerror' in log_lower and 'expected' in log_lower, 0.92, 'AssertionError with expectation'),
                (('test' in log_lower or 'spec' in log_lower) and 'failed' in log_lower and ('expected' in log_lower or 'assert' in log_lower), 0.88, 'Test assertion failure'),
            ],
        }
        
        # Check for reclassification
        reclassify_to = None
        reclassify_confidence = 0.0
        reclassify_reason = None
        
        for target_error_type, patterns in reclassification_patterns.items():
            for pattern_condition, pattern_confidence, reason in patterns:
                if pattern_condition and pattern_confidence > base_confidence:
                    if pattern_confidence > reclassify_confidence:
                        reclassify_to = target_error_type
                        reclassify_confidence = pattern_confidence
                        reclassify_reason = reason
        
        # Apply reclassification if found
        reclassified = False
        if reclassify_to is not None:
            # Verify that the target error type exists in the model
            if reclassify_to in self.label_encoder.classes_:
                original_error_type = error_type
                original_confidence = base_confidence
                error_type = reclassify_to
                base_confidence = reclassify_confidence
                reclassified = True
                
                # Find index of new error type
                idx = np.where(self.label_encoder.classes_ == reclassify_to)[0][0]
            else:
                # Target error type not in model, skip reclassification
                pass
        
        # === ENHANCED CONFIDENCE BOOSTING ===
        # Multi-level signal detection with higher boost values
        confidence_boost = 0.0
        detected_signals = []
        
        # Strong signals for each error type
        log_lower = log_text.lower()
        
        if error_type == 'dependency_error':
            # TIER 1: Very strong signals (each worth 0.15-0.30)
            tier1_signals = [
                ('shared librar' in log_lower and '.so' in log_lower, 0.30, 'System library (.so) error'),
                ('cannot open shared object' in log_lower, 0.28, 'Shared object not found'),
                ('libatomic' in log_lower or 'libssl' in log_lower or 'libpq' in log_lower, 0.25, 'Specific library missing'),
            ]
            
            # TIER 2: Strong signals (each worth 0.10-0.20)
            tier2_signals = [
                ('module not found' in log_lower or 'modulenotfounderror' in log_lower, 0.20, 'Module not found'),
                ('cannot find module' in log_lower, 0.18, 'Cannot find module'),
                ('npm err' in log_lower and 'elifecycle' not in log_lower, 0.15, 'NPM error'),
                ('no such file or directory' in log_lower and ('lib' in log_lower or 'package' in log_lower), 0.15, 'Package file missing'),
                ('peer dep' in log_lower or 'peerDependenc' in log_lower, 0.12, 'Peer dependency issue'),
            ]
            
            # TIER 3: Medium signals (each worth 0.05-0.10)
            tier3_signals = [
                ('package' in log_lower and 'not found' in log_lower, 0.10, 'Package not found'),
                ('importerror' in log_lower or 'import error' in log_lower, 0.08, 'Python import error'),
                ('could not find' in log_lower or 'unable to locate' in log_lower, 0.08, 'Unable to locate'),
                ('missing' in log_lower and ('dependency' in log_lower or 'package' in log_lower), 0.08, 'Missing dependency'),
            ]
            
            # Negative signals: Detect misclassification as dependency_error
            negative_signals = [
                (('syntaxerror' in log_lower or 'unexpected token' in log_lower or 
                  ('expected' in log_lower and any(punct in log_lower for punct in ["'}'", "'}'", "';'", "','"]))), 
                 -0.15, 'Actually syntax error (penalize)'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals + negative_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    if boost > 0:
                        detected_signals.append(f"{description} (+{boost:.0%})")
                    else:
                        detected_signals.append(f"⚠️ {description}")
                    
        elif error_type == 'syntax_error':
            all_signals = [
                ('syntaxerror' in log_lower, 0.25, 'SyntaxError keyword'),
                ('unexpected token' in log_lower or 'unexpected identifier' in log_lower, 0.20, 'Unexpected token'),
                ('expected' in log_lower and any(c in log_lower for c in ['{', '}', '[', ']', '(', ')']), 0.15, 'Expected bracket/brace'),
                ('unterminated' in log_lower or 'unmatched' in log_lower, 0.18, 'Unterminated/unmatched'),
                ('indentation' in log_lower or 'unexpected indent' in log_lower, 0.15, 'Indentation error'),
                ('parse error' in log_lower or 'parsing' in log_lower, 0.12, 'Parse error'),
                # Add weak signals to help misclassified cases
                ('expected' in log_lower and 'found' in log_lower, 0.10, 'Expected vs found'),
                ("'" in log_text and '"' in log_text and ('unterminated' in log_lower or 'expected' in log_lower), 0.08, 'Quote mismatch'),
            ]
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
                    
        elif error_type == 'test_failure':
            all_signals = [
                ('assertionerror' in log_lower, 0.25, 'AssertionError'),
                ('expected' in log_lower and ('received' in log_lower or 'but got' in log_lower), 0.20, 'Assertion mismatch'),
                ('test' in log_lower and 'failed' in log_lower, 0.12, 'Test failed'),
                ('assert' in log_lower and ('equal' in log_lower or 'true' in log_lower or 'false' in log_lower), 0.15, 'Assert statement'),
                ('spec' in log_lower and 'fail' in log_lower, 0.10, 'Spec failure'),
            ]
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
                    
        elif error_type == 'timeout' or error_type == 'timeout_error':
            # TIER 1: Very strong signals
            tier1_signals = [
                ('timeout' in log_lower and 'exceeded' in log_lower, 0.30, 'Timeout exceeded'),
                ('timed out' in log_lower, 0.28, 'Timed out'),
                ('marking the build as aborted' in log_lower, 0.25, 'Build aborted (timeout)'),
            ]
            
            # TIER 2: Strong signals
            tier2_signals = [
                ('timeout of' in log_lower and 'ms' in log_lower, 0.20, 'Specific timeout value'),
                ('exceeded' in log_lower and ('time' in log_lower or 'limit' in log_lower), 0.18, 'Time limit exceeded'),
                ('deadline' in log_lower or 'time limit' in log_lower, 0.15, 'Deadline/time limit'),
            ]
            
            # TIER 3: Medium signals
            tier3_signals = [
                ('hung' in log_lower or 'hangs' in log_lower or 'hanging' in log_lower, 0.12, 'Process hung'),
                ('aborted' in log_lower and 'timeout' in log_lower, 0.10, 'Aborted due to timeout'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
                    
        elif error_type == 'environment_error':
            # TIER 1: Very strong signals
            tier1_signals = [
                ('command not found' in log_lower or 'not found' in log_lower and any(cmd in log_lower for cmd in ['docker', 'node', 'python', 'java', 'npm', 'gcc', 'git']), 0.30, 'Command not found'),
                ('exit code 127' in log_lower, 0.28, 'Exit code 127 (command not found)'),
                ('exit code 126' in log_lower, 0.25, 'Exit code 126 (permission denied)'),
            ]
            
            # TIER 2: Strong signals
            tier2_signals = [
                ('no such file' in log_lower and 'bin' in log_lower, 0.20, 'Binary not found'),
                ('permission denied' in log_lower or 'eacces' in log_lower, 0.18, 'Permission denied'),
                ('script.sh' in log_lower and 'not found' in log_lower, 0.15, 'Script not found'),
                ('env' in log_lower and ('not set' in log_lower or 'undefined' in log_lower), 0.15, 'Environment variable issue'),
            ]
            
            # TIER 3: Medium signals
            tier3_signals = [
                ('path' in log_lower and 'not found' in log_lower, 0.10, 'PATH issue'),
                ('executable' in log_lower and 'not found' in log_lower, 0.10, 'Executable not found'),
            ]
            
            # Negative signals: Detect misclassification
            negative_signals = [
                ('shared librar' in log_lower or 'cannot open shared object' in log_lower, -0.20, 'Actually dependency error (penalize)'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals + negative_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    if boost > 0:
                        detected_signals.append(f"{description} (+{boost:.0%})")
                    else:
                        # Negative signal - suggest reclassification
                        detected_signals.append(f"⚠️ {description}")
        
        elif error_type == 'docker_error':
            # TIER 1: Very strong signals
            tier1_signals = [
                ('docker' in log_lower and 'error' in log_lower, 0.30, 'Docker error'),
                ('failed to pull' in log_lower or 'pull access denied' in log_lower, 0.28, 'Docker pull failed'),
                ('manifest' in log_lower and ('not found' in log_lower or 'unknown' in log_lower), 0.25, 'Docker manifest error'),
            ]
            
            # TIER 2: Strong signals
            tier2_signals = [
                ('dockerfile' in log_lower and 'error' in log_lower, 0.20, 'Dockerfile error'),
                ('docker build' in log_lower and 'failed' in log_lower, 0.18, 'Docker build failed'),
                ('container' in log_lower and ('exited' in log_lower or 'stopped' in log_lower), 0.15, 'Container stopped'),
                ('image' in log_lower and 'not found' in log_lower, 0.15, 'Image not found'),
            ]
            
            # TIER 3: Medium signals
            tier3_signals = [
                ('docker daemon' in log_lower, 0.10, 'Docker daemon issue'),
                ('registry' in log_lower and 'error' in log_lower, 0.10, 'Registry error'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
        
        elif error_type == 'deployment_error':
            # TIER 1: Very strong signals
            tier1_signals = [
                ('deployment failed' in log_lower or 'deploy' in log_lower and 'failed' in log_lower, 0.30, 'Deployment failed'),
                ('rollback' in log_lower, 0.28, 'Rollback triggered'),
                ('connection refused' in log_lower and 'deploy' in log_lower, 0.25, 'Deployment connection refused'),
            ]
            
            # TIER 2: Strong signals
            tier2_signals = [
                ('kubectl' in log_lower and 'error' in log_lower, 0.20, 'Kubectl error'),
                ('kubernetes' in log_lower and 'failed' in log_lower, 0.18, 'Kubernetes failure'),
                ('service unavailable' in log_lower, 0.15, 'Service unavailable'),
                ('health check failed' in log_lower, 0.15, 'Health check failed'),
            ]
            
            # TIER 3: Medium signals
            tier3_signals = [
                ('pod' in log_lower and ('crash' in log_lower or 'error' in log_lower), 0.10, 'Pod error'),
                ('replica' in log_lower and 'failed' in log_lower, 0.10, 'Replica failure'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
        
        elif error_type == 'network_error':
            # TIER 1: Very strong signals
            tier1_signals = [
                ('connection timed out' in log_lower or 'timeout' in log_lower and 'connection' in log_lower, 0.30, 'Connection timeout'),
                ('could not resolve host' in log_lower or 'name resolution' in log_lower, 0.28, 'DNS resolution failed'),
                ('connection refused' in log_lower, 0.25, 'Connection refused'),
            ]
            
            # TIER 2: Strong signals
            tier2_signals = [
                ('network' in log_lower and ('error' in log_lower or 'unreachable' in log_lower), 0.20, 'Network unreachable'),
                ('ssl' in log_lower and ('error' in log_lower or 'handshake' in log_lower), 0.18, 'SSL/TLS error'),
                ('certificate' in log_lower and ('invalid' in log_lower or 'expired' in log_lower), 0.15, 'Certificate error'),
                ('econnrefused' in log_lower or 'etimedout' in log_lower or 'enotfound' in log_lower, 0.15, 'Network error code'),
            ]
            
            # TIER 3: Medium signals
            tier3_signals = [
                ('http' in log_lower and ('timeout' in log_lower or 'error' in log_lower), 0.10, 'HTTP error'),
                ('socket' in log_lower and ('error' in log_lower or 'closed' in log_lower), 0.10, 'Socket error'),
            ]
            
            all_signals = tier1_signals + tier2_signals + tier3_signals
            for condition, boost, description in all_signals:
                if condition:
                    confidence_boost += boost
                    detected_signals.append(f"{description} (+{boost:.0%})")
        
        # === PATTERN COMBINATION BONUS ===
        # Extra boost for multiple strong signals (confidence in prediction)
        if len(detected_signals) >= 2:
            combination_boost = min(len(detected_signals) * 0.03, 0.10)  # Max +10% for multiple signals
            confidence_boost += combination_boost
            detected_signals.append(f"Multiple signals detected (+{combination_boost:.0%})")
        
        # Apply boost with dynamic cap based on base confidence
        # Higher base confidence allows higher final confidence
        if base_confidence >= 0.5:
            max_confidence = 0.98  # Very confident base allows near certainty
        elif base_confidence >= 0.3:
            max_confidence = 0.92  # Medium base allows high confidence
        else:
            max_confidence = 0.85  # Low base caps at good confidence
            
        enhanced_confidence = min(base_confidence + confidence_boost, max_confidence)
        
        # Normalize probabilities if boosted
        if confidence_boost > 0:
            # Redistribute probability mass
            other_proba_sum = 1.0 - base_confidence
            if other_proba_sum > 0:
                scale_factor = (1.0 - enhanced_confidence) / other_proba_sum
                enhanced_proba = {}
                for i, label in enumerate(self.label_encoder.classes_):
                    if i == idx:
                        enhanced_proba[label] = enhanced_confidence
                    else:
                        enhanced_proba[label] = float(proba[i] * scale_factor)
            else:
                enhanced_proba = {label: float(p) for label, p in zip(self.label_encoder.classes_, proba)}
                enhanced_proba[error_type] = enhanced_confidence
        else:
            enhanced_proba = {label: float(p) for label, p in zip(self.label_encoder.classes_, proba)}
        
        result = {
            'error_type': error_type,
            'confidence': enhanced_confidence,
            'base_confidence': base_confidence,
            'confidence_boost': confidence_boost,
            'detected_signals': detected_signals,  # For debugging
            'probabilities': enhanced_proba,
            'proba': proba
        }
        
        # Add reclassification info if applicable
        if reclassified:
            result['reclassified'] = True
            result['original_error_type'] = original_error_type
            result['original_confidence'] = original_confidence
            result['reclassification_reason'] = reclassify_reason
            detected_signals.insert(0, f"🔄 Reclassified from {original_error_type} ({original_confidence*100:.1f}%) → {error_type} ({base_confidence*100:.1f}%): {reclassify_reason}")
        
        return result

