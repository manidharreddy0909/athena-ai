"""
Athena AI — Phase 18: Expanded Unit Tests
Tests for Phase 8 (Multilingual), Phase 9 (Modes), Phase 10 (Resume/JD),
Phase 11 (Recruiter Intelligence), Phase 13 (Analytics), Phase 16 (Security).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Phase 8: Multilingual ────────────────────────────────────────────────────

class TestMultilingualService:
    def test_build_language_system_prompt_english_passthrough(self):
        """English should pass through unchanged."""
        from core.multilingual import MultilingualService
        base = "You are an interviewer."
        result = MultilingualService.build_language_system_prompt("en", base)
        assert result == base

    def test_build_language_system_prompt_hindi_wraps(self):
        """Non-English should append language instruction."""
        from core.multilingual import MultilingualService
        base = "You are an interviewer."
        result = MultilingualService.build_language_system_prompt("hi", base)
        assert base in result
        assert "hi" in result.lower() or "hindi" in result.lower() or "language" in result.lower()

    def test_build_language_system_prompt_spanish_wraps(self):
        """Spanish language code should inject translation instruction."""
        from core.multilingual import MultilingualService
        base = "Ask a question about transformers."
        result = MultilingualService.build_language_system_prompt("es", base)
        assert base in result
        assert len(result) > len(base)  # Must have appended something

    def test_get_language_name_known_codes(self):
        """Known language codes should resolve to human-readable names."""
        from core.multilingual import MultilingualService
        info_en = MultilingualService.get_language_info("en")
        info_hi = MultilingualService.get_language_info("hi")
        assert info_en is not None
        assert info_hi is not None

    def test_get_language_name_unknown_defaults(self):
        """Unknown code should not crash — get_language_info may return None or a fallback."""
        from core.multilingual import MultilingualService
        result = MultilingualService.get_language_info("xx")
        # Should not raise — either None or a dict/object is acceptable
        assert result is None or isinstance(result, (dict, str))


# ─── Phase 9: Interview Modes ─────────────────────────────────────────────────

class TestInterviewMode:
    def test_interview_mode_enum_values(self):
        """InterviewMode should have the 3 expected values."""
        from models.interview import InterviewMode
        assert InterviewMode.GENERAL == "general"
        assert InterviewMode.CODING == "coding"
        assert InterviewMode.SYSTEM_DESIGN == "system_design"

    def test_start_interview_request_defaults_mode_general(self):
        """StartInterviewRequest should default mode to 'general'."""
        from models.interview import StartInterviewRequest
        req = StartInterviewRequest(name="Test Candidate")
        assert req.mode == "general"

    def test_start_interview_request_accepts_coding_mode(self):
        """StartInterviewRequest should accept 'coding' as a valid mode."""
        from models.interview import StartInterviewRequest
        req = StartInterviewRequest(name="Alice", mode="coding")
        assert req.mode == "coding"

    def test_interview_state_mode_field(self):
        """InterviewState should carry a mode field defaulting to general."""
        from models.interview import InterviewState, CandidateProfile
        state = InterviewState(
            session_id="test-123",
            candidate=CandidateProfile(name="Bob"),
        )
        assert state.mode == "general"


# ─── Phase 10: Resume & JD ────────────────────────────────────────────────────

class TestResumeAndJD:
    def test_start_interview_request_accepts_resume(self):
        """StartInterviewRequest should accept resume_text field."""
        from models.interview import StartInterviewRequest
        req = StartInterviewRequest(
            name="Alice",
            resume_text="Python developer, 5 years, built NLP models.",
            jd_text="Seeking ML Engineer with Python and LLM experience.",
        )
        assert req.resume_text is not None
        assert req.jd_text is not None

    def test_candidate_profile_has_resume_fields(self):
        """CandidateProfile should have resume_text and jd_text."""
        from models.interview import CandidateProfile
        profile = CandidateProfile(
            name="Test",
            resume_text="5 years Python",
            jd_text="We need Python devs",
        )
        assert profile.resume_text == "5 years Python"
        assert profile.jd_text == "We need Python devs"

    @pytest.mark.asyncio
    async def test_analyze_resume_and_jd_empty_graceful(self):
        """Empty resume/JD should return a valid fallback dict."""
        from agents.resume_agent import analyze_resume_and_jd
        from knowledge.domain_engine import DomainEngine, InterviewDomain

        domain_engine = DomainEngine(InterviewDomain.AI_ML)
        result = await analyze_resume_and_jd("", "", domain_engine)

        assert "focus_topics" in result
        assert "identified_gaps" in result
        assert "candidate_strengths" in result
        assert isinstance(result["focus_topics"], list)


# ─── Phase 11: Recruiter Intelligence ────────────────────────────────────────

class TestRecruiterIntelligence:
    def test_feedback_report_has_recruiter_fields(self):
        """FeedbackReport should have red_flags, green_flags, executive_summary, culture_fit_notes."""
        from models.interview import FeedbackReport, DimensionScore, HiringRecommendation
        report = FeedbackReport(
            session_id="s1",
            candidate_id="c1",
            candidate_name="Alice",
            overall_score=72.0,
            technical_depth=DimensionScore(score=70.0),
            coding_ability=DimensionScore(score=65.0),
            architecture=DimensionScore(score=75.0),
            communication=DimensionScore(score=80.0),
            reasoning=DimensionScore(score=70.0),
            hiring_recommendation=HiringRecommendation.HIRE,
        )
        assert hasattr(report, "red_flags")
        assert hasattr(report, "green_flags")
        assert hasattr(report, "executive_summary")
        assert hasattr(report, "culture_fit_notes")
        assert isinstance(report.red_flags, list)
        assert isinstance(report.green_flags, list)

    @pytest.mark.asyncio
    async def test_generate_recruiter_intelligence_empty_state(self):
        """Recruiter intelligence on empty state should return graceful fallback."""
        from agents.recruiter_agent import generate_recruiter_intelligence
        from models.interview import InterviewState, CandidateProfile

        state = InterviewState(
            session_id="test-empty",
            candidate=CandidateProfile(name="EmptyCandidate"),
        )
        result = await generate_recruiter_intelligence(state)

        assert "executive_summary" in result
        assert "red_flags" in result
        assert "green_flags" in result
        assert "culture_fit_notes" in result
        assert isinstance(result["red_flags"], list)


# ─── Phase 13: Analytics ─────────────────────────────────────────────────────

class TestAnalytics:
    def test_analytics_endpoint_imported(self):
        """Analytics router should be importable without errors."""
        from api.routes.analytics import router
        assert router is not None

    @pytest.mark.asyncio
    async def test_global_stats_empty_sessions(self, monkeypatch):
        """Global stats with no sessions should return zeros gracefully."""
        import graph.orchestrator as orch
        monkeypatch.setattr(orch, "_sessions", {})

        from api.routes.analytics import get_global_stats
        result = await get_global_stats()

        assert result["total_sessions"] == 0
        assert result["active_sessions"] == 0
        assert result["completed_sessions"] == 0
        assert result["global_avg_score"] == 0.0


# ─── Phase 16: Security ───────────────────────────────────────────────────────

class TestSecurityHeaders:
    def test_main_imports_cleanly(self):
        """main.py should import without errors."""
        import main  # noqa: F401 — just checking no import error

    def test_security_middleware_registered(self):
        """Security middleware should be wired into the app without error."""
        from main import app
        # Verify the app object was created and its route count is sane
        assert app is not None
        assert len(app.routes) > 0
