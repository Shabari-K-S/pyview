"""Function caching and memoization decorators for PyView."""

from __future__ import annotations

from collections import OrderedDict
from functools import wraps
import hashlib
import pickle
import threading
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _compute_func_prefix(func: Callable[..., Any]) -> bytes:
    """Precompute deterministic bytecode/name digest once per wrapped function."""
    hasher = hashlib.sha256()
    hasher.update(func.__name__.encode("utf-8"))
    code_obj = getattr(func, "__code__", None)
    if code_obj is not None:
        hasher.update(code_obj.co_code)
    return hasher.digest()


def _hash_args(prefix: bytes, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Generate a deterministic hash string from precomputed prefix and call arguments."""
    hasher = hashlib.sha256(prefix)
    try:
        args_bytes = pickle.dumps((args, sorted(kwargs.items())))
        hasher.update(args_bytes)
    except Exception:
        hasher.update(repr((args, sorted(kwargs.items()))).encode("utf-8"))
    return hasher.hexdigest()


class CacheDataWrapper:
    """Wrapper class implementing @cache_data behavior with TTL, max_entries, and .clear()."""

    def __init__(
        self,
        func: Callable[..., Any],
        ttl: float | None = None,
        max_entries: int | None = None,
        show_spinner: bool = True,
    ) -> None:
        self.func = func
        self.ttl = float(ttl) if ttl is not None else None
        self.max_entries = int(max_entries) if max_entries is not None else None
        self.show_spinner = show_spinner
        self._func_prefix = _compute_func_prefix(func)
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        wraps(func)(self)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = _hash_args(self._func_prefix, args, kwargs)
        now = time.time()

        with self._lock:
            if key in self._cache:
                timestamp, result = self._cache[key]
                if self.ttl is None or (now - timestamp) < self.ttl:
                    self._cache.move_to_end(key)
                    return result
                else:
                    # Expired
                    del self._cache[key]

        # Execute function
        result = self.func(*args, **kwargs)

        with self._lock:
            # Enforce max_entries O(1) LRU eviction if specified
            if self.max_entries is not None and len(self._cache) >= self.max_entries:
                self._cache.popitem(last=False)

            self._cache[key] = (now, result)

        return result

    def clear(self) -> None:
        """Clear all cached entries for this function."""
        with self._lock:
            self._cache.clear()


class CacheResourceWrapper:
    """Wrapper class implementing @cache_resource behavior (singleton/global across sessions)."""

    def __init__(
        self,
        func: Callable[..., Any],
        ttl: float | None = None,
        max_entries: int | None = None,
        show_spinner: bool = True,
    ) -> None:
        self.func = func
        self.ttl = float(ttl) if ttl is not None else None
        self.max_entries = int(max_entries) if max_entries is not None else None
        self.show_spinner = show_spinner
        self._func_prefix = _compute_func_prefix(func)
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        wraps(func)(self)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = _hash_args(self._func_prefix, args, kwargs)
        now = time.time()

        with self._lock:
            if key in self._cache:
                timestamp, resource = self._cache[key]
                if self.ttl is None or (now - timestamp) < self.ttl:
                    self._cache.move_to_end(key)
                    return resource
                else:
                    del self._cache[key]

        # Execute initializer
        resource = self.func(*args, **kwargs)

        with self._lock:
            if self.max_entries is not None and len(self._cache) >= self.max_entries:
                self._cache.popitem(last=False)

            self._cache[key] = (now, resource)

        return resource

    def clear(self) -> None:
        """Clear all cached resources for this function."""
        with self._lock:
            self._cache.clear()


def cache_data(
    func: F | None = None,
    *,
    ttl: float | None = None,
    max_entries: int | None = None,
    show_spinner: bool = True,
) -> Callable[[F], CacheDataWrapper] | CacheDataWrapper:
    """Memoization decorator for data loading and pure computations.

    Can be used with or without parentheses:
    ```python
    @pv.cache_data
    def load_data(): ...

    @pv.cache_data(ttl=3600, max_entries=50)
    def fetch_records(query): ...
    ```
    """
    def decorator(fn: F) -> CacheDataWrapper:
        return CacheDataWrapper(fn, ttl=ttl, max_entries=max_entries, show_spinner=show_spinner)

    if func is not None:
        return decorator(func)
    return decorator


def cache_resource(
    func: F | None = None,
    *,
    ttl: float | None = None,
    max_entries: int | None = None,
    show_spinner: bool = True,
) -> Callable[[F], CacheResourceWrapper] | CacheResourceWrapper:
    """Singleton memoization decorator for global resources (ML models, DB connection pools).

    Can be used with or without parentheses:
    ```python
    @pv.cache_resource
    def get_database_engine(): ...

    @pv.cache_resource(ttl=86400)
    def load_neural_net(): ...
    ```
    """
    def decorator(fn: F) -> CacheResourceWrapper:
        return CacheResourceWrapper(fn, ttl=ttl, max_entries=max_entries, show_spinner=show_spinner)

    if func is not None:
        return decorator(func)
    return decorator
