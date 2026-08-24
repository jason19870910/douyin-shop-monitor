"""Database migration framework.

Supports both:
1. Manual SQL-based migrations (for simple deployments)
2. Alembic integration (for SQLAlchemy-based deployments)

Migration files should be named: V{version}__{description}.py
Example: V001__initial_schema.py, V002__add_compliance_tables.py
"""
import os
import re
import json
import logging
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Represents a single migration."""
    version: int
    name: str
    filename: str
    upgrade_fn: Callable[[], None]
    downgrade_fn: Optional[Callable[[], None]] = None
    description: str = ""
    checksum: str = ""
    applied_at: Optional[datetime] = None


class MigrationBackend(ABC):
    """Abstract base class for migration backends."""
    
    @abstractmethod
    def get_applied_versions(self) -> List[int]:
        """Get list of applied migration versions."""
        pass
    
    @abstractmethod
    def record_migration(self, migration: Migration) -> None:
        """Record a migration as applied."""
        pass
    
    @abstractmethod
    def remove_migration_record(self, version: int) -> None:
        """Remove migration record (for rollback)."""
        pass
    
    @abstractmethod
    def execute_sql(self, sql: str) -> None:
        """Execute raw SQL."""
        pass


class JSONFileBackend(MigrationBackend):
    """Migration backend using JSON file for tracking (no database required)."""
    
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.state_file = migrations_dir / ".migration_state.json"
        self._ensure_state_file()
    
    def _ensure_state_file(self):
        """Create state file if it doesn't exist."""
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({"applied_migrations": []}))
    
    def get_applied_versions(self) -> List[int]:
        import json
        try:
            data = json.loads(self.state_file.read_text())
            return sorted(data.get("applied_migrations", []))
        except Exception:
            return []
    
    def record_migration(self, migration: Migration) -> None:
        import json
        applied = self.get_applied_versions()
        if migration.version not in applied:
            applied.append(migration.version)
            applied.sort()
            self.state_file.write_text(json.dumps({
                "applied_migrations": applied,
                "last_updated": datetime.now().isoformat()
            }))
    
    def remove_migration_record(self, version: int) -> None:
        import json
        applied = self.get_applied_versions()
        if version in applied:
            applied.remove(version)
            self.state_file.write_text(json.dumps({
                "applied_migrations": applied,
                "last_updated": datetime.now().isoformat()
            }))
    
    def execute_sql(self, sql: str) -> None:
        """Execute SQL (no-op for JSON backend - migrations must handle their own persistence)."""
        logger.warning("JSON backend: execute_sql is no-op. Migration must handle persistence.")


class DatabaseBackend(MigrationBackend):
    """Migration backend using a database table for tracking."""
    
    def __init__(self, connection_string: str, table_name: str = "migration_history"):
        self.connection_string = connection_string
        self.table_name = table_name
        self._init_table()
    
    def _init_table(self):
        """Create migration history table if not exists."""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            version INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            checksum VARCHAR(64),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_sql(sql)
    
    def get_applied_versions(self) -> List[int]:
        sql = f"SELECT version FROM {self.table_name} ORDER BY version"
        # Implementation depends on database driver
        # This is a placeholder - actual implementation would use SQLAlchemy or raw driver
        raise NotImplementedError("DatabaseBackend requires SQLAlchemy or specific driver")
    
    def record_migration(self, migration: Migration) -> None:
        raise NotImplementedError("DatabaseBackend requires SQLAlchemy or specific driver")
    
    def remove_migration_record(self, version: int) -> None:
        raise NotImplementedError("DatabaseBackend requires SQLAlchemy or specific driver")
    
    def execute_sql(self, sql: str) -> None:
        raise NotImplementedError("DatabaseBackend requires SQLAlchemy or specific driver")


