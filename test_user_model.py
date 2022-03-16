"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Follows

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


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Follows.query.delete()

        u1 = User.signup("test1", "email1@email.com", "password", None)
        u1.id = 111

        u2 = User.signup("test2", "email2@email.com", "password", None)
        u2.id = 222

        db.session.commit()

        u1 = User.query.get(u1.id)
        u2 = User.query.get(u2.id)

        self.u1 = u1
        self.u1id = u1.id

        self.u2 = u2
        self.u2id = u2.id

        self.client = app.test_client()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # test repr method
        self.assertEqual(u.__repr__(), "<User #1: testuser, test@test.com>")


####### FOLLOWING TESTS ######################
    def test_is_following(self):
        """Does user1 follow user2?"""

        rel = Follows(user_being_followed_id=222, user_following_id=111)
        db.session.add(rel)
        db.session.commit()

        self.assertEqual(self.u1.is_following(self.u2), 1)
        self.assertEqual(self.u2.is_following(self.u1), 0)


    def test_is_followed_by(self):
        """Does user2 follow user1?"""

        rel = Follows(user_being_followed_id=111, user_following_id=222)
        db.session.add(rel)
        db.session.commit()

        self.assertEqual(self.u2.is_following(self.u1), 1)
        self.assertEqual(self.u1.is_following(self.u2), 0)


####### SIGNUP TESTS ######################
    def test_valid_signup(self):
        u3 = User.signup("testnew", "emailnew@email.com", "password", None)
        u3.id = 333
        db.session.commit()

        u3 = User.query.get(u3.id)
        self.assertEqual(u3.username, "testnew")
        self.assertEqual(u3.email, "emailnew@email.com")
        self.assertNotEqual(u3.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u3.password.startswith("$2b$"))


    def test_invalid_username_signup(self):
        invalid = User.signup(None, "testest@email.com", "password", None)
        invalid.id = 9999
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_email_signup(self):
        invalid = User.signup("testest", None, "password", None)
        invalid.id = 8888
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)
    

####### AUTHENTICATION TESTS ######################
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1.id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "notpassword"))
