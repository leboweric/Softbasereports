from werkzeug.security import generate_password_hash

password = "abc123"
password_hash = generate_password_hash(password)

print("Password hash for 'abc123':")
print(password_hash)
print("\n--- SQL UPDATE STATEMENTS ---\n")

emails = ['dmeyer@bmhmn.com', 'mmikota@bmhmn.com', 'dgritti@bmhmn.com']

for email in emails:
    print(f"UPDATE \"user\" SET password_hash = '{password_hash}' WHERE email = '{email}';")