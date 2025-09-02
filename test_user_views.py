import os
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from unittest import TestCase
from app import app, CURR_USER_KEY
from models import db, User, Message

app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()
        self.client = app.test_client()

        u1 = User.signup("u1", "u1@test.com", "password", None)
        u2 = User.signup("u2", "u2@test.com", "password", None)
        db.session.commit()
        self.u1 = u1
        self.u2 = u2

        m2 = Message(text="hello", user_id=u2.id)
        db.session.add(m2)
        db.session.commit()
        self.m2 = m2

    def tearDown(self):
        db.session.rollback()

    def login(self, user_id):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user_id

    def test_follow_unfollow(self):
        self.login(self.u1.id)
        resp = self.client.post(f"/users/follow/{self.u2.id}", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.u1.is_following(self.u2))

        resp = self.client.post(f"/users/stop-following/{self.u2.id}", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.u1.is_following(self.u2))

    def test_like_toggle(self):
        self.login(self.u1.id)
        resp = self.client.post(f"/messages/{self.m2.id}/like", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.m2, self.u1.liked_messages)

        resp = self.client.post(f"/messages/{self.m2.id}/like", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.m2, self.u1.liked_messages)

    def test_like_own_message_forbidden(self):
        self.login(self.u2.id)
        resp = self.client.post(f"/messages/{self.m2.id}/like", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        # flashes “cannot like your own message” and nothing added
        self.assertNotIn(self.m2, self.u2.liked_messages)

    def test_profile_edit_requires_auth(self):
        resp = self.client.get("/users/profile", follow_redirects=True)
        self.assertIn(b"Access unauthorized", resp.data)

    def test_profile_edit_success(self):
        self.login(self.u1.id)
        resp = self.client.post("/users/profile", data={
            "username": "u1",
            "email": "u1@test.com",
            "image_url": "",
            "header_image_url": "",
            "bio": "hey there",
            "location": "CLT",
            "password": "password"
        }, follow_redirects=True)
        self.assertIn(b"Profile updated!", resp.data)
        self.assertEqual(User.query.get(self.u1.id).bio, "hey there")