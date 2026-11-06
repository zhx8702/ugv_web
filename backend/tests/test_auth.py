# -*- coding: utf-8 -*-
from flask import Flask

from app.auth import auth_bp, init_auth


def _make_app():
    app = Flask(__name__)
    app.secret_key = 'test-secret'
    app.config['TESTING'] = True
    app.config['AUTH_ENABLED'] = True
    app.config['AUTH_USER'] = 'ws'
    app.config['AUTH_PASSWORD'] = 'secret'
    app.register_blueprint(auth_bp)
    init_auth(app)

    @app.get('/api/audio/status')
    def audio_status():
        return {'ok': True}

    return app


def test_login_and_protected_api():
    client = _make_app().test_client()

    denied = client.get('/api/audio/status')
    assert denied.status_code == 401

    bad = client.post('/api/auth/login', json={'username': 'ws', 'password': 'nope'})
    assert bad.status_code == 401

    ok = client.post('/api/auth/login', json={'username': 'ws', 'password': 'secret'})
    assert ok.status_code == 200
    assert ok.get_json()['success'] is True

    status = client.get('/api/audio/status')
    assert status.status_code == 200
