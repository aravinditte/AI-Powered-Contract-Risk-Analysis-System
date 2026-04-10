from app.ai.pipeline import run_ai_pipeline


def test_ai_pipeline_basic_flow():
    contract_text = """
    The payment shall be made within 30 days.
    Either party may terminate this agreement.
    """

    results = run_ai_pipeline(contract_text)

    assert isinstance(results, list)
    assert len(results) > 0

    for result in results:
        assert "risk_level" in result
        assert "explanation" in result
        assert "confidence" in result
