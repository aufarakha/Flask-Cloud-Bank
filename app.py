from flask import Flask, render_template, request, redirect, flash, abort, url_for, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, User, Transaction, Config, RoleEnum, AdminPermissions
from dotenv import load_dotenv
import requests
import os
from werkzeug.utils import secure_filename
import secrets

load_dotenv()
app = Flask(__name__, static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SECRET_KEY'] = 'your-secret-key'

# Exchange rate API
API_KEY = os.environ.get('EXCHANGE_API_KEY', '4d60b8cba96b5fbd5c207748')
BASE_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}'
# Exchange rate API

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login_register"

@login_manager.user_loader
def load_user(uid):
    # Try loading by ID first
    try:
        user = User.query.get(int(uid))
        if user:
            return user
    except ValueError:
        pass
    
    # If not found or not an integer, try by account number
    return User.query.filter_by(acc_num=uid).first()

def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

@app.route("/login_register", methods=["GET", "POST"])
def login_register():
    if request.method == "POST":
        password = request.form['password']
        action = request.form.get('action')

        if action == "login":
            email = request.form['email']
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                if user.is_banned:
                    flash("Your account is banned.", "error")
                    return redirect(url_for('login_register'))
                
                login_user(user, force=True)
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "error")
                return redirect(url_for('login_register'))
        
        elif action == "register":
            email = request.form['email']
            username = request.form['username']
            
            if User.query.filter_by(email=email).first():
                flash("Email already registered. Please use a different email.", "error")
                return redirect(url_for('login_register'))
                
            if User.query.filter_by(username=username).first():
                flash("Username already taken. Please choose a different one.", "error")
                return redirect(url_for('login_register'))
                
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role=RoleEnum.user,
                created_at=datetime.now(),
                ip_address=get_ip()
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login_register'))

    return render_template("login_register.html")

@app.route("/logout")
@login_required
def logout():
    # Clear any existing flash messages
    session.pop('_flashes', None)
    logout_user()
    return redirect(url_for('login_register'))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        if 'topup' in request.form:
            amt = float(request.form['amount'])
            current_user.balance += amt
        elif 'transfer' in request.form:
            to_un = request.form['to']
            amt = float(request.form['amount'])
            to_u = User.query.filter_by(username=to_un).first()
            if to_u and current_user.balance >= amt:
                current_user.balance -= amt
                to_u.balance += amt
                tx = Transaction(
                    sender_id=current_user.id,
                    receiver_id=to_u.id,
                    amount=amt,
                    timestamp=datetime.now()
                )
                db.session.add(tx)
                db.session.commit()
                flash("Transfer successful", "success")
            else:
                flash("Transfer failed. Please check the username and your balance.", "error")
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template(
        "dashboard.html",
        isDebug = True,
        user=current_user,
        active_page="dashboard"
    )


@app.route("/account")
@login_required
def account():
    isDebug = True
    return render_template(
        "account.html",
        isDebug = True,
        user=current_user,
        active_page="account"
    )

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    rates = {}
    base = 'USD'
    target = 'IDR'
    amount = None
    result = None

    # Fetch latest rates
    try:
        resp = requests.get(f"{BASE_URL}/latest/USD")
        data = resp.json()
        if data.get('result') == 'success':
            rates = {
                'USD': 1,  # Base currency is always 1
                'SGD': data['conversion_rates']['SGD'],
                'AUD': data['conversion_rates']['AUD'],
                'EUR': data['conversion_rates']['EUR'],
                'GBP': data['conversion_rates']['GBP'],
                'IDR': data['conversion_rates']['IDR']
            }
        else:
            flash('Error fetching exchange rates')
    except Exception as e:
        flash(f'Network error: {str(e)}')

    # Handle conversion form
    if request.method == 'POST' and request.form.get('action') == 'convert':
        try:
            base = request.form['from_currency']
            target = request.form['to_currency']
            amount = float(request.form['amount'])
            
            # If base is not USD, convert through USD rate
            if base != 'USD':
                # First convert to USD
                usd_amount = amount / rates[base]
                # Then convert USD to target
                result = usd_amount * rates[target]
            else:
                # Direct conversion from USD
                result = amount * rates[target]
                
        except ValueError:
            flash('Please enter a valid amount')
        except Exception as e:
            flash(f'Conversion error: {str(e)}')

    return render_template(
        "home.html",
        isDebug = False,
        user=current_user,
        rates=rates,
        base=base,
        target=target,
        amount=amount,
        result=result,
        datetime=datetime,
        active_page="home"
    )

