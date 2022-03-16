"""User views tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()
        # Follows.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 8888
        self.u1 = User.signup("george", "george@test.com", "password", None)
        self.u1.id = 1111
        self.u2 = User.signup("elliot", "elliot@test.com", "password", None)
        self.u2.id = 2222
        self.u3 = User.signup("bob", "bob@test.com", "password", None)
        self.u3.id = 3333
        self.u4 = User.signup("frank", "frank@test.com", "password", None)
        self.u4.id = 4444

        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@george", str(resp.data))
            self.assertIn("@elliot", str(resp.data))
            self.assertIn("@bob", str(resp.data))
            self.assertIn("@frank", str(resp.data))


    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=e")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@george", str(resp.data))
            self.assertIn("@elliot", str(resp.data))

            self.assertNotIn("@bob", str(resp.data))
            self.assertNotIn("@frank", str(resp.data))


    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))


    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.testuser.id)
        m2 = Message(text="who wants to get lunch?", user_id=self.testuser.id)
        m3 = Message(id=1234, text="likable warble", user_id=self.u1.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser.id, message_id=1234)

        db.session.add(l1)
        db.session.commit()


    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 2 messages
            self.assertIn("2", found[0].text)

            # Test for a count of 0 followers
            self.assertIn("0", found[1].text)

            # Test for a count of 0 following
            self.assertIn("0", found[2].text)

            # Test for a count of 1 like
            self.assertIn("1", found[3].text)


    def test_add_like(self):
        m = Message(id=1996, text="march madness", user_id=self.u1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1996/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1996).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser.id)


    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser.id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser.id and Likes.message_id==m.id
        ).one()

        # Now we are sure that testuser likes the message "likable warble"
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)


    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.testuser.id)
        f2 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.testuser.id)
        f3 = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u1.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()


    def test_user_show_with_follows(self):
        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")
        
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)


    def test_add_follow(self):
        f = Follows(user_being_followed_id=self.u2.id, user_following_id=self.u1.id)
        db.session.add(f)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.post("/users/follow/2222", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            follows = Follows.query.filter(Follows.user_following_id==1111).all()
            self.assertEqual(len(follows), 1)
            self.assertEqual(follows[0].user_following_id, self.u1.id)


    def test_remove_follow(self):
        self.setup_followers()

        f = Follows.query.filter(Follows.user_being_followed_id==2222)
        self.assertIsNotNone(f)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/stop-following/2222", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            follows = Follows.query.filter(Follows.user_being_followed_id==2222).all()
            # the follow has been removed
            self.assertEqual(len(follows), 0)


    def test_show_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@george", str(resp.data))
            self.assertIn("@elliot", str(resp.data))
            self.assertNotIn("@bob", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))


    def test_show_followers(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")

            self.assertIn("@george", str(resp.data))
            self.assertNotIn("@elliot", str(resp.data))
            self.assertNotIn("@bob", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))


    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@george", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))


    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@george", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
