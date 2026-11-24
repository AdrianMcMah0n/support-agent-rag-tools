"""Guardrails that live in code are tested without calling the API."""
from agent.agent import SupportAgent
from agent.kb import chunks
from agent.tools import create_ticket, get_order
from data.make_db import build


def test_order_needs_matching_email(tmp_path):
    db = build(tmp_path / 'store.db')
    assert get_order('1002', 'tom.h@example.com', db)['status'] == 'Shipped'
    wrong = get_order('1002', 'someone.else@example.com', db)
    missing = get_order('9999', 'tom.h@example.com', db)
    assert wrong == missing == {'found': False, 'message': 'No order matches that order number and email.'}


def test_order_result_never_contains_the_email(tmp_path):
    db = build(tmp_path / 'store.db')
    assert 'email' not in get_order('1001', 'MAYA.R@example.com ', db)


def test_ticket_only_for_a_real_order(tmp_path):
    db = build(tmp_path / 'store.db')
    assert create_ticket('1002', 'tom.h@example.com', 'arrived damaged', db)['ticket_id'] == 'T-00001'
    assert create_ticket('1002', 'not-an-email', 'x', db)['created'] is False
    assert create_ticket('1003', 'tom.h@example.com', 'x', db)['created'] is False


def test_chunk_ids_are_citable():
    ids = [c['id'] for c in chunks()]
    assert 'returns#2' in ids and len(ids) == len(set(ids))


def test_citation_guard():
    ok = SupportAgent._finish('Opened candles cannot be returned [returns#2].', [{'tool': 'search_kb'}], {'returns#2'})
    invented = SupportAgent._finish('Returns take 90 days [returns#9].', [{'tool': 'search_kb'}], {'returns#2'})
    uncited = SupportAgent._finish('Returns take 90 days.', [{'tool': 'search_kb'}], {'returns#2'})
    assert ok['verified'] and not invented['verified'] and not uncited['verified']
    assert invented['invalid_citations'] == ['returns#9']
