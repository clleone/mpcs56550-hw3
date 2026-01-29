import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_db


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_db():
    """Clean up the database before each test"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts where username = 'test_user'")
    conn.commit()
    cursor.close()
    conn.close()
    yield


@pytest.fixture
def test_user():
    "Get test user"
    return {
        "username": "test_user",
        "password": "test_pass",
        "email": "example@gmail.com",
    }


def test_register_new_user(client, clean_db, test_user):
    """Test that a new user can successfully register"""
    # ping register and check response
    response = client.post("/register", data=test_user, follow_redirects=True)
    assert response.status_code == 200

    # see if user landed in db
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM accounts WHERE username = %s", (test_user["username"],)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # check that db info is as expected
    assert user is not None
    assert user["username"] == test_user["username"]
    assert user["password"] == test_user["password"]
    assert user["email"] == test_user["email"]


def test_existing_acct(client, test_user):
    """Test that login tells you if you already have an account w an email."""
    # try to create exactly identical redundant account
    response = client.post("/register", data=test_user, follow_redirects=True)
    assert response.status_code == 200

    # check login message
    assert b"There is already an account associated with that email." in response.data


def test_duplicate_registration(client, test_user):
    """Test that you cannot create new user w existing username"""
    # we have test_user from previous test
    # attempt duplicate user w same username
    test_user_2 = test_user
    test_user_2["email"] = "different@aol.com"
    response = client.post("/register", data=test_user_2, follow_redirects=True)
    assert b"That username is not available." in response.data

    # see how many users with username
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COUNT(*) AS count FROM accounts WHERE username = %s",
        (test_user["username"],),
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    assert result["count"] == 1


def test_login_with_valid_credentials(client, test_user):
    """Test that user will valid credentials can log in."""
    # ping login for test acct
    response = client.post("/login", data=test_user, follow_redirects=True)
    assert response.status_code == 200

    # Assert: check session exists
    with client.session_transaction() as sess:
        assert sess.get("username") == test_user["username"]

    assert b"Welcome, " + test_user["username"].encode() in response.data


def test_login_with_invalid_password(client, test_user):
    """Test login with invalid password."""
    # recreate test_user but with typo in password
    typo_user = test_user
    typo_user["password"] = "test_pasd"  # should be test_pass

    # attempt to login typo_user
    response = client.post("/login", data=typo_user, follow_redirects=True)
    assert response.status_code == 200

    # confirm there is no session
    with client.session_transaction() as sess:
        assert sess.get("loggedin") is None

    # confirm we're sent back to login page
    assert b"Incorrect username/password combination." in response.data


def test_logout(client, test_user):
    """Test that user can logout."""
    # login and confirm login status
    client.post("/login", data=test_user, follow_redirects=True)
    with client.session_transaction() as sess:
        assert sess.get("loggedin") is not None

    # ping logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200

    # confirm there is no session
    with client.session_transaction() as sess:
        assert sess.get("loggedin") is None

    # confirm we're on login page
    assert b"Don't have an account?" in response.data
