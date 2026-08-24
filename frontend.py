"""Frontend blueprint for serving React app."""
from flask import Blueprint, send_from_directory
from pathlib import Path

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend."""
    static_folder = Path(__file__).parent.parent / 'frontend' / 'build' / 'static'
    index_dir = Path(static_folder).parent
    
    if path and (static_folder / path).exists():
        return send_from_directory(static_folder, path)
    
    return send_from_directory(index_dir, 'index.html')