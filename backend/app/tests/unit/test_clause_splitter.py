from app.ai.clause_extraction.splitter import split_into_clauses


def test_split_into_clauses_basic():
    text = """
    This Agreement shall commence on the Effective Date.

    Either party may terminate this Agreement with 30 days notice.

    Confidential information must not be disclosed.
    """

    clauses = split_into_clauses(text)

    assert isinstance(clauses, list)
    assert len(clauses) == 3
    assert all(len(c) > 30 for c in clauses)
