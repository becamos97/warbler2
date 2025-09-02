"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from unittest import TestCase
from app import app
from models import db, User, Message


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

app.config['WTF_CSRF_ENABLED'] = False


# Now we can import app



# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


class UserModelTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()
        u1 = User.signup("u1", "u1@test.com", "password", None)
        u2 = User.signup("u2", "u2@test.com", "password", None)
        db.session.commit()
        self.u1 = u1
        self.u2 = u2

    def tearDown(self):
        db.session.rollback()

    def test_signup_and_authenticate(self):
        u = User.authenticate("u1", "password")
        self.assertTrue(u)
        self.assertEqual(u.id, self.u1.id)
        bad = User.authenticate("u1", "nope")
        self.assertFalse(bad)

    def test_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertTrue(self.u2.is_followed_by(self.u1))

    def test_likes_relationship(self):
        m = Message(text="hi", user_id=self.u2.id)
        db.session.add(m)
        db.session.commit()
        self.u1.liked_messages.append(m)
        db.session.commit()
        self.assertIn(m, self.u1.liked_messages)
        self.assertIn(self.u1, m.liked_by)