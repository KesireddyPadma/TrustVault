import os, uuid, hashlib, json
from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy import UniqueConstraint
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.config.update(SECRET_KEY=os.getenv('SECRET_KEY', 'local-dev-only-change-this-key'), SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///' + str(BASE / 'trustvault.db')).replace('postgres://','postgresql://',1), SQLALCHEMY_TRACK_MODIFICATIONS=False, MAX_CONTENT_LENGTH=10*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','0')=='1')
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', str(BASE/'private_uploads')))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Only the Flask server uses the Supabase secret key. Never expose it to browsers.
SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'trustvault-documents')
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)


def storage_request(method, storage_key, data=None, mime=None):
    """Private Supabase Storage API call, after application-level authorization."""
    if not SUPABASE_ENABLED:
        raise RuntimeError('Supabase Storage is not configured')
    if not SUPABASE_URL.startswith('https://'):
        raise RuntimeError('SUPABASE_URL must use HTTPS')
    bucket = quote(SUPABASE_BUCKET, safe='')
    key = quote(storage_key, safe='')
    url = f'{SUPABASE_URL}/storage/v1/object/{bucket}/{key}'
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    }
    if mime:
        headers['Content-Type'] = mime
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as response:
        return response.read()


def storage_upload(storage_key, data, mime):
    storage_request('POST', storage_key, data, mime)


def storage_download(storage_key):
    return storage_request('GET', storage_key)


def storage_delete(storage_key):
    storage_request('DELETE', storage_key)

db=SQLAlchemy(app)
login_manager=LoginManager(app)
login_manager.login_view='login'
csrf=CSRFProtect(app)
ph=PasswordHasher()

def now(): return datetime.now(timezone.utc)
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(255),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(500),nullable=False)
    role=db.Column(db.String(20),nullable=False,default='user')
    created_at=db.Column(db.DateTime(timezone=True),default=now)
