"""Frontend blueprint for serving React app (optional fallback when Nginx is not used)."""
from __future__ import annotations

from flask import Blueprint, send_from_directory, abort
from pathlib import Path
from typing import Optional

frontend_bp = Blueprint('frontend', __name__)


def _resolve_build_dir() -> Optional[Path]:
    """Locate frontend build directory across common layouts."""
    backend_root = Path(__file__).resolve().parent.parent
    candidates = [
        # Monorepo: src/frontend/build (preferred)
        backend_root.parent / 'frontend' / 'build',
        # Copied into backend image: src/backend/frontend/build
        backend_root / 'frontend' / 'build',
        # Legacy opt path
        backend_root.parent.parent / 'opt' / 'douyin-platform' / 'apps' / 'monitor' / 'frontend' / 'build',
    ]
    for path in candidates:
        if (path / 'index.html').exists():
            return path
    return None


@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_frontend(path: str):
    """Serve React frontend SPA with history-fallback."""
    print(f"[FRONTEND DEBUG] serve_frontend called with path={repr(path)}", flush=True)
    if path.startswith('api/'):
        print(f"[FRONTEND DEBUG] path starts with api/, aborting 404", flush=True)
        abort(404)

    build_dir = _resolve_build_dir()
    if build_dir is None:
        abort(404)

    candidate = build_dir / path
    if path and candidate.exists() and candidate.is_file():
        return send_from_directory(build_dir, path)

    static_dir = build_dir / 'static'
    if path and static_dir.exists():
        static_candidate = static_dir / path
        if static_candidate.exists() and static_candidate.is_file():
            return send_from_directory(static_dir, path)

    return send_from_directory(build_dir, 'index.html')
