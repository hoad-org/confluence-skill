"""Extended tests for guardrails module covering all validation paths."""

from unittest.mock import patch

import pytest

from confluence_skill.guardrails import ApprovalGate, GuardailValidator
from confluence_skill.models import DocumentMetadata, GuardrailsConfig


@pytest.fixture
def guardrails_config():
    """Create test guardrails config."""
    return GuardrailsConfig(
        enabled=True,
        validate_metadata=True,
        validate_links=True,
        require_approval=True,
        required_metadata_fields=["owner", "audience"],
        deprecated_terms=["old-service", "legacy"],
    )


@pytest.fixture
def disabled_config():
    """Create disabled guardrails config."""
    return GuardrailsConfig(enabled=False)


@pytest.fixture
def metadata():
    """Create test metadata."""
    return DocumentMetadata(
        title="Test Document",
        owner="test-team",
        audience=["engineers"],
    )


@pytest.fixture
def validator(guardrails_config):
    """Create GuardailValidator."""
    return GuardailValidator(guardrails_config)


class TestGuardailValidatorMetadata:
    """Test metadata validation."""

    def test_validate_metadata_disabled_config(self, metadata):
        """Test metadata validation with disabled config."""
        config = GuardrailsConfig(enabled=False)
        validator = GuardailValidator(config)

        result = validator.validate_metadata(metadata)

        assert result is True
        assert len(validator.errors) == 0

    def test_validate_metadata_validation_disabled(self, metadata):
        """Test metadata validation when validate_metadata=False."""
        config = GuardrailsConfig(enabled=True, validate_metadata=False)
        validator = GuardailValidator(config)

        result = validator.validate_metadata(metadata)

        assert result is True

    def test_validate_metadata_missing_required_field(self, guardrails_config):
        """Test validation with missing required field."""
        metadata = DocumentMetadata(
            title="Test",
            owner="team",
            # Missing audience
        )
        validator = GuardailValidator(guardrails_config)

        result = validator.validate_metadata(metadata)

        assert result is False
        assert len(validator.errors) > 0
        assert any("audience" in str(e.field).lower() for e in validator.errors)

    def test_validate_metadata_with_deprecated_term(self, validator):
        """Test validation detects deprecated terms."""
        metadata = DocumentMetadata(
            title="Legacy old-service Documentation",
            owner="team",
            audience=["engineers"],
        )

        result = validator.validate_metadata(metadata)

        assert result is True  # Not an error, just warning
        assert len(validator.warnings) > 0
        assert any("legacy" in str(w.message).lower() for w in validator.warnings)

    def test_validate_metadata_without_deprecated_terms(self):
        """Test metadata validation without deprecated terms configured."""
        config = GuardrailsConfig(enabled=True, validate_metadata=True)
        validator = GuardailValidator(config)
        metadata = DocumentMetadata(
            title="New Service Documentation",
            owner="team",
            audience=["engineers"],
        )

        result = validator.validate_metadata(metadata)

        assert result is True
        assert len(validator.errors) == 0


class TestGuardailValidatorContent:
    """Test content validation."""

    def test_validate_content_disabled_config(self, metadata):
        """Test content validation with disabled config."""
        config = GuardrailsConfig(enabled=False)
        validator = GuardailValidator(config)

        result = validator.validate_content("<p>Test</p>", metadata)

        assert result is True

    def test_validate_content_exceeds_size_limit(self, validator, metadata):
        """Test warning when content exceeds size limit."""
        large_content = "<p>" + "x" * (2000 * 1024) + "</p>"

        result = validator.validate_content(large_content, metadata)

        assert result is True  # Not an error, just warning
        assert len(validator.warnings) > 0
        assert any("size" in str(w.message).lower() for w in validator.warnings)

    def test_validate_content_within_size_limit(self, validator, metadata):
        """Test validation passes when content within size limit."""
        content = "<p>Small content</p>"

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.errors) == 0

    def test_validate_content_with_link_validation_disabled(self, metadata):
        """Test content validation without link validation."""
        config = GuardrailsConfig(
            enabled=True,
            validate_links=False,
            required_metadata_fields=[],
        )
        validator = GuardailValidator(config)
        content = '<p><a href="#invalid">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.errors) == 0

    def test_validate_content_with_deprecated_term(self, validator, metadata):
        """Test validation detects deprecated terms in content."""
        content = "<p>This describes the old-service legacy system</p>"

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.warnings) > 0


