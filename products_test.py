from flask import Blueprint
bp = Blueprint("test", __name__, url_prefix="/api/v1")
@bp.route("/test", methods=["GET"])
def test():
    return {"status": "ok"}