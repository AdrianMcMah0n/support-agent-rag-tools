"""Create data/store.db with fictional orders (Larkspur Home is an invented store; every name and email is made up)."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / 'store.db'
ORDERS = [
    # order_id, email, status, items, ordered, shipped, carrier, tracking, total
    ('1001', 'maya.r@example.com', 'Delivered', 'Oak side table', '2026-10-28', '2026-10-29', 'UPS', '1Z999AA10123456784', 189.00),
    ('1002', 'tom.h@example.com', 'Shipped', 'Linen cushion covers (2)', '2026-11-18', '2026-11-19', 'USPS', '9400111899223344556677', 42.50),
    ('1003', 'priya.k@example.com', 'Processing', 'Brass floor lamp', '2026-11-23', None, None, None, 265.00),
    ('1004', 'leo.b@example.com', 'Cancelled', 'Scented candle set', '2026-11-10', None, None, None, 36.00),
    ('1005', 'ana.s@example.com', 'Shipped', 'Walnut bookshelf', '2026-11-20', '2026-11-21', 'UPS', '1Z999AA10198765432', 420.00),
]


def build(path: Path = DB) -> Path:
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
        create table orders (order_id text primary key, email text, status text, items text, ordered text,
                             shipped text, carrier text, tracking text, total real);
        create table tickets (ticket_id integer primary key autoincrement, order_id text, email text,
                              summary text, created text default (datetime('now')));""")
    con.executemany('insert into orders values (?,?,?,?,?,?,?,?,?)', ORDERS)
    con.commit()
    con.close()
    return path


if __name__ == '__main__':
    print('wrote', build())
