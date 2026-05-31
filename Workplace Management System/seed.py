"""
Run once to seed the database with demo data.
Usage: python seed.py
"""
from app import create_app
from models import db, User, Team

app = create_app()

with app.app_context():
    db.create_all()

    # Teams
    if not Team.query.first():
        t1 = Team(name='Engineering')
        t2 = Team(name='Marketing')
        db.session.add_all([t1, t2])
        db.session.flush()

        # Executive
        exec_user = User(first_name='Alice', last_name='Smith',
                         email='alice@demo.com', role='executive')
        exec_user.set_password('password')

        # Team leaders
        tl1 = User(first_name='Bob', last_name='Jones',
                   email='bob@demo.com', role='team_leader', team_id=t1.id)
        tl1.set_password('password')

        tl2 = User(first_name='Carol', last_name='White',
                   email='carol@demo.com', role='team_leader', team_id=t2.id)
        tl2.set_password('password')

        # Operators
        op1 = User(first_name='Dave', last_name='Brown',
                   email='dave@demo.com', role='operator', team_id=t1.id)
        op1.set_password('password')

        op2 = User(first_name='Eve', last_name='Davis',
                   email='eve@demo.com', role='operator', team_id=t2.id)
        op2.set_password('password')

        db.session.add_all([exec_user, tl1, tl2, op1, op2])
        db.session.commit()
        print("Seeded successfully.")
        print("\nDemo accounts (password: 'password'):")
        print("  alice@demo.com  — Executive")
        print("  bob@demo.com    — Team Leader (Engineering)")
        print("  carol@demo.com  — Team Leader (Marketing)")
        print("  dave@demo.com   — Operator (Engineering)")
        print("  eve@demo.com    — Operator (Marketing)")
    else:
        print("Database already seeded.")
