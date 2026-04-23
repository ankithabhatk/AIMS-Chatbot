from app.services.lead_store import get_connection
from app.brain.lead_queue import get_next_leads
from app.services.lead_dispatcher import assign_lead


def run():
    conn = get_connection()
    cur = conn.cursor()

    leads = get_next_leads(cur, limit=10)
    
    if not leads:
        print("Queue is empty. No new leads to assign.")

    for lead in leads:
        result = assign_lead(cur, lead)
        print("Assigned:", result)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