@app.route("/transfer", methods=["GET","POST"])
@login_required
def transfer():
    if request.method=="POST":
        bank = request.form.get('bank')
        if bank != 'cloud':
            flash("Hanya transfer ke Cloud Bank yang tersedia saat ini.", "error")
            return redirect(url_for('transfer'))
            
        to_acc = request.form['to']
        amt = float(request.form['amount'])
        message = request.form.get('message', '')
        to_u = User.query.filter_by(acc_num=to_acc).first()
        
        if to_u is None:
            flash("Nomor rekening tidak ditemukan.", "error")
            return redirect(url_for('transfer'))
            
        if to_u.acc_num == current_user.acc_num:
            flash("Tidak dapat transfer ke rekening sendiri.", "error")
            return redirect(url_for('transfer'))
            
        if amt < 50000:
            flash("Minimal transfer Rp 50.000", "error")
            return redirect(url_for('transfer'))
            
        if current_user.balance < amt:
            flash("Saldo tidak mencukupi.", "error")
            return redirect(url_for('transfer'))
            
        current_user.balance -= amt
        to_u.balance += amt
        
        tx = Transaction(
            sender_id=current_user.id,
            receiver_id=to_u.id,
            amount=amt,
            timestamp=datetime.now(),
            message=message
        )
        db.session.add(tx)
        db.session.commit()
        
        # Render success page instead of redirecting
        return render_template(
            "transfer_success.html",
            transaction=tx,
            sender=current_user,
            receiver=to_u,
            user=current_user,
            active_page="transfer"
        )
        
    return render_template(
        "transfer.html",
        user=current_user,
        active_page="transfer"
    )

@app.route("/history")
@login_required
def history():
    txs = Transaction.query.filter(
        (Transaction.sender_id==current_user.id) |
        (Transaction.receiver_id==current_user.id)
    ).order_by(Transaction.timestamp.desc()).all()
    return render_template(
        "history.html",
        user=current_user,
        active_page="history",
        transactions=txs
    )

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    # (Add any per-user settings logic here)
    return render_template(
        "settings.html",
        user=current_user,
        active_page="settings"
    )

@app.route("/admin", methods=["GET","POST"])
@login_required
def admin_panel():
    if current_user.role not in (RoleEnum.admin, RoleEnum.owner):
        abort(403)

    cfg = Config.query.first()
    users = User.query.order_by(User.id).all()
    selected_user_id = request.args.get('user_id', type=int)
    selected_user = User.query.get(selected_user_id) if selected_user_id else None

    # Owner-only: create user
    if request.method=="POST" and 'create_user' in request.form:
        if current_user.role != RoleEnum.owner:
            abort(403)
        uname = request.form['new_username']
        email = request.form['new_email']
        
        # Check if username exists
        if User.query.filter_by(username=uname).first():
            flash("Username taken", "error")
            return redirect(url_for('admin_panel'))
            
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for('admin_panel'))
            
        # Create new user
        u = User(
            username=uname,
            email=email,
            password=generate_password_hash(request.form['new_password']),
            role=RoleEnum(request.form['new_role']),
            created_at=datetime.now(),
            ip_address=get_ip()
        )
        db.session.add(u)
        db.session.commit()
        flash("User created successfully", "success")
        return redirect(url_for('admin_panel'))

    # Delete user
    if request.method=="POST" and 'delete_user' in request.form:
        if not (current_user.role == RoleEnum.owner or 
                (current_user.role == RoleEnum.admin and current_user.has_permission(AdminPermissions.DELETE_USER))):
            abort(403)
            
        user_id = request.form['delete_user']
        user_to_delete = User.query.get_or_404(user_id)
        
        # Cannot delete owner or self
        if user_to_delete.role == RoleEnum.owner or user_to_delete.id == current_user.id:
            abort(403)
            
        # Delete profile photo if not default
        if user_to_delete.profile_photo != 'default.png':
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user_to_delete.profile_photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                
        # Delete user's transactions
        Transaction.query.filter(
            (Transaction.sender_id == user_id) |
            (Transaction.receiver_id == user_id)
        ).delete()
        
        # Delete the user
        db.session.delete(user_to_delete)
        db.session.commit()
        
        flash("User deleted successfully", "success")
        return redirect(url_for('admin_panel'))

    return render_template(
        "admin_panel.html",
        user=current_user,
        active_page="admin",
        users=users,
        cfg=cfg,
        selected_user=selected_user,
        AdminPermissions=AdminPermissions
    )

