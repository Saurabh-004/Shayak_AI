from app.schemas import Analysis
from app.services.ai_service import safe_analysis


def test_model_output_cannot_recommend_sensitive_action():
    result = safe_analysis(Analysis(
        risk_level="HIGH", category="TEST", summary="Test", warning_signs=[],
        do_not=[], recommended_actions=["Send money now", "Call the official bank number"],
    ))
    assert result.recommended_actions == ["Call the official bank number"]


def test_model_output_has_a_safe_fallback_action():
    result = safe_analysis(Analysis(
        risk_level="HIGH", category="TEST", summary="Test", warning_signs=[],
        do_not=[], recommended_actions=["Share OTP"],
    ))
    assert "verify" in result.recommended_actions[0].lower()
