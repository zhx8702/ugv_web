# -*- coding: utf-8 -*-
"""Simple session login for the web control UI."""
import hmac
from flask import Blueprint, current_app, jsonify, request, session

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _auth_enabled():
    return bool(current_app.config.get('AUTH_ENABLED'))


@auth_bp.route('/status', methods=['GET'])
def auth_status():
    enabled = _auth_enabled()
    return jsonify({
        'enabled': enabled,
        'authenticated': (not enabled) or bool(session.get('user')),
        'user': session.get('user')
    })


@auth_bp.route('/login', methods=['POST'])
def login():
    if not _auth_enabled():
        session['user'] = current_app.config.get('AUTH_USER', 'ws')
        return jsonify({'success': True, 'user': session['user'], 'enabled': False})

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    expected_user = current_app.config.get('AUTH_USER', 'ws')
    expected_pass = current_app.config.get('AUTH_PASSWORD', '')

    user_ok = hmac.compare_digest(username, expected_user)
    pass_ok = hmac.compare_digest(password, expected_pass)
    if not (user_ok and pass_ok):
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    session.clear()
    session['user'] = username
    session.permanent = True
    return jsonify({'success': True, 'user': username})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


def init_auth(app):
    """Protect /api/* when AUTH_ENABLED is set."""

    @app.before_request
    def require_login():
        if not app.config.get('AUTH_ENABLED'):
            return None
        if request.method == 'OPTIONS':
            return None

        path = request.path or ''
        if path.startswith('/api/auth/'):
            return None
        if path in ('/api/system/health',):
            return None
        if not path.startswith('/api/'):
            return None

        if session.get('user'):
            return None
        return jsonify({'error': 'unauthorized'}), 401
