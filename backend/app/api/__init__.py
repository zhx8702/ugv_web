"""
API Blueprints
"""
from flask import Blueprint

# Create blueprints
system_bp = Blueprint('system', __name__)
control_bp = Blueprint('control', __name__)
media_bp = Blueprint('media', __name__)
cv_bp = Blueprint('cv', __name__)
audio_bp = Blueprint('audio', __name__)

# Import routes (must be after blueprint creation to avoid circular imports)
from app.api import system, control, media, cv, audio  # noqa
