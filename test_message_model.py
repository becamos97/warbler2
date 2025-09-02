import os
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from unittest import TestCase
from app import app
from models import db, User, Message

app.config['WTF_CSRF_ENABLED'] = False

class MessageModelTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()
        u = User.signup("u", "u@test.com", "password", None)
        db.session.commit()
        self.u = u

    def tearDown(self):
        db.session.rollback()

    def test_message_make(self):
        m = Message(text="a"*140, user_id=self.u.id)
        db.session.add(m)
        db.session.commit()
        self.assertEqual(m.user_id, self.u.id)

    def test_text_limit(self):
        m = Message(text="a"*141, user_id=self.u.id)
        db.session.add(m)
        with self.assertRaises(Exception):
            db.session.commit()