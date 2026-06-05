password = "admin123"

def run_query(user_id):
    query = f"SELECT * FROM users WHERE id={user_id}"
    return query