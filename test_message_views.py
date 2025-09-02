"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from unittest import TestCase
from app import app, CURR_USER_KEY
from models import db, User, Message

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewsTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()
        self.client = app.test_client()

        u = User.signup("u", "u@test.com", "password", None)
        db.session.commit()
        self.u = u

    def tearDown(self):
        db.session.rollback()

    def login(self):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u.id

    def test_add_and_delete_message(self):
        self.login()
        resp = self.client.post("/messages/new", data={"text": "hello"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        m = Message.query.filter_by(text="hello").first()
        self.assertIsNotNone(m)

        resp = self.client.post(f"/messages/{m.id}/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(Message.query.get(m.id))

    def test_cannot_delete_others_message(self):
        # create other user + message
        u2 = User.signup("u2", "u2@test.com", "password", None)
        db.session.commit()
        m2 = Message(text="yo", user_id=u2.id)
        db.session.add(m2); db.session.commit()

        self.login()
        resp = self.client.post(f"/messages/{m2.id}/delete", follow_redirects=True)
        self.assertIn(b"only delete your own", resp.data)
        self.assertIsNotNone(Message.query.get(m2.id))