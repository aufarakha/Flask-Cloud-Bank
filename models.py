from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from enum import Enum
import random
import string

db = SQLAlchemy()

class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"
    owner = "owner"

# Define admin permissions
class AdminPermissions:
    CREATE_USER = 'create_user'
    DELETE_USER = 'delete_user'
    BAN_USER = 'ban_user'
    PROMOTE_USER = 'promote_user'
    VIEW_TRANSACTIONS = 'view_transactions'
    MANAGE_PERMISSIONS = 'manage_permissions'
    
    @staticmethod
    def get_all_permissions():
        return {
            AdminPermissions.CREATE_USER: 'Create Users',
            AdminPermissions.DELETE_USER: 'Delete Users',
            AdminPermissions.BAN_USER: 'Ban/Unban Users',
            AdminPermissions.PROMOTE_USER: 'Promote/Demote Users',
            AdminPermissions.VIEW_TRANSACTIONS: 'View All Transactions',
            AdminPermissions.MANAGE_PERMISSIONS: 'Manage Admin Permissions'
        }

def generate_account_number():
    # Generate 4 groups of 4 digits
    groups = []
    for _ in range(4):
        group = ''.join(random.choices(string.digits, k=4))
        groups.append(group)
    # Join with spaces
    return ' '.join(groups)

class User(UserMixin, db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    acc_num      = db.Column(db.String(19), unique=True, nullable=False, default=generate_account_number)  # 16 digits + 3 spaces
    email        = db.Column(db.String(120), unique=True, nullable=False)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    role         = db.Column(db.Enum(RoleEnum), default=RoleEnum.user, nullable=False)
    balance      = db.Column(db.Float, default=0)
    savings      = db.Column(db.Float, default=0)
    is_banned    = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, nullable=False)
    ip_address   = db.Column(db.String(100))
    profile_photo = db.Column(db.String(200), default='default.png')  # Profile photo field
    
    # Track who promoted this user
    promoted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    promoted_by = db.relationship('User', remote_side=[id], backref='promoted_users')
    
    # Admin permissions (stored as comma-separated string)
    admin_permissions = db.Column(db.String(500), default='')
    
    # Display preferences
    language = db.Column(db.String(5), default='id')  # 'id' for Indonesian, 'en' for English
    dark_mode = db.Column(db.Boolean, default=False)

    def get_id(self):
        return self.acc_num

    def has_permission(self, permission):
        if self.role == RoleEnum.owner:
            return True
        if self.role != RoleEnum.admin:
            return False
        return permission in (self.admin_permissions or '').split(',')
        
    def set_permission(self, permission, value):
        if self.role != RoleEnum.admin:
            return
            
        current_permissions = set((self.admin_permissions or '').split(','))
        if value:
            current_permissions.add(permission)
        else:
            current_permissions.discard(permission)
            
        # Remove empty string if present
        current_permissions.discard('')
        self.admin_permissions = ','.join(sorted(current_permissions))

class Config(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    admin_can_promote = db.Column(db.Boolean, default=False)

class Transaction(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    sender_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount       = db.Column(db.Float, nullable=False)
    timestamp    = db.Column(db.DateTime, nullable=False)
    message      = db.Column(db.String(200), nullable=True)  # Adding message field

    sender       = db.relationship('User', foreign_keys=[sender_id], backref='sent_transactions')
    receiver     = db.relationship('User', foreign_keys=[receiver_id], backref='received_transactions')
