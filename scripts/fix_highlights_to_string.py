# scripts/fix_highlights_to_string.py

from app.db.session import SessionLocal
from app.models.reports import SessionReport

def main():
    db = SessionLocal()
    reports = db.query(SessionReport).all()
    changed = 0

    for r in reports:
        if isinstance(r.highlights, list):
            r.highlights = "\n".join(str(v) for v in r.highlights)
            changed += 1

    db.commit()
    db.close()
    print(f"Updated {changed} reports.")

if __name__ == "__main__":
    main()