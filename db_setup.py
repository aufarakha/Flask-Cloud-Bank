from app import app, db
from models import User, Config
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()

    # Create owner account
    owner = User(
        username="owner",
        email="owner@cloudbank.com",
        password=generate_password_hash("ownerpass"),
        role="owner",
        created_at=datetime.now(),
        ip_address="127.0.0.1",
        promoted_by=None  # Owner has no promoter
    )
    db.session.add(owner)

    # Ensure config row exists
    cfg = Config(admin_can_promote=False)
    db.session.add(cfg)

    db.session.commit()
    print("✅ DB initialized (owner + config).")
