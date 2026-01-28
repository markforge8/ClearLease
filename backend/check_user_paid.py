"""
Check the paid status of a specific user in the database.
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('clearlease.db')
cursor = conn.cursor()

# Execute the query to check user's paid status
cursor.execute("SELECT id, email, paid FROM user_profiles WHERE email = 'newuser@example.com';")

# Fetch the result
result = cursor.fetchone()

# Print the result
print("=== User Paid Status ===")
if result:
    print(f"ID: {result[0]}")
    print(f"Email: {result[1]}")
    print(f"Paid: {result[2]}")
else:
    print("User not found")

# Close the connection
conn.close()
