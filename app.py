from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import uuid
import base64

app = Flask(__name__)
app.secret_key = 'thangmay-secret-key-change-me-2024'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ==================== MODELS ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(20), default='editor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(50), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(300), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    images = db.relationship('ProductImage', backref='product',
                             cascade='all, delete-orphan', lazy=True,
                             order_by='ProductImage.sort_order')

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    client = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    year = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    short_description = db.Column(db.String(300), nullable=True)
    content = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(300), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('ProjectImage', backref='project',
                             cascade='all, delete-orphan', lazy=True,
                             order_by='ProjectImage.sort_order')

class ProjectImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    sort_order = db.Column(db.Integer, default=0)

class SliderImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    subtitle = db.Column(db.String(300), nullable=True)
    link = db.Column(db.String(300), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== HELPERS ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Vui lòng đăng nhập để truy cập!', 'error')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Vui lòng đăng nhập!', 'error')
            return redirect(url_for('login'))
        if session.get('admin_role') != 'superadmin':
            flash('Chỉ Super Admin mới có quyền truy cập!', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action, target_type=None, target_id=None, description=None):
    try:
        log = ActivityLog(
            user_id=session.get('admin_id'), username=session.get('admin_username', 'anonymous'),
            action=action, target_type=target_type, target_id=target_id,
            description=description, ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f'⚠️ Log error: {e}')
        db.session.rollback()

def get_content(key, default=''):
    c = SiteContent.query.filter_by(key=key).first()
    return c.value if c and c.value else default

def get_all_settings():
    defaults = {
        'company_name': 'ThangMayPro', 'company_tagline': 'Elevator Technology',
        'logo': '', 'favicon': '', 'logo_text': 'ELIFT', 'about_image': '', # ⭐ THÊM about_image
        'hotline': '0900 123 456', 'email': 'info@thangmaypro.vn',
        'address': '123 Nguyễn Văn Linh, Q.7, TP.HCM', 'working_hours': 'T2 - T7: 8:00 - 18:00',
        'facebook_url': '', 'zalo_url': '', 'messenger_url': '', 'youtube_url': '', 'google_map': '',
        'hero_title': 'Thang máy chất lượng cao cho mọi công trình',
        'hero_subtitle': 'Hơn 15 năm kinh nghiệm cung cấp, lắp đặt và bảo trì thang máy tại Việt Nam',
        'about_text': 'ThangMayPro là công ty hàng đầu trong lĩnh vực cung cấp giải pháp thang máy tại Việt Nam.',
        'stat1_num': '500+', 'stat1_label': 'Dự án hoàn thành',
        'stat2_num': '15+', 'stat2_label': 'Năm kinh nghiệm',
        'stat3_num': '2000+', 'stat3_label': 'Khách hàng tin dùng',
        'stat4_num': '24/7', 'stat4_label': 'Hỗ trợ kỹ thuật',
        'primary_color': '#dc2626', 'primary_dark_color': '#b91c1c',
        'topbar_bg_color': '#ffffff', 'topbar_text_color': '#0f172a', 'topbar_accent_color': '#dc2626',
        'nav_bg_color': '#dc2626', 'nav_text_color': '#ffffff', 'nav_hover_bg_color': 'rgba(0,0,0,0.15)',
        'footer_bg_color': '#0f172a', 'footer_text_color': '#cbd5e1',
        'body_bg_color': '#ffffff', 'text_color': '#0f172a',
        'cta_text': 'Nhận báo giá',
    }
    settings = {}
    for key, default in defaults.items():
        settings[key] = get_content(key, default)
    return settings

@app.context_processor
def inject_settings():
    return {'settings': get_all_settings()}

# ==================== AUTH ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.is_active and user.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = user.username
            session['admin_role'] = user.role
            session['admin_id'] = user.id
            user.last_login = datetime.utcnow()
            user.last_ip = request.remote_addr
            db.session.commit()
            log_activity('login', 'user', user.id, f'Đăng nhập từ {request.remote_addr}')
            flash('Đăng nhập thành công!', 'success')
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Sai thông tin đăng nhập hoặc tài khoản bị khóa!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('admin_logged_in'):
        log_activity('logout', 'user', session.get('admin_id'), 'Đăng xuất')
    session.clear()
    flash('Đã đăng xuất!', 'success')
    return redirect(url_for('index'))

