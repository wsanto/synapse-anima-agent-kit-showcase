"""Storage provider abstractions for Synapse Anima Agent Kit."""

from .base import BaseStorageProvider
from .memory import InMemoryStorageProvider

__all__ = [
    "BaseStorageProvider",
    "InMemoryStorageProvider",
]

# Optional imports for Neo4j (requires neo4j package)
try:
    from .neo4j import Neo4jStorageProvider
    __all__.append("Neo4jStorageProvider")
except ImportError:
    Neo4jStorageProvider = None

# Optional imports for Supabase (requires supabase package)
try:
    from .supabase import SupabaseStorageProvider
    __all__.append("SupabaseStorageProvider")
except ImportError:
    SupabaseStorageProvider = None
