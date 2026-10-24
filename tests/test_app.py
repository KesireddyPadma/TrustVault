import io
import pytest
from app import app, db, User, Document, Grant, ph

@pytest.fixture
def client(tmp_path):
    app.config.update(TESTING=True,SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'test.db'),WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.session.remove(); db.engine.dispose(); db.create_all()
        for name,email in [('Owner','owner@example.com'),('Viewer','viewer@example.com'),('Stranger','stranger@example.com')]:
            db.session.add(User(name=name,email=email,password_hash=ph.hash('SecurePass123!'),role='user'))
        db.session.commit()
    import app as module
    old=module.UPLOAD_DIR; module.UPLOAD_DIR=tmp_path/'uploads'; module.UPLOAD_DIR.mkdir()
    with app.test_client() as c: yield c
    module.UPLOAD_DIR=old
    with app.app_context(): db.session.remove(); db.drop_all()

def login(c,email): return c.post('/login',data={'email':email,'password':'SecurePass123!'},follow_redirects=True)
def logout(c): return c.post('/logout')
def test_auth(client):
    assert login(client,'owner@example.com').status_code==200
    assert b'Your secure workspace' in client.get('/dashboard').data
    assert logout(client).status_code==302
    assert client.get('/dashboard').status_code==302

def test_owner_share_and_revoke(client):
    login(client,'owner@example.com')
    r=client.post('/upload',data={'title':'Secret','file':(io.BytesIO(b'private test text'),'secret.txt')},content_type='multipart/form-data')
    assert r.status_code==302
    with app.app_context(): doc_id=Document.query.filter_by(title='Secret').first().id
    logout(client); login(client,'stranger@example.com')
    assert client.get(f'/documents/{doc_id}/download').status_code==403
    assert client.post(f'/documents/{doc_id}/delete').status_code==403
    logout(client); login(client,'owner@example.com')
    assert client.post(f'/documents/{doc_id}/share',data={'email':'viewer@example.com','permission':'read'}).status_code==302
    logout(client); login(client,'viewer@example.com')
    assert client.get(f'/documents/{doc_id}/download').status_code==200
    assert client.post(f'/documents/{doc_id}/edit',data={'title':'No'}).status_code==403
    logout(client); login(client,'owner@example.com')
    with app.app_context(): uid=User.query.filter_by(email='viewer@example.com').first().id
    assert client.post(f'/documents/{doc_id}/revoke/{uid}').status_code==302
    logout(client); login(client,'viewer@example.com')
    assert client.get(f'/documents/{doc_id}/download').status_code==403

def test_admin_is_protected(client):
    assert client.get('/admin').status_code==302
    login(client,'owner@example.com')
    assert client.get('/admin').status_code==403

def test_invalid_file_rejected(client):
    login(client,'owner@example.com')
    client.post('/upload',data={'file':(io.BytesIO(b'not a real pdf'),'fake.pdf')},content_type='multipart/form-data')
    with app.app_context(): assert Document.query.count()==0