# ==================== PUBLIC ====================
@app.route('/')
def index():
    products = Product.query.limit(6).all()
    projects = Project.query.filter_by(is_featured=True).order_by(Project.sort_order.asc()).limit(6).all()
    if not projects: projects = Project.query.order_by(Project.id.desc()).limit(6).all()
    sliders = SliderImage.query.filter_by(is_active=True).order_by(SliderImage.sort_order.asc()).all()
    return render_template('index.html', products=products, projects=projects, sliders=sliders)

@app.route('/products')
def products():
    return render_template('products.html', products=Product.query.all())

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related = Product.query.filter(Product.category == product.category, Product.id != id).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)

@app.route('/projects')
def projects_list():
    return render_template('projects.html', projects=Project.query.order_by(Project.sort_order.asc(), Project.id.desc()).all())

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    related = Project.query.filter(Project.id != id).order_by(Project.id.desc()).limit(3).all()
    return render_template('project_detail.html', project=project, related=related)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        db.session.add(Contact(name=request.form['name'], email=request.form['email'], phone=request.form.get('phone', ''), message=request.form['message']))
        db.session.commit()
        flash('Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ==================== ADMIN ====================
@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html',
                           total_products=Product.query.count(), total_projects=Project.query.count(),
                           total_sliders=SliderImage.query.count(), total_contacts=Contact.query.count(),
                           total_users=User.query.count(), recent_contacts=Contact.query.order_by(Contact.id.desc()).limit(5).all())

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        try:
            keys = [
                'company_name', 'company_tagline', 'logo_text', 'hotline', 'email', 'address', 'working_hours',
                'facebook_url', 'zalo_url', 'messenger_url', 'youtube_url', 'google_map',
                'hero_title', 'hero_subtitle', 'about_text',
                'stat1_num', 'stat1_label', 'stat2_num', 'stat2_label', 'stat3_num', 'stat3_label', 'stat4_num', 'stat4_label',
                'primary_color', 'primary_dark_color', 'topbar_bg_color', 'topbar_text_color', 'topbar_accent_color',
                'nav_bg_color', 'nav_text_color', 'nav_hover_bg_color', 'footer_bg_color', 'footer_text_color',
                'body_bg_color', 'text_color', 'cta_text',
            ]
            for key in keys:
                value = request.form.get(key, '').strip()
                c = SiteContent.query.filter_by(key=key).first()
                if c: c.value = value
                else: db.session.add(SiteContent(key=key, value=value))

            # Xử lý upload file (logo, favicon, about_image)
            for file_key in ['logo_file', 'favicon_file', 'about_image_file']:
                file = request.files.get(file_key)
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    db_key = file_key.replace('_file', '') # Chuyển logo_file -> logo
                    fname = f"{db_key}_{uuid.uuid4().hex}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    c = SiteContent.query.filter_by(key=db_key).first()
                    if c: c.value = fname
                    else: db.session.add(SiteContent(key=db_key, value=fname))

            db.session.commit()
            log_activity('update', 'settings', None, 'Cập nhật cấu hình website')
            flash('✅ Đã lưu cấu hình thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Lỗi: {e}', 'error')
        return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html')

@app.route('/admin/settings/reset_colors', methods=['POST'])
@login_required
def admin_settings_reset_colors():
    defaults = {
        'primary_color': '#dc2626', 'primary_dark_color': '#b91c1c', 'topbar_bg_color': '#ffffff',
        'topbar_text_color': '#0f172a', 'topbar_accent_color': '#dc2626', 'nav_bg_color': '#dc2626',
        'nav_text_color': '#ffffff', 'nav_hover_bg_color': 'rgba(0,0,0,0.15)', 'footer_bg_color': '#0f172a',
        'footer_text_color': '#cbd5e1', 'body_bg_color': '#ffffff', 'text_color': '#0f172a',
    }
    for key, value in defaults.items():
        c = SiteContent.query.filter_by(key=key).first()
        if c: c.value = value
        else: db.session.add(SiteContent(key=key, value=value))
    db.session.commit()
    flash('✅ Đã khôi phục màu sắc mặc định!', 'success')
    return redirect(url_for('admin_settings'))

