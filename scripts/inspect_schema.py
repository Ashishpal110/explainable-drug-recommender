import sqlite3

conn = sqlite3.connect('data/processed/drug_system.db')
c = conn.cursor()
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;")
for row in c.fetchall():
    print(f"Table: {row[0]}")
    print(row[1])
    print("-" * 50)

for tbl in ['drugs', 'conditions', 'drug_conditions', 'allergy_crosswalk', 'drug_interactions', 'contraindications', 'recommendation_audit_logs']:
    c.execute(f"SELECT COUNT(*) FROM {tbl};")
    print(f"{tbl}: {c.fetchone()[0]} rows")

conn.close()
