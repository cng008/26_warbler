"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        u = User.signup("test111", "email111@email.com", "password", None)
        u.id = 111
        self.uid = u.id

        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="this is a test message",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "this is a test message")


    def test_message_like(self):
        m1 = Message(
            text="this is a test message",
            user_id=self.uid
        )

        m2 = Message(
            text="warble is fun",
            user_id=self.uid
        )

        u = User.signup("testliker", "testliker@email.com", "password", None)
        u.id = 222
        db.session.add_all([m1, m2])
        db.session.commit()

        rel = Likes(user_id=222, message_id=1)
        db.session.add(rel)
        db.session.commit()

        l = Likes.query.filter(Likes.user_id == u.id).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)
