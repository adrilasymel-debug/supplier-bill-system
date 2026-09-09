from auth import create_user


username = input("Enter username: ")
password = input("Enter password: ")
name = input("Enter name: ")

role = input("Enter role (boss/staff): ").lower()

if role not in ["boss", "staff"]:
    print("Invalid role. Please enter boss or staff.")
else:
    success = create_user(username, password, name, role)

    if success:
        print("User created successfully!")
    else:
        print("Could not create user. Username may already exist.")