@app.route("/admin/permissions/update", methods=["POST"])
@login_required
def update_permissions():
    if current_user.role not in (RoleEnum.admin, RoleEnum.owner):
        return jsonify({
            'success': False,
            'message': 'Unauthorized access'
        }), 403

    data = request.get_json()
    user_id = data.get('user_id')
    permission = data.get('permission')
    enabled = data.get('enabled')

    # Validate input
    if not all([user_id, permission, enabled is not None]):
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400

    # Get target user
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404

    # Only owner can modify admin permissions
    if current_user.role != RoleEnum.owner and target_user.role == RoleEnum.admin:
        return jsonify({
            'success': False,
            'message': 'Only owner can modify admin permissions'
        }), 403

    # Validate permission
    if permission not in AdminPermissions.get_all_permissions():
        return jsonify({
            'success': False,
            'message': 'Invalid permission'
        }), 400

    try:
        target_user.set_permission(permission, enabled)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Permission {'granted' if enabled else 'revoked'} successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating permission: {str(e)}'
        }), 500

@app.route("/ban/<int:uid>")
@login_required
def ban_user(uid):
    # Check if user has permission to ban
    if not (current_user.role == RoleEnum.owner or 
            (current_user.role == RoleEnum.admin and current_user.has_permission(AdminPermissions.BAN_USER))):
        abort(403)
        
    u = User.query.get_or_404(uid)
    
    # Cannot ban owners
    if u.role == RoleEnum.owner:
        flash("Cannot ban owners.", "error")
        return redirect(url_for('admin_panel'))
        
    # Cannot ban yourself
    if u.id == current_user.id:
        flash("Cannot ban yourself.", "error")
        return redirect(url_for('admin_panel'))
        
    # Admins cannot ban other admins
    if current_user.role == RoleEnum.admin and u.role == RoleEnum.admin:
        flash("Admins cannot ban other admins.", "error")
        return redirect(url_for('admin_panel'))
        
    u.is_banned = not u.is_banned
    db.session.commit()
    
    flash(
        f"User {'banned' if u.is_banned else 'unbanned'} successfully.", 
        "success"
    )
    return redirect(url_for('admin_panel'))