class SQLAlchemyBackend(MigrationBackend):
    """Migration backend using SQLAlchemy."""
    
    def __init__(self, engine):
        self.engine = engine
        self._init_table()
    
    def _init_table(self):
        from sqlalchemy import text, Table, Column, Integer, String, Text, DateTime, MetaData
        metadata = MetaData()
        migration_table = Table(
            'migration_history', metadata,
            Column('version', Integer, primary_key=True),
            Column('name', String(255), nullable=False),
            Column('description', Text),
            Column('checksum', String(64)),
            Column('applied_at', DateTime, default=datetime.utcnow)
        )
        metadata.create_all(self.engine)
    
    def get_applied_versions(self) -> List[int]:
        from sqlalchemy import text
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT version FROM migration_history ORDER BY version"))
            return [row[0] for row in result]
    
    def record_migration(self, migration: Migration) -> None:
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO migration_history (version, name, description, checksum, applied_at)
                VALUES (:version, :name, :description, :checksum, :applied_at)
            """), {
                "version": migration.version,
                "name": migration.name,
                "description": migration.description,
                "checksum": migration.checksum,
                "applied_at": migration.applied_at or datetime.utcnow()
            })
            conn.commit()
    
    def remove_migration_record(self, version: int) -> None:
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM migration_history WHERE version = :version"), {"version": version})
            conn.commit()
    
    def execute_sql(self, sql: str) -> None:
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()


class MigrationManager:
    """Manages migration discovery, execution, and rollback."""
    
    def __init__(self, migrations_dir: Path, backend: MigrationBackend):
        self.migrations_dir = migrations_dir
        self.backend = backend
        self.migrations: Dict[int, Migration] = {}
        self._discover_migrations()
    
    def _discover_migrations(self):
        """Discover migration files in the migrations directory."""
        pattern = re.compile(r'^V(\d+)__(.+)\.py$')
        
        for file_path in sorted(self.migrations_dir.glob("V*.py")):
            match = pattern.match(file_path.name)
            if not match:
                logger.warning(f"Skipping invalid migration filename: {file_path.name}")
                continue
            
            version = int(match.group(1))
            name = match.group(2)
            
            # Load migration module
            spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load migration: {file_path}")
                continue
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Extract upgrade/downgrade functions
            upgrade_fn = getattr(module, 'upgrade', None)
            downgrade_fn = getattr(module, 'downgrade', None)
            
            if upgrade_fn is None:
                logger.error(f"Migration {file_path.name} missing 'upgrade' function")
                continue
            
            # Get description from module docstring
            description = module.__doc__ or ""
            
            migration = Migration(
                version=version,
                name=name,
                filename=file_path.name,
                upgrade_fn=upgrade_fn,
                downgrade_fn=downgrade_fn,
                description=description
            )
            
            self.migrations[version] = migration
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet."""
        applied = set(self.backend.get_applied_versions())
        return [
            m for v, m in sorted(self.migrations.items())
            if v not in applied
        ]
    
    def get_applied_migrations(self) -> List[Migration]:
        """Get migrations that have been applied."""
        applied = set(self.backend.get_applied_versions())
        return [
            m for v, m in sorted(self.migrations.items())
            if v in applied
        ]
    
    def migrate(self, target_version: Optional[int] = None) -> List[Migration]:
        """Apply pending migrations up to target_version."""
        pending = self.get_pending_migrations()
        
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]
        
        applied = []
        for migration in pending:
            logger.info(f"Applying migration V{migration.version:03d}: {migration.name}")
            try:
                migration.upgrade_fn()
                migration.applied_at = datetime.now()
                self.backend.record_migration(migration)
                applied.append(migration)
                logger.info(f"Migration V{migration.version:03d} applied successfully")
            except Exception as e:
                logger.error(f"Migration V{migration.version:03d} failed: {e}")
                raise
        
        return applied
    
    def rollback(self, target_version: int) -> List[Migration]:
        """Rollback migrations down to target_version."""
        applied = self.get_applied_migrations()
        to_rollback = [m for m in reversed(applied) if m.version > target_version]
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return []
        
        rolled_back = []
        for migration in to_rollback:
            if migration.downgrade_fn is None:
                raise ValueError(f"Migration V{migration.version:03d} has no downgrade function")
            
            logger.info(f"Rolling back migration V{migration.version:03d}: {migration.name}")
            try:
                migration.downgrade_fn()
                self.backend.remove_migration_record(migration.version)
                rolled_back.append(migration)
                logger.info(f"Migration V{migration.version:03d} rolled back successfully")
            except Exception as e:
                logger.error(f"Rollback of V{migration.version:03d} failed: {e}")
                raise
        
        return rolled_back
    
    def status(self) -> Dict[str, Any]:
        """Get migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "applied_at": m.applied_at.isoformat() if m.applied_at else None
                }
                for m in applied
            ],
            "pending": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description
                }
                for m in pending
            ]
        }


def create_backend(backend_type: str, **kwargs) -> MigrationBackend:
    """Factory function to create migration backend."""
    if backend_type == "json":
        migrations_dir = kwargs.get("migrations_dir", Path("migrations"))
        return JSONFileBackend(migrations_dir)
    elif backend_type == "sqlalchemy":
        from sqlalchemy import create_engine
        engine = create_engine(kwargs["connection_string"])
        return SQLAlchemyBackend(engine)
    elif backend_type == "database":
        return DatabaseBackend(kwargs["connection_string"])
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


def get_migration_manager(
    migrations_dir: Path = None,
    backend: MigrationBackend = None,
    backend_type: str = "json",
    **backend_kwargs
) -> MigrationManager:
    """Get migration manager instance."""
    if migrations_dir is None:
        migrations_dir = Path(__file__).parent
    
    if backend is None:
        backend = create_backend(backend_type, migrations_dir=migrations_dir, **backend_kwargs)
    
    return MigrationManager(migrations_dir, backend)


# Convenience functions for manual migrations
def create_migration_template(migrations_dir: Path, version: int, name: str) -> Path:
    """Create a new migration file from template."""
    filename = f"V{version:03d}__{name}.py"
    file_path = migrations_dir / filename
    
    if file_path.exists():
        raise FileExistsError(f"Migration file already exists: {file_path}")
    
    template = f'''"""