class TestLinkValidation:
    """Test link validation functionality."""

    def test_validate_links_broken_anchor(self, validator, metadata):
        """Test validation detects broken anchor links."""
        content = '<h1>Title</h1><p><a href="#missing">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is False
        assert len(validator.errors) > 0
        assert any("anchor" in str(e.message).lower() for e in validator.errors)

    def test_validate_links_valid_anchor(self, validator, metadata):
        """Test validation accepts valid anchor links."""
        content = '<h1 id="section">Title</h1><p><a href="#section">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.errors) == 0

    def test_validate_links_relative_path_invalid(self, validator, metadata):
        """Test warning for invalid relative paths."""
        content = '<p><a href="/invalid">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.warnings) > 0
        assert any("relative" in str(w.message).lower() for w in validator.warnings)

    def test_validate_links_relative_path_valid(self, validator, metadata):
        """Test validation accepts valid-looking relative paths."""
        content = '<p><a href="/confluence/spaces/page">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is True

    def test_validate_links_external_url(self, validator, metadata):
        """Test validation allows external URLs."""
        content = '<p><a href="https://example.com">Link</a></p>'

        result = validator.validate_content(content, metadata)

        assert result is True
        assert len(validator.errors) == 0


class TestAnchorValidation:
    """Test anchor validation helper."""

    def test_anchor_exists_with_id_attribute(self, validator):
        """Test anchor detection with id attribute."""
        content = '<div id="my-section">Content</div>'

        exists = validator._anchor_exists(content, "my-section")

        assert exists is True

    def test_anchor_exists_with_link_tag(self, validator):
        """Test anchor detection with link tag."""
        content = '<a id="target">Target</a>'

        exists = validator._anchor_exists(content, "target")

        assert exists is True

    def test_anchor_not_exists(self, validator):
        """Test anchor detection when anchor missing."""
        content = '<div id="other">Content</div>'

        exists = validator._anchor_exists(content, "missing")

        assert exists is False

    def test_anchor_with_special_chars(self, validator):
        """Test anchor detection with special characters."""
        content = '<div id="my-section-v2.0">Content</div>'

        exists = validator._anchor_exists(content, "my-section-v2.0")

        assert exists is True


class TestPathValidation:
    """Test path validation helper."""

    def test_valid_path(self, validator):
        """Test validation of valid path."""
        path = "/confluence/spaces/SPACE/pages"

        is_valid = validator._is_valid_path(path)

        assert is_valid is True

    def test_invalid_path_too_few_segments(self, validator):
        """Test validation rejects path with too few segments."""
        path = "/invalid"

        is_valid = validator._is_valid_path(path)

        assert is_valid is False

    def test_invalid_path_with_parent_ref(self, validator):
        """Test validation rejects path with parent directory reference."""
        path = "/path/../escape"

        is_valid = validator._is_valid_path(path)

        assert is_valid is False

    def test_valid_path_deep_nesting(self, validator):
        """Test validation of deeply nested path."""
        path = "/a/b/c/d/e/f"

        is_valid = validator._is_valid_path(path)

        assert is_valid is True


class TestValidationSummary:
    """Test validation summary generation."""

    def test_summary_no_errors_or_warnings(self, validator, metadata):
        """Test summary when validation passes."""
        validator.validate_metadata(metadata)

        summary = validator.get_summary()

        assert "✅" in summary
        assert "All validations passed" in summary

    def test_summary_with_errors(self, validator):
        """Test summary generation with errors."""
        metadata = DocumentMetadata(
            title="Test",
            # Missing required fields
        )
        validator.validate_metadata(metadata)

        summary = validator.get_summary()

        assert "❌" in summary
        assert "Errors" in summary
        assert "owner" in summary.lower()

    def test_summary_with_warnings(self, validator):
        """Test summary generation with warnings."""
        metadata = DocumentMetadata(
            title="Legacy old-service Documentation",
            owner="team",
            audience=["engineers"],
        )
        validator.validate_metadata(metadata)

        summary = validator.get_summary()

        assert "⚠️" in summary
        assert "Warnings" in summary

    def test_summary_includes_suggestions(self, validator):
        """Test that summary includes suggestions for errors."""
        metadata = DocumentMetadata(title="Test")
        validator.validate_metadata(metadata)

        summary = validator.get_summary()

        assert "💡" in summary


