from web_app import create_app


def test_login_page_loads_without_auth():
    app = create_app()
    client = app.test_client()

    response = client.get('/login')
    assert response.status_code == 200
    assert b'Admin Login' in response.data or b'Login' in response.data


def test_dashboard_requires_login():
    app = create_app()
    client = app.test_client()

    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/login'


def test_web_app_api_stats_requires_auth():
    app = create_app()
    client = app.test_client()

    response = client.get('/api/stats')
    assert response.status_code == 401
    assert response.get_json()['success'] is False


def test_successful_login_sets_session_and_allows_dashboard():
    app = create_app()
    client = app.test_client()

    response = client.post('/login', json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200

    dashboard = client.get('/dashboard')
    assert dashboard.status_code == 200
    assert b'IdeaForge' in dashboard.data or b'Operations Dashboard' in dashboard.data