@app.route('/admin/sliders')
@login_required
def admin_sliders():
    return render_template('admin_slider.html', sliders=SliderImage.query.order_by(SliderImage.sort_order.asc()).all())

@app.route('/admin/sliders/add', methods=['POST'])
@login_required
def admin_slider_add():
    files = request.files.getlist('files')
    if not files: return redirect(url_for('admin_sliders'))
    max_order = db.session.query(db.func.max(SliderImage.sort_order)).scalar() or 0
    for idx, file in enumerate(files):
        if file and file.filename and allowed_file(file.filename):
            fname = f"slide_{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            db.session.add(SliderImage(filename=fname, sort_order=max_order + idx + 1))
    db.session.commit()
    flash('✅ Đã thêm ảnh slider!', 'success')
    return redirect(url_for('admin_sliders'))

@app.route('/admin/sliders/<int:id>/edit', methods=['POST'])
@login_required
def admin_slider_edit(id):
    slider = SliderImage.query.get_or_404(id)
    slider.title = request.form.get('title', '')
    slider.subtitle = request.form.get('subtitle', '')
    slider.link = request.form.get('link', '')
    slider.is_active = request.form.get('is_active') == 'on'
    db.session.commit()
    flash('✅ Đã cập nhật slider!', 'success')
    return redirect(url_for('admin_sliders'))

@app.route('/admin/sliders/<int:id>/delete', methods=['POST'])
@login_required
def admin_slider_delete(id):
    slider = SliderImage.query.get_or_404(id)
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], slider.filename)
        if os.path.exists(filepath): os.remove(filepath)
    except: pass
    db.session.delete(slider)
    db.session.commit()
    return redirect(url_for('admin_sliders'))

@app.route('/admin/projects')
@login_required
def admin_projects():
    return render_template('admin_projects.html', projects=Project.query.order_by(Project.sort_order.asc(), Project.id.desc()).all())

