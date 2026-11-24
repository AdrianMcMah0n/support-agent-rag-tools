"""The actions the agent may take. Each one checks its own inputs: the model never gets data it should not see."""
import re
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / 'data' / 'store.db'

SCHEMAS = [
    {'type': 'function', 'function': {
        'name': 'search_kb', 'description': 'Search the store policy documents (shipping, returns, warranty, payments, '
        'order changes, international, rewards, support hours). Returns sections with ids to cite.',
        'parameters': {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'get_order', 'description': 'Look up one order. Needs BOTH the order number and the email used on the order.',
        'parameters': {'type': 'object', 'properties': {'order_id': {'type': 'string'}, 'email': {'type': 'string'}},
                       'required': ['order_id', 'email'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'create_ticket', 'description': 'Open a ticket for the human support team (damaged item, wrong item, '
        'anything the documents do not cover). Needs the order number, the email and a one-line summary.',
        'parameters': {'type': 'object', 'properties': {'order_id': {'type': 'string'}, 'email': {'type': 'string'},
                                                       'summary': {'type': 'string'}},
                       'required': ['order_id', 'email', 'summary'], 'additionalProperties': False}}},
]


def _email_ok(e: str) -> bool:
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', e or ''))


def get_order(order_id: str, email: str, db: Path = DB) -> dict:
    """Order details only when the email matches the order. A mismatch and a missing order look the same,
    so the tool cannot be used to find out which order numbers exist."""
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    row = con.execute('select * from orders where order_id = ?', (str(order_id).strip(),)).fetchone()
    con.close()
    if not row or row['email'].lower() != (email or '').strip().lower():
        return {'found': False, 'message': 'No order matches that order number and email.'}
    d = dict(row)
    d.pop('email')
    return {'found': True, **d}


def create_ticket(order_id: str, email: str, summary: str, db: Path = DB) -> dict:
    if not _email_ok(email):
        return {'created': False, 'message': 'A valid email is needed to open a ticket.'}
    if get_order(order_id, email, db)['found'] is False:
        return {'created': False, 'message': 'No order matches that order number and email.'}
    con = sqlite3.connect(db)
    cur = con.execute('insert into tickets (order_id, email, summary) values (?,?,?)', (order_id, email.lower(), summary[:300]))
    con.commit()
    tid = cur.lastrowid
    con.close()
    return {'created': True, 'ticket_id': f'T-{tid:05d}', 'reply_within': '1 business day'}
