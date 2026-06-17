from app.models import engine, init_db
from sqlalchemy import text

# Initialize the database
init_db()

with engine.connect() as c:
    tables = c.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print('=== TABLES ===')
    for t in tables:
        print(t[0])

    print()
    print('=== PROJECTS ===')
    print(c.execute(text('SELECT * FROM projects')).fetchall())

    print()
    print('=== STEPS ===')
    print(c.execute(text('SELECT * FROM steps')).fetchall())

    print()
    print('=== TASKS ===')
    print(c.execute(text('SELECT * FROM tasks')).fetchall())

    print()
    print('=== MILESTONES ===')
    print(c.execute(text('SELECT * FROM milestones')).fetchall())

    print()
    print('=== CHAT SESSIONS ===')
    print(c.execute(text('SELECT * FROM chat_sessions')).fetchall())

    print()
    print('=== CHAT MESSAGES ===')
    print(c.execute(text('SELECT * FROM chat_messages')).fetchall())

    print()
    print('=== DECISIONS ===')
    print(c.execute(text('SELECT * FROM decisions')).fetchall())