import bcrypt
from database import get_connection


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def create_user(username, password, name, role):
    connection = get_connection()

    try:
        password_hash = hash_password(password)

        connection.execute("""
            INSERT INTO users (username, password_hash, name, role)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, name, role))

        connection.commit()
        return True

    except Exception:
        return False

    finally:
        connection.close()


def login_user(username, password):
    connection = get_connection()

    user = connection.execute("""
        SELECT user_id, username, password_hash, name, role
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    connection.close()

    if user is None:
        return None

    if verify_password(password, user["password_hash"]):
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"]
        }

    return None