from database import get_connection
from auth import hash_password


username = input("Enter the username to reset: ")
new_password = input("Enter the new password: ")

connection = get_connection()

existing = connection.execute(
    "SELECT user_id FROM users WHERE username = ?",
    (username,)
).fetchone()

if existing is None:
    print(f"No user found with username '{username}'.")

else:
    password_hash = hash_password(new_password)

    connection.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (password_hash, username)
    )

    connection.commit()
    print(f"Password for '{username}' has been reset successfully!")

connection.close()
