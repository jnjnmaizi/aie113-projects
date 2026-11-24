def test_frontend_and_assets_are_served(client):
    page = client.get('/')
    assert page.status_code == 200
    assert 'text/html' in page.headers['content-type']
    assert 'lang="ar" dir="rtl"' in page.text
    assert client.get('/static/app.js').status_code == 200
    assert client.get('/static/style.css').status_code == 200
    assert client.get('/static/../settings.py').status_code == 404


def test_frontend_preserves_api_routes(client, photo):
    assert client.get('/').status_code == 200
    response = client.post('/v1/predict', files={'file': ('leaf.png', photo, 'image/png')})
    assert response.status_code == 200
    assert response.json()['label'] == 'bean_rust'
    assert client.get('/docs').status_code == 200