@app.route("/role/<int:uid>", methods=["POST"])
@login_required
def change_role(uid):
    target = User.query.get_or_404(uid)
    new_role = RoleEnum(request.form['role'])
    cfg = Config.query.first()

    # Owner can't be demoted by anyone
    if target.role == RoleEnum.owner and target.id != current_user.id:
        flash("Cannot demote owner.", "error")
        return redirect(url_for('admin_panel'))

    # Owner can do anything except demote themselves
    if current_user.role == RoleEnum.owner:
        if target.id == current_user.id and new_role != RoleEnum.owner:
            flash("Cannot demote yourself.", "error")
        else:
            target.role = new_role
            target.promoted_by = current_user
            db.session.commit()
            flash("Role updated.", "success")
        return redirect(url_for('admin_panel'))

    # Admin permissions
    if current_user.role == RoleEnum.admin:
        # Can only promote to user or admin (if allowed)
        if new_role not in (RoleEnum.user, RoleEnum.admin):
            flash("Not permitted.", "error")
            return redirect(url_for('admin_panel'))
            
        # Can only promote to admin if config allows
        if new_role == RoleEnum.admin and not cfg.admin_can_promote:
            flash("Not permitted.", "error")
            return redirect(url_for('admin_panel'))
            
        # Can only demote users they promoted
        if target.role == RoleEnum.admin and target.promoted_by_id != current_user.id:
            flash("You can only demote admins that you promoted.", "error")
            return redirect(url_for('admin_panel'))

        target.role = new_role
        target.promoted_by = current_user
        db.session.commit()
        flash("Role updated.", "success")
        return redirect(url_for('admin_panel'))

    abort(403)

def format_rupiah(number):
    return "{:,.2f}".format(number).replace('.', '#').replace(',', '.').replace('#', ',')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/update_profile_photo', methods=['POST'])
@login_required
def update_profile_photo():
    if 'profile_photo' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('account'))
    
    file = request.files['profile_photo']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('account'))
    
    if file and allowed_file(file.filename):
        try:
            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > MAX_FILE_SIZE:
                flash('File size too large. Maximum size is 5MB', 'error')
                return redirect(url_for('account'))
            
            # Delete old profile photo if it exists and is not the default
            if current_user.profile_photo != 'default.png':
                old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
            
            # Generate unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            filename = secure_filename(filename)
            
            # Save new photo
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Update database
            current_user.profile_photo = filename
            db.session.commit()
            
            flash('Profile photo updated successfully', 'success')
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('Invalid file type. Allowed types are: PNG, JPG, JPEG, WebP', 'error')
    
    return redirect(url_for('account'))

@app.route("/settings/update", methods=["POST"])
@login_required
def update_settings():
    setting_type = request.form.get('type')
    value = request.form.get('value')
    
    if setting_type == 'display':
        field = request.form.get('field')
        if field == 'language':
            current_user.language = value
        elif field == 'dark_mode':
            current_user.dark_mode = (value == 'true')
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid setting type'})

@app.route("/admin/transactions/<int:uid>")
@login_required
def get_user_transactions(uid):
    # Check if user has permission to view transactions
    if not (current_user.role == RoleEnum.owner or 
            (current_user.role == RoleEnum.admin and current_user.has_permission(AdminPermissions.VIEW_TRANSACTIONS))):
        abort(403)
        
    # Get user's transactions
    transactions = Transaction.query.filter(
        (Transaction.sender_id == uid) | (Transaction.receiver_id == uid)
    ).order_by(Transaction.timestamp.desc()).all()
    
    # Format transactions for JSON response
    transactions_data = []
    for tx in transactions:
        transactions_data.append({
            'id': tx.id,
            'sender_id': tx.sender_id,
            'receiver_id': tx.receiver_id,
            'sender_username': tx.sender.username,
            'receiver_username': tx.receiver.username,
            'amount': tx.amount,
            'message': tx.message,
            'timestamp': tx.timestamp.strftime("%d %B %Y %H:%M")
        })
    
    return jsonify({
        'success': True,
        'transactions': transactions_data
    })

@app.route("/update_account", methods=["POST"])
@login_required
def update_account():
    # Get form data
    username = request.form.get('username')
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    current_password = request.form.get('current_password')
    
    # Verify current password
    if not check_password_hash(current_user.password, current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for('account'))
        
    # Check if username exists (if changed)
    if username != current_user.username:
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for('account'))
            
    # Check if email exists (if changed)
    if email != current_user.email:
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for('account'))
    
    # Update user information
    current_user.username = username
    current_user.email = email
    
    # Update password if provided
    if new_password:
        current_user.password = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        flash("Account updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating account: {str(e)}", "error")
    
    return redirect(url_for('account'))

if __name__=="__main__":
    app.run(debug=True)
