"""
Query payments table to check if Gumroad webhook has written data.
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('clearlease.db')
cursor = conn.cursor()

# Execute the query
cursor.execute("SELECT id, buyer_email, paid, created_at FROM payments ORDER BY created_at DESC LIMIT 5;")

# Fetch all results
results = cursor.fetchall()

# Print the results
print("=== Payments Table Records ===")
if results:
    print(f"Found {len(results)} records")
    print("ID, Buyer Email, Paid, Created At")
    for row in results:
        print(f"{row[0]}, {row[1]}, {row[2]}, {row[3]}")
else:
    print("No records found in payments table")

# Close the connection
conn.close()
