"""
Cache Manager for LLM responses
Reduces API costs by caching results with TTL support
"""
import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import asdict


class CacheManager:
    """
    Disk-based cache manager with TTL support
    
    Features:
    - Hash-based keys (SHA256)
    - TTL (time-to-live) expiration
    - Disk storage for persistence
    - Cache statistics
    
    Expected hit rate: 50-70% after initial usage
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: int = 604800,  # 7 days in seconds
        enabled: bool = True,
    ):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache storage (default: ~/.ai-logguard/cache)
            ttl: Time-to-live in seconds (default: 7 days)
            enabled: Enable/disable caching
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".ai-logguard" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.enabled = enabled
        
        # Always initialize directory paths (even if disabled)
        self.summaries_dir = self.cache_dir / "summaries"
        self.explanations_dir = self.cache_dir / "explanations"
        self.fixes_dir = self.cache_dir / "fixes"
        
        # Create cache directories only if enabled
        if self.enabled:
            for dir_path in [self.summaries_dir, self.explanations_dir, self.fixes_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, content: str) -> str:
        """
        Generate cache key from content
        
        Args:
            content: Content to hash
        
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cache_path(self, key: str, cache_type: str = "summaries") -> Path:
        """Get full path to cache file"""
        type_dir_map = {
            "summaries": self.summaries_dir,
            "explanations": self.explanations_dir,
            "fixes": self.fixes_dir,
        }
        
        cache_dir = type_dir_map.get(cache_type, self.summaries_dir)
        return cache_dir / f"{key}.pkl"
    
    def get(
        self,
        content: str,
        cache_type: str = "summaries",
    ) -> Optional[Any]:
        """
        Get cached value if exists and not expired
        
        Args:
            content: Content to lookup (will be hashed)
            cache_type: Type of cache (summaries, explanations, fixes)
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(content)
        cache_path = self._get_cache_path(key, cache_type)
        
        if not cache_path.exists():
            self.misses += 1
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check TTL
            timestamp = cache_data.get('timestamp', 0)
            if time.time() - timestamp > self.ttl:
                # Expired
                cache_path.unlink()
                self.misses += 1
                return None
            
            # Cache hit
            self.hits += 1
            return cache_data.get('value')
        
        except (pickle.PickleError, KeyError, EOFError) as e:
            # Corrupted cache file
            if cache_path.exists():
                cache_path.unlink()
            self.misses += 1
            return None
    
    def set(
        self,
        content: str,
        value: Any,
        cache_type: str = "summaries",
    ):
        """
        Store value in cache
        
        Args:
            content: Content to use as key (will be hashed)
            value: Value to cache
            cache_type: Type of cache (summaries, explanations, fixes)
        """
        if not self.enabled:
            return
        
        key = self._generate_key(content)
        cache_path = self._get_cache_path(key, cache_type)
        
        cache_data = {
            'timestamp': time.time(),
            'value': value,
        }
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            # Fail silently - caching is optional
            pass
    
    def clear(self, cache_type: Optional[str] = None):
        """
        Clear cache
        
        Args:
            cache_type: Specific cache type to clear, or None for all
        """
        if not self.enabled:
            return
        
        if cache_type:
            cache_dir = self._get_cache_path("", cache_type).parent
            for cache_file in cache_dir.glob("*.pkl"):
                cache_file.unlink()
        else:
            # Clear all
            for dir_path in [self.summaries_dir, self.explanations_dir, self.fixes_dir]:
                for cache_file in dir_path.glob("*.pkl"):
                    cache_file.unlink()
        
        # Reset stats
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        # Count cache files
        cache_sizes = {}
        for name, dir_path in [
            ("summaries", self.summaries_dir),
            ("explanations", self.explanations_dir),
            ("fixes", self.fixes_dir),
        ]:
            if dir_path.exists():
                cache_sizes[name] = len(list(dir_path.glob("*.pkl")))
            else:
                cache_sizes[name] = 0
        
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_sizes": cache_sizes,
            "ttl": self.ttl,
            "cache_dir": str(self.cache_dir),
        }
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        if not self.enabled:
            return
        
        removed = 0
        current_time = time.time()
        
        for dir_path in [self.summaries_dir, self.explanations_dir, self.fixes_dir]:
            for cache_file in dir_path.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    timestamp = cache_data.get('timestamp', 0)
                    if current_time - timestamp > self.ttl:
                        cache_file.unlink()
                        removed += 1
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink()
                    removed += 1
        
        return removed