class Document(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    owner_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    title=db.Column(db.String(200),nullable=False)
    filename=db.Column(db.String(255),nullable=False)
    storage_key=db.Column(db.String(80),unique=True,nullable=False)
    mime=db.Column(db.String(100),nullable=False)
    sha256=db.Column(db.String(64),nullable=False)
    size=db.Column(db.Integer,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    owner=db.relationship('User')
class Grant(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    document_id=db.Column(db.Integer,db.ForeignKey('document.id',ondelete='CASCADE'),nullable=False,index=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False,index=True)
    permission=db.Column(db.String(10),nullable=False)
    __table_args__=(UniqueConstraint('document_id','user_id'),)
    user=db.relationship('User')
class Audit(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    actor_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=True)
    document_id=db.Column(db.Integer,nullable=True)
    action=db.Column(db.String(60),nullable=False)
    detail=db.Column(db.String(500),default='')
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    actor=db.relationship('User')
@login_manager.user_loader
def load_user(uid):
    try: return db.session.get(User,int(uid))
    except (ValueError,TypeError): return None

def log(action, doc=None, detail=''):
    db.session.add(Audit(actor_id=current_user.id if current_user.is_authenticated else None,document_id=doc,action=action,detail=detail[:500]))
    db.session.commit()

def permission(doc):
    if not current_user.is_authenticated: return None
    if current_user.role=='admin': return 'admin'
    if doc.owner_id==current_user.id: return 'owner'
    grant=Grant.query.filter_by(document_id=doc.id,user_id=current_user.id).first()
    return grant.permission if grant else None

def require_doc(doc, action):
    p=permission(doc)
    allowed={'read':{'admin','owner','read','edit'},'edit':{'admin','owner','edit'},'manage':{'admin','owner'}}
    if p not in allowed[action]:
        log('denied',doc.id,action)
        abort(403)

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args,**kwargs):
        if current_user.role!='admin': abort(403)
        return fn(*args,**kwargs)
    return wrapped

def document_or_404(doc_id): return db.get_or_404(Document,doc_id)

def visible_documents():
    if current_user.role=='admin': return Document.query.order_by(Document.created_at.desc()).all()
    owned=Document.query.filter_by(owner_id=current_user.id).all()
    ids=[g.document_id for g in Grant.query.filter_by(user_id=current_user.id).all()]
    shared=Document.query.filter(Document.id.in_(ids)).all() if ids else []
    return sorted({d.id:d for d in owned+shared}.values(),key=lambda d:d.created_at,reverse=True)

@app.route('/')
def home():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else render_template('home.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
        if not name or len(name)>120 or '@' not in email or len(email)>255 or not 12<=len(pw)<=128:
            flash('Enter valid details. Password must be 12–128 characters.','error')
        elif User.query.filter_by(email=email).first(): flash('Email already registered. Sign in instead.','error')
        else:
            user=User(name=name,email=email,password_hash=ph.hash(pw),role='user')
            db.session.add(user); db.session.commit(); login_user(user); log('register'); return redirect(url_for('dashboard'))
    return render_template('auth.html',mode='register')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
        user=User.query.filter_by(email=email).first()
        valid=False
        if user:
            try: valid=ph.verify(user.password_hash,pw)
            except (VerifyMismatchError,VerificationError,ValueError): pass
        if valid:
            login_user(user); log('login'); return redirect(url_for('dashboard'))
        flash('Invalid email or password.','error')
    return render_template('auth.html',mode='login')
@app.post('/logout')
@login_required
def logout():
    log('logout'); logout_user(); return redirect(url_for('home'))
@app.get('/dashboard')
@login_required
def dashboard():
    docs=visible_documents(); own=sum(d.owner_id==current_user.id for d in docs)
    return render_template('dashboard.html',docs=docs,own=own,shared=len(docs)-own,grants=Grant,permission=permission)

ALLOWED={'.pdf':'application/pdf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.txt':'text/plain'}
def valid_content(ext, data):
    if ext=='.pdf': return data.startswith(b'%PDF-')
    if ext=='.png': return data.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in ('.jpg','.jpeg'): return data.startswith(b'\xff\xd8\xff')
    if ext=='.txt':
        try: data.decode('utf-8'); return True
        except UnicodeDecodeError: return False
    return False
@app.post('/upload')
@login_required
def upload():
    file=request.files.get('file'); title=request.form.get('title','').strip()
    if not file or not file.filename: flash('Choose a file.','error'); return redirect(url_for('dashboard'))
    filename=secure_filename(file.filename)
    ext=Path(filename).suffix.lower()
    if ext not in ALLOWED: flash('Only PDF, PNG, JPG, TXT files allowed.','error'); return redirect(url_for('dashboard'))
    data=file.read(10*1024*1024+1)
    if not data or len(data)>10*1024*1024 or not valid_content(ext,data):
        flash('Invalid file type or size (10 MB maximum).','error'); return redirect(url_for('dashboard'))
    # sb_ prefix distinguishes new Supabase objects from legacy local files.
    key=('sb_' if SUPABASE_ENABLED else '') + uuid.uuid4().hex
    try:
        if SUPABASE_ENABLED:
            storage_upload(key, data, ALLOWED[ext])
        else:
            (UPLOAD_DIR/key).write_bytes(data)
            
    except (HTTPError, URLError, OSError, RuntimeError) as exc:
        print("SUPABASE UPLOAD ERROR:", repr(exc), flush=True)
        app.logger.error('Storage upload failed: %s', type(exc).__name__)
        flash('Upload failed. Please try again later.','error')
        return redirect(url_for('dashboard'))
    doc=Document(owner_id=current_user.id,title=(title[:200] or filename),filename=filename,storage_key=key,mime=ALLOWED[ext],sha256=hashlib.sha256(data).hexdigest(),size=len(data))
    try:
        db.session.add(doc); db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            if key.startswith('sb_'): storage_delete(key)
            else: (UPLOAD_DIR/key).unlink(missing_ok=True)
        except Exception: app.logger.warning('Could not clean up orphaned upload')
        raise
    log('upload',doc.id,filename)
    flash('Document uploaded securely.','success'); return redirect(url_for('dashboard'))
@app.get('/documents/<int:doc_id>/download')
@login_required
def download(doc_id):
    doc=document_or_404(doc_id); require_doc(doc,'read')
    if doc.storage_key.startswith('sb_'):
        try:
            data=storage_download(doc.storage_key)
        except HTTPError as exc:
            if exc.code==404: abort(404)
            app.logger.error('Storage download failed: HTTP %s', exc.code)
            abort(502)
        except (URLError, OSError, RuntimeError):
            app.logger.error('Storage download failed')
            abort(502)
        if hashlib.sha256(data).hexdigest()!=doc.sha256:
            app.logger.error('Document checksum mismatch: id=%s', doc.id)
            abort(502)
        log('download',doc.id)
        return send_file(BytesIO(data),as_attachment=True,download_name=doc.filename,mimetype=doc.mime)
    path=UPLOAD_DIR/doc.storage_key
    if not path.is_file(): abort(404)
    log('download',doc.id)
    return send_file(path,as_attachment=True,download_name=doc.filename,mimetype=doc.mime)
@app.post('/documents/<int:doc_id>/edit')
@login_required
def edit_document(doc_id):
    doc=document_or_404(doc_id); require_doc(doc,'edit')
    title=request.form.get('title','').strip()
    if not title or len(title)>200: flash('Invalid title.','error')
    else:
        doc.title=title; db.session.commit(); log('rename',doc.id); flash('Document renamed.','success')
    return redirect(url_for('dashboard'))
@app.post('/documents/<int:doc_id>/delete')
@login_required
def delete_document(doc_id):
    doc=document_or_404(doc_id); require_doc(doc,'manage')
    # Remove remote file first; if it fails, preserve the document DB record.
    if doc.storage_key.startswith('sb_'):
        try:
            storage_delete(doc.storage_key)
        except HTTPError as exc:
            if exc.code!=404:
                app.logger.error('Storage delete failed: HTTP %s', exc.code)
                abort(502)
        except (URLError, OSError, RuntimeError):
            app.logger.error('Storage delete failed')
            abort(502)
    Grant.query.filter_by(document_id=doc.id).delete()
    db.session.delete(doc); db.session.commit(); log('delete',doc_id)
    if not doc.storage_key.startswith('sb_'):
        (UPLOAD_DIR/doc.storage_key).unlink(missing_ok=True)
    flash('Document deleted.','success'); return redirect(url_for('dashboard'))
@app.post('/documents/<int:doc_id>/share')
@login_required
def share_document(doc_id):
    doc=document_or_404(doc_id); require_doc(doc,'manage')
    email=request.form.get('email','').strip().lower(); level=request.form.get('permission','')
    user=User.query.filter_by(email=email).first()
    if not user or user.id==doc.owner_id or level not in ('read','edit'):
        flash('Choose a registered user and Read or Edit permission.','error')
    else:
        grant=Grant.query.filter_by(document_id=doc.id,user_id=user.id).first()
        if grant: grant.permission=level
        else: db.session.add(Grant(document_id=doc.id,user_id=user.id,permission=level))
        db.session.commit(); log('share',doc.id,f'{email}: {level}'); flash('Permission saved.','success')
    return redirect(url_for('dashboard'))
@app.post('/documents/<int:doc_id>/revoke/<int:user_id>')
@login_required
def revoke(doc_id,user_id):
    doc=document_or_404(doc_id); require_doc(doc,'manage')
    grant=Grant.query.filter_by(document_id=doc.id,user_id=user_id).first_or_404()
    db.session.delete(grant); db.session.commit(); log('revoke',doc.id,str(user_id)); flash('Access revoked.','success')
    return redirect(url_for('dashboard'))
@app.get('/activity')
@login_required
def activity():
    docs=visible_documents(); ids=[d.id for d in docs]
    logs=Audit.query.filter((Audit.actor_id==current_user.id) | (Audit.document_id.in_(ids))).order_by(Audit.created_at.desc()).limit(100).all()
    return render_template('activity.html',logs=logs)
@app.get('/admin')
@admin_required
def admin():
    return render_template('admin.html',users=User.query.order_by(User.id).all(),docs=Document.query.order_by(Document.id.desc()).all(),logs=Audit.query.order_by(Audit.id.desc()).limit(200).all())
@app.get('/health')
def health(): return jsonify(status='ok')
@app.errorhandler(403)
def forbidden(err): return render_template('error.html',code=403,message='You do not have access to this resource.'),403
@app.errorhandler(404)
def missing(err): return render_template('error.html',code=404,message='Resource not found.'),404
@app.errorhandler(413)
def too_big(err): return render_template('error.html',code=413,message='Maximum upload size is 10 MB.'),413
@app.cli.command('init-db')
def init_db():
    db.create_all(); print('Database initialized.')
@app.cli.command('create-admin')
def create_admin():
    from getpass import getpass
    email=input('Admin email: ').strip().lower(); name=input('Admin name: ').strip(); pw=getpass('Password (12+ chars): ')
    if not name or '@' not in email or len(pw)<12: raise ValueError('Invalid admin details')
    user=User.query.filter_by(email=email).first()
    if user: user.role='admin'; user.password_hash=ph.hash(pw)
    else: db.session.add(User(email=email,name=name,password_hash=ph.hash(pw),role='admin'))
    db.session.commit(); print('Admin account ready.')
with app.app_context(): db.create_all()
if __name__=='__main__': app.run(debug=True)
