import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'crm_pro.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS deals (id TEXT PRIMARY KEY, company TEXT, stage TEXT, value INTEGER, contact_role TEXT, blocker TEXT, success_reason TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transcripts (id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, date TEXT, content TEXT)''')
    conn.commit()
    
    # Reset deals to load the new 20
    conn.execute("DELETE FROM deals")
    conn.execute("DELETE FROM transcripts")
    
    deals = [
        ("D1", "Stark Industries", "Stalled", 500000, "CFO", "Pushing back hard on upfront costs. Wants Net-90.", ""),
        ("D2", "Wayne Enterprises", "Stalled", 250000, "CTO", "Worried about migration downtime.", ""),
        ("D3", "Oscorp", "Closed Won", 800000, "CFO", "", "We structured a milestone-based payment plan tied to deployment phases, neutralizing the risk of upfront costs."),
        ("D4", "Tyrell Corp", "Stalled", 1200000, "CTO", "Needs absolute guarantee against vendor lock-in.", ""),
        ("D5", "Globex", "Stalled", 450000, "VP Security", "Wants an on-prem deployment option which we don't offer.", ""),
        ("D6", "InGen Technologies", "Closed Won", 650000, "VP Engineering", "", "Provided a dedicated technical account manager for the first 30 days and ran the migration over the weekend at no extra cost to alleviate downtime fears."),
        ("D7", "Cyberdyne Systems", "Closed Won", 1500000, "CIO", "", "Overcame vendor lock-in fears by providing a source-code escrow agreement and standardizing our data export APIs."),
        ("D8", "Umbrella Corp", "Closed Won", 950000, "CISO", "", "Solved the on-prem requirement by offering a dedicated single-tenant AWS VPC with direct peering to their network, satisfying their compliance team."),
        ("D9", "Massive Dynamic", "Discovery", 300000, "Director IT", "No clear blocker yet.", ""),
        ("D10", "Aperture Science", "Proposal", 400000, "Lead Researcher", "Budget constraints for this quarter.", ""),
        ("D11", "Black Mesa", "Stalled", 550000, "CTO", "Security team is stalling the review.", ""),
        ("D12", "Weyland-Yutani", "Closed Won", 2200000, "VP Procurement", "", "Offered a multi-year volume discount."),
        ("D13", "Soylent Corp", "Discovery", 150000, "CEO", "Needs a faster onboarding timeline.", ""),
        ("D14", "Virtucon", "Proposal", 280000, "CFO", "Comparing us against a cheaper competitor.", ""),
        ("D15", "Omni Consumer Products", "Closed Won", 1100000, "COO", "", "Provided a custom SLA for their 24/7 operations."),
        ("D16", "LexCorp", "Stalled", 750000, "VP Tech", "Waiting on board approval.", ""),
        ("D17", "Gringotts", "Discovery", 900000, "CISO", "Extremely strict data residency requirements.", ""),
        ("D18", "Acme Corp", "Closed Won", 120000, "Manager", "", "Self-serve onboarding worked perfectly."),
        ("D19", "Spacely Sprockets", "Proposal", 350000, "VP Ops", "Wants a pilot before committing.", ""),
        ("D20", "Cogswell Cogs", "Stalled", 420000, "CIO", "Legacy system integration looks too complex.", "")
    ]
    conn.executemany("INSERT INTO deals VALUES (?, ?, ?, ?, ?, ?, ?)", deals)
    
    transcripts = [
        ("D1", "2026-09-01", "CFO said: 'We can't commit to a 500k upfront payment in this economy.'"),
        ("D2", "2026-09-15", "CTO said: 'If the system goes down during migration, we lose millions. How do you mitigate this?'"),
        ("D4", "2026-09-20", "CTO: 'We got burned by our last vendor. We need guarantees we can get our data and code out.'"),
        ("D5", "2026-09-22", "Security VP: 'Our compliance policy mandates on-prem. We cannot do standard SaaS cloud.'")
    ]
    conn.executemany("INSERT INTO transcripts (deal_id, date, content) VALUES (?, ?, ?)", transcripts)
    conn.commit()
    conn.close()

init_db()