class TestApprovalGateBasic:
    """Test basic approval gate functionality."""

    def test_approval_not_required(self):
        """Test approval gate when approval not required."""
        gate = ApprovalGate(require_approval=False)

        result = gate.request_approval("doc-1", "create", "Create new doc")

        assert result is True

    def test_approval_required_non_interactive(self):
        """Test approval request in non-interactive mode."""
        gate = ApprovalGate(require_approval=True, interactive=False)

        result = gate.request_approval("doc-1", "create", "Create new doc")

        assert result is False

    def test_approval_cached(self):
        """Test that approval is cached."""
        gate = ApprovalGate(require_approval=True, interactive=False)

        gate._approved.add("doc-1")
        result = gate.request_approval("doc-1", "create", "Create new doc")

        assert result is True

    def test_approval_different_docs(self):
        """Test approval is per-document."""
        gate = ApprovalGate(require_approval=True, interactive=False)

        gate._approved.add("doc-1")
        result = gate.request_approval("doc-2", "create", "Create new doc")

        assert result is False


class TestApprovalGateInteractive:
    """Test interactive approval gate."""

    def test_approval_user_yes(self):
        """Test approval when user says yes."""
        gate = ApprovalGate(require_approval=True, interactive=True)

        with patch.object(gate.console, "input", return_value="y"):
            result = gate.request_approval("doc-1", "create", "Create new doc")

            assert result is True
            assert "doc-1" in gate._approved

    def test_approval_user_no(self):
        """Test approval when user says no."""
        gate = ApprovalGate(require_approval=True, interactive=True)

        with patch.object(gate.console, "input", return_value="n"):
            result = gate.request_approval("doc-1", "create", "Create new doc")

            assert result is False
            assert "doc-1" not in gate._approved

    def test_approval_user_empty_response(self):
        """Test approval with empty response (default no)."""
        gate = ApprovalGate(require_approval=True, interactive=True)

        with patch.object(gate.console, "input", return_value=""):
            result = gate.request_approval("doc-1", "create", "Create new doc")

            assert result is False

    def test_approval_user_uppercase_yes(self):
        """Test approval with uppercase Y response (converted to lowercase)."""
        gate = ApprovalGate(require_approval=True, interactive=True)

        with patch.object(gate.console, "input", return_value="Y"):
            result = gate.request_approval("doc-1", "create", "Create new doc")

            assert result is True  # Uppercase Y is converted to lowercase and accepted

    def test_approval_prints_summary(self):
        """Test that approval prints action summary."""
        gate = ApprovalGate(require_approval=True, interactive=True)

        with patch.object(gate.console, "input", return_value="n"):
            with patch.object(gate.console, "print") as mock_print:
                gate.request_approval("doc-1", "create", "Create new document")

                # Should print the action summary
                mock_print.assert_called()


class TestMergeStrategy:
    """Test merge strategy request."""

    def test_merge_strategy_non_interactive(self):
        """Test merge strategy in non-interactive mode."""
        gate = ApprovalGate(interactive=False)

        strategy = gate.request_merge_strategy("Old Document")

        assert strategy is None

    def test_merge_strategy_append(self):
        """Test user choosing append strategy."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value="1"):
            strategy = gate.request_merge_strategy("Old Document")

            assert strategy == "append"

    def test_merge_strategy_replace(self):
        """Test user choosing replace strategy."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value="2"):
            strategy = gate.request_merge_strategy("Old Document")

            assert strategy == "replace"

    def test_merge_strategy_skip(self):
        """Test user choosing skip strategy."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value="3"):
            strategy = gate.request_merge_strategy("Old Document")

            assert strategy == "skip"

    def test_merge_strategy_invalid_choice(self):
        """Test invalid merge strategy choice."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value="99"):
            strategy = gate.request_merge_strategy("Old Document")

            assert strategy is None

    def test_merge_strategy_empty_choice(self):
        """Test empty merge strategy choice."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value=""):
            strategy = gate.request_merge_strategy("Old Document")

            assert strategy is None

    def test_merge_strategy_prints_options(self):
        """Test that merge strategy prints options."""
        gate = ApprovalGate(interactive=True)

        with patch.object(gate.console, "input", return_value="1"):
            with patch.object(gate.console, "print") as mock_print:
                gate.request_merge_strategy("Old Document")

                # Should print options
                mock_print.assert_called()
                call_texts = [str(call) for call in mock_print.call_args_list]
                # Should mention append, replace, skip
                assert any("append" in str(call) for call in call_texts)
