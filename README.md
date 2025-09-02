Make sure venv is active:

source venv/bin/activate:

then we gotta create the database:

createdb warbler

Then we gotta make sure DB exists and tables are created:

createdb warbler 
python - <<'PY'
from app import app
from models import db
with app.app_context():
    db.create_all()
    print("Tables ready.")
PY

then flask run!