@app.route('/admin/projects/add', methods=['GET', 'POST'])
@login_required
def admin_project_add():
    if request.method == 'POST':
        project = Project(
            title=request.form['title'], client=request.form.get('client', ''), location=request.form.get('location', ''),
            year=request.form.get('year', ''), category=request.form.get('category', ''), short_description=request.form.get('short_description', ''),
            content=request.form.get('content', ''), is_featured=request.form.get('is_featured') == 'on',
            sort_order=int(request.form.get('sort_order', 0)), cover_image=request.form.get('cover_image_filename') or None,
        )
        db.session.add(project)
        db.session.flush()
        for idx, fname in enumerate(request.form.getlist('gallery_images[]')):
            if fname.strip(): db.session.add(ProjectImage(project_id=project.id, filename=fname.strip(), sort_order=idx))
        db.session.commit()
        flash('✅ Thêm dự án thành công!', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('add_project.html')

@app.route('/admin/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.title = request.form['title']
        project.client = request.form.get('client', '')
        project.location = request.form.get('location', '')
        project.year = request.form.get('year', '')
        project.category = request.form.get('category', '')
        project.short_description = request.form.get('short_description', '')
        project.content = request.form.get('content', '')
        project.is_featured = request.form.get('is_featured') == 'on'
        project.sort_order = int(request.form.get('sort_order', 0))
        cover = request.form.get('cover_image_filename')
        if cover: project.cover_image = cover

        kept_ids = [int(x) for x in request.form.getlist('kept_image_ids[]') if x.isdigit()]
        for img in list(project.images):
            if img.id not in kept_ids:
                try:
                    fp = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
                    if os.path.exists(fp): os.remove(fp)
                except: pass
                db.session.delete(img)
        max_order = db.session.query(db.func.max(ProjectImage.sort_order)).filter_by(project_id=id).scalar() or 0
        for idx, fname in enumerate(request.form.getlist('new_gallery_images[]')):
            if fname.strip(): db.session.add(ProjectImage(project_id=id, filename=fname.strip(), sort_order=max_order + idx + 1))
        db.session.commit()
        flash('✅ Đã cập nhật dự án!', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('edit_project.html', project=project)

@app.route('/admin/projects/<int:id>/delete', methods=['POST'])
@login_required
def admin_project_delete(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('admin_projects'))

@app.route('/admin/contacts')
@login_required
def admin_contacts():
    return render_template('admin_contacts.html', contacts=Contact.query.order_by(Contact.id.desc()).all())

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'], description=request.form.get('description', ''),
            price=float(request.form['price']), category=request.form.get('category', ''),
            image=request.form.get('image_filename') or None
        )
        db.session.add(product)
        db.session.flush()
        for idx, fname in enumerate(request.form.getlist('gallery_images[]')):
            if fname.strip(): db.session.add(ProductImage(product_id=product.id, filename=fname.strip(), sort_order=idx))
        db.session.commit()
        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form.get('description', '')
        product.price = float(request.form['price'])
        product.category = request.form.get('category', '')
        img = request.form.get('image_filename')
        if img: product.image = img

        kept_ids = [int(x) for x in request.form.getlist('kept_image_ids[]') if x.isdigit()]
        for image in list(product.images):
            if image.id not in kept_ids:
                try:
                    fp = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                    if os.path.exists(fp): os.remove(fp)
                except: pass
                db.session.delete(image)
        max_order = db.session.query(db.func.max(ProductImage.sort_order)).filter_by(product_id=id).scalar() or 0
        for idx, fname in enumerate(request.form.getlist('new_gallery_images[]')):
            if fname.strip(): db.session.add(ProductImage(product_id=id, filename=fname.strip(), sort_order=max_order + idx + 1))
        db.session.commit()
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('products'))

@app.route('/admin/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user = User.query.get(session['admin_id'])
        if not user.check_password(request.form['current_password']):
            flash('Mật khẩu hiện tại không đúng!', 'error')
        elif len(request.form['new_password']) < 6:
            flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'error')
        elif request.form['new_password'] != request.form['confirm_password']:
            flash('Xác nhận mật khẩu không khớp!', 'error')
        else:
            user.set_password(request.form['new_password'])
            db.session.commit()
            flash('✅ Đổi mật khẩu thành công!', 'success')
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('change_password'))
    return render_template('change_password.html')

@app.route('/admin/users')
@superadmin_required
def user_list():
    return render_template('user_list.html', users=User.query.order_by(User.id.asc()).all())

@app.route('/admin/users/add', methods=['GET', 'POST'])
@superadmin_required
def user_add():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if User.query.filter_by(username=username).first(): flash('Tên đăng nhập đã tồn tại!', 'error')
        elif len(request.form['password']) < 6: flash('Mật khẩu phải >= 6 ký tự!', 'error')
        elif request.form['password'] != request.form['confirm_password']: flash('Xác nhận MK không khớp!', 'error')
        else:
            new_user = User(username=username, full_name=request.form.get('full_name', ''),
                            email=request.form.get('email', ''), role=request.form.get('role', 'editor'), is_active=True)
            new_user.set_password(request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            flash(f'✅ Đã tạo tài khoản "{username}"!', 'success')
            return redirect(url_for('user_list'))
        return redirect(url_for('user_add'))
    return render_template('user_add.html')

@app.route('/admin/users/<int:id>/toggle', methods=['POST'])
@superadmin_required
def user_toggle(id):
    user = User.query.get_or_404(id)
    if user.id != session['admin_id']:
        user.is_active = not user.is_active
        db.session.commit()
    return redirect(url_for('user_list'))

@app.route('/admin/users/<int:id>/reset_password', methods=['POST'])
@superadmin_required
def user_reset_password(id):
    user = User.query.get_or_404(id)
    if len(request.form.get('new_password', '')) >= 6:
        user.set_password(request.form['new_password'])
        db.session.commit()
    return redirect(url_for('user_list'))

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@superadmin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    if user.id != session['admin_id'] and not (user.role == 'superadmin' and User.query.filter_by(role='superadmin').count() <= 1):
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('user_list'))