Migration V{version:03d}: {name}
{name.replace('_', ' ').title()}

Run: python -m migrations.migrate
"""
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration."""
    logger.info(f"Applying migration V{version:03d}: {name}")
    # TODO: Add your upgrade logic here
    # Example:
    # from services.fetcher import cache, CACHE_KEYS
    # cache.set(CACHE_KEYS['new_key'], [])
    
    logger.info(f"Migration V{version:03d} completed")


def downgrade():
    """Rollback migration."""
    logger.info(f"Rolling back migration V{version:03d}: {name}")
    # TODO: Add your rollback logic here
    # Example:
    # from services.fetcher import cache, CACHE_KEYS
    # cache.delete(CACHE_KEYS['new_key'])
    
    logger.info(f"Migration V{version:03d} rolled back")
'''
    
    file_path.write_text(template)
    logger.info(f"Created migration template: {file_path}")
    return file_path


# CLI entry point
def main():
    """Command-line interface for migrations."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m migrations <command> [args]")
        print("Commands:")
        print("  status              - Show migration status")
        print("  migrate [version]   - Apply pending migrations (up to version)")
        print("  rollback <version>  - Rollback to version")
        print("  create <version> <name> - Create new migration template")
        sys.exit(1)
    
    command = sys.argv[1]
    migrations_dir = Path(__file__).parent
    
    manager = get_migration_manager(migrations_dir)
    
    if command == "status":
        status = manager.status()
        print(f"Total: {status['total_migrations']}, Applied: {status['applied_count']}, Pending: {status['pending_count']}")
        print("\\nApplied:")
        for m in status['applied']:
            print(f"  V{m['version']:03d}: {m['name']} ({m['applied_at']})")
        print("\\nPending:")
        for m in status['pending']:
            print(f"  V{m['version']:03d}: {m['name']}")
    
    elif command == "migrate":
        target_version = int(sys.argv[2]) if len(sys.argv) > 2 else None
        applied = manager.migrate(target_version)
        print(f"Applied {len(applied)} migration(s)")
    
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("Usage: python -m migrations rollback <target_version>")
            sys.exit(1)
        target_version = int(sys.argv[2])
        rolled_back = manager.rollback(target_version)
        print(f"Rolled back {len(rolled_back)} migration(s)")
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("Usage: python -m migrations create <version> <name>")
            sys.exit(1)
        version = int(sys.argv[2])
        name = sys.argv[3]
        create_migration_template(migrations_dir, version, name)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()