@app.route('/admin/activity')
@login_required
def activity_log():
    if session.get('admin_role') != 'superadmin':
        logs = ActivityLog.query.filter_by(user_id=session['admin_id']).order_by(ActivityLog.created_at.desc()).limit(200).all()
    else:
        logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(500).all()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return render_template('activity_log.html', logs=logs, total_logs=ActivityLog.query.count(),
                           today_logs=ActivityLog.query.filter(ActivityLog.created_at >= today_start).count(),
                           active_users=db.session.query(ActivityLog.username, db.func.count(ActivityLog.id)).group_by(ActivityLog.username).all())

# ==================== API ====================
@app.route('/api/upload_image', methods=['POST'])
@login_required
def api_upload_image():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename): return jsonify({'success': False}), 400
    fname = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    return jsonify({'success': True, 'filename': fname, 'url': url_for('static', filename=f'uploads/{fname}')})

@app.route('/api/upload_cropped', methods=['POST'])
@login_required
def api_upload_cropped():
    try:
        img_bytes = base64.b64decode(request.get_json()['image'].split(',')[1])
        fname = f"crop_{uuid.uuid4().hex}.png"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], fname), 'wb') as f: f.write(img_bytes)
        return jsonify({'success': True, 'filename': fname, 'url': url_for('static', filename=f'uploads/{fname}')})
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload_multiple', methods=['POST'])
@login_required
def api_upload_multiple():
    results = []
    for file in request.files.getlist('files'):
        if file and allowed_file(file.filename):
            fname = f"gal_{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            results.append({'success': True, 'filename': fname, 'url': url_for('static', filename=f'uploads/{fname}')})
    return jsonify({'success': True, 'files': results})

@app.route('/api/product/<int:id>', methods=['PUT'])
@login_required
def api_update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data: product.name = data['name']
    if 'description' in data: product.description = data['description']
    if 'price' in data:
        try: product.price = float(data['price'])
        except: pass
    if 'category' in data: product.category = data['category']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/content', methods=['POST'])
@login_required
def api_update_content():
    try:
        for key, value in request.get_json().items():
            key, value = str(key).strip(), str(value).strip()
            if not key: continue
            c = SiteContent.query.filter_by(key=key).first()
            if c: c.value = value
            else: db.session.add(SiteContent(key=key, value=value))
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contact/<int:id>', methods=['DELETE'])
@login_required
def api_delete_contact(id):
    db.session.delete(Contact.query.get_or_404(id))
    db.session.commit()
    return jsonify({'success': True})

# ==================== INIT ====================
def init_admin():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', full_name='Quản trị viên', role='superadmin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Tài khoản superadmin: admin / admin123')

def init_default_content():
    defaults = {
        'company_name': 'ThangMayPro', 'company_tagline': 'Elevator Technology',
        'hotline': '0904 303 668', 'email': 'van.elift@gmail.com',
        'address': '123 Nguyễn Văn Linh, Q.7, TP.HCM', 'working_hours': 'T2 - T7: 8:00 - 18:00',
        'primary_color': '#dc2626', 'cta_text': 'Nhận báo giá',
        'messenger_url': 'https://m.me/yourpage', 'zalo_url': 'https://zalo.me/0904303668',
    }
    for key, value in defaults.items():
        if not SiteContent.query.filter_by(key=key).first():
            db.session.add(SiteContent(key=key, value=value))
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_admin()
        init_default_content()
    app.run(debug=True, host='0.0.0.0', port=5000)
