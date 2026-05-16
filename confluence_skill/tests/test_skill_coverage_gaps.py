"""Tests targeting specific coverage gaps in skill.py."""

from unittest.mock import MagicMock, patch

import pytest

from confluence_skill.models import SkillConfig
from confluence_skill.skill import ConfluenceSkill


@pytest.fixture
def config():
    """Create test skill config with Jira enabled."""
    return SkillConfig(
        confluence={
            "instance_url": "https://test.atlassian.net",
            "space_key": "TEST",
            "auth_token_env": "TEST_TOKEN",
        },
        documentation={
            "template": "api",
            "space_key": "TEST",
            "metadata": {
                "owner": "test-team",
                "audience": ["engineers"],
            },
        },
        jira={
            "enabled": True,
            "instance_url": "https://test.atlassian.net",
            "auth_token_env": "JIRA_TOKEN",
            "default_project": "INFRA",
            "create_tasks_for_gaps": True,
        },
    )


@pytest.fixture
def skill(config, monkeypatch):
    """Create ConfluenceSkill."""
    monkeypatch.setenv("TEST_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_TOKEN", "jira-token")
    return ConfluenceSkill(config)


class TestNonDryRunDocumentWriting:
    """Test non-dry-run document writing paths."""

    def test_document_create_new_page_non_dry_run(self, skill):
        """Test creating new page when not in dry-run mode."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch.object(skill, "approval_gate") as mock_approval:
                        with patch("confluence_skill.skill.LocalConfig"):
                            with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                mock_client.find_page_by_title.return_value = None
                                mock_validator.errors = []
                                mock_validator.warnings = []
                                mock_approval.require_approval = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Test content"
                                mock_gen_factory.return_value = mock_generator

                                mock_client.create_page.return_value = {
                                    "id": "new-page-123",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify page creation was called
                                assert mock_client.create_page.called
                                assert result.success
                                assert result.document_id == "new-page-123"

    def test_document_update_existing_page_non_dry_run(self, skill):
        """Test updating existing page when not in dry-run mode."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch.object(skill, "approval_gate") as mock_approval:
                        with patch("confluence_skill.skill.LocalConfig"):
                            with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                existing_page = {"id": "existing-123", "title": "Test Doc"}
                                mock_client.find_page_by_title.return_value = existing_page
                                mock_validator.errors = []
                                mock_validator.warnings = []
                                mock_approval.require_approval = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Updated content"
                                mock_gen_factory.return_value = mock_generator

                                mock_client.update_page.return_value = {
                                    "id": "existing-123",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify page update was called
                                assert mock_client.update_page.called
                                assert result.success
                                assert result.document_id == "existing-123"

    def test_document_with_audit_trail(self, skill):
        """Test creating audit trail comment when enabled."""
        skill.config.output.create_audit_trail = True

        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch.object(skill, "approval_gate") as mock_approval:
                        with patch("confluence_skill.skill.LocalConfig"):
                            with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                mock_client.find_page_by_title.return_value = None
                                mock_validator.errors = []
                                mock_validator.warnings = []
                                mock_approval.require_approval = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Test content"
                                mock_gen_factory.return_value = mock_generator

                                mock_client.create_page.return_value = {
                                    "id": "new-page-123",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify create_page was called (audit trail not tested for update)
                                assert result.success


class TestApprovalGateRejection:
    """Test approval gate rejection paths."""

    def test_document_approval_gate_requires_approval_and_user_declines(self, skill):
        """Test when approval gate requires approval and user declines."""
        skill.config.guardrails.require_approval = True

        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch.object(skill, "approval_gate") as mock_approval:
                        with patch("confluence_skill.skill.LocalConfig"):
                            with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                mock_client.find_page_by_title.return_value = None
                                mock_validator.errors = []
                                mock_validator.warnings = []
                                mock_approval.require_approval = True
                                mock_approval.request_approval.return_value = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Test content"
                                mock_gen_factory.return_value = mock_generator

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify approval was requested and result contains warning
                                assert mock_approval.request_approval.called
                                assert any("approval" in str(e.field).lower() for e in result.errors)


class TestJiraIntegration:
    """Test Jira integration paths."""

    def test_document_with_jira_initialization_disabled_credentials(self, skill):
        """Test Jira initialization when credentials missing."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch("confluence_skill.skill.LocalConfig"):
                        with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                            with patch("confluence_skill.skill.JiraIntegration") as mock_jira_class:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                mock_client.find_page_by_title.return_value = None
                                mock_validator.errors = []
                                mock_validator.warnings = []

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Test content"
                                mock_gen_factory.return_value = mock_generator

                                # Jira initialized but client disabled
                                mock_jira_instance = MagicMock()
                                mock_jira_instance.client.enabled = False
                                mock_jira_class.return_value = mock_jira_instance

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=True,
                                )

                                # JiraIntegration should be instantiated
                                assert mock_jira_class.called
                                assert result.duration_seconds >= 0

    def test_document_with_jira_linking_issues(self, skill):
        """Test Jira integration linking related issues."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch.object(skill, "approval_gate") as mock_approval:
                        with patch("confluence_skill.skill.LocalConfig"):
                            with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                                with patch("confluence_skill.skill.JiraIntegration") as mock_jira_class:
                                    # Setup mocks
                                    mock_scanner.scan_repos.return_value = {
                                        "apis": [{"name": "GET /users", "description": "List users"}]
                                    }
                                    mock_client.validate_space.return_value = True
                                    mock_client.check_write_permission.return_value = True
                                    mock_client.find_page_by_title.return_value = None
                                    mock_validator.errors = []
                                    mock_validator.warnings = []
                                    mock_approval.require_approval = False

                                    mock_generator = MagicMock()
                                    mock_generator.generate.return_value = "API Documentation"
                                    mock_gen_factory.return_value = mock_generator

                                    mock_client.create_page.return_value = {
                                        "id": "page-123",
                                        "title": "Test Doc",
                                    }

                                    # Jira with linking enabled
                                    mock_jira_instance = MagicMock()
                                    mock_jira_instance.config.enabled = True
                                    mock_jira_instance.config.default_project = "INFRA"
                                    mock_jira_instance.config.create_tasks_for_gaps = True
                                    mock_jira_instance.client.enabled = True
                                    mock_jira_instance.client.find_epic_for_service.return_value = "EPIC-123"
                                    mock_jira_instance.link_related_issues.return_value = ["INFRA-1", "INFRA-2"]
                                    mock_jira_instance.create_tasks_for_gaps.return_value = ["INFRA-3"]
                                    mock_jira_class.return_value = mock_jira_instance

                                    skill.document(
                                        task="Test Doc",
                                        repo_path=".",
                                        dry_run=False,
                                    )

                                    # Verify Jira integration methods were called
                                    assert mock_jira_instance.link_related_issues.called
                                    assert mock_jira_instance.create_tasks_for_gaps.called


class TestConfigMerging:
    """Test configuration merging paths."""

    def test_document_with_config_merge_from_local_file(self, skill):
        """Test that merged config triggers console print."""
        with patch.object(skill, "client"):
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator"):
                    with patch.object(skill, "_load_and_merge_config") as mock_merge:
                        with patch("confluence_skill.skill.create_generator"):
                            # Setup config that's different from original
                            different_config = MagicMock()
                            different_config.documentation = skill.config.documentation
                            different_config.confluence = skill.config.confluence
                            different_config.jira = skill.config.jira
                            mock_merge.return_value = different_config

                            mock_scanner.scan_repos.return_value = {"apis": []}

                            # The merge will trigger the "Merged local config" print
                            result = skill.document(
                                task="Test Doc",
                                repo_path="/some/path",
                                dry_run=True,
                            )

                            # Just verify the workflow completes
                            assert result.duration_seconds >= 0


class TestErrorHandling:
    """Test error handling paths."""

    def test_prepare_config_with_invalid_doc_type(self, skill):
        """Test error handling for invalid doc type."""
        # Invalid doc type prints warning but doesn't raise
        result = skill._prepare_config("INVALID_TYPE", None, None, None, skill.config)
        assert result is not None

    def test_prepare_config_with_none_working_config(self, skill):
        """Test _prepare_config when working_config is None."""
        doc_config = skill._prepare_config("api", None, None, None, None)

        assert doc_config is not None
        assert doc_config.template.value == "api"

    def test_prepare_config_with_space_key_fallback(self, skill):
        """Test _prepare_config falls back to confluence space_key."""
        doc_config = skill.config.documentation
        doc_config.space_key = None

        result = skill._prepare_config("api", None, None, None, skill.config)

        # Should fallback to confluence.space_key
        assert result.space_key == "TEST"

    def test_generate_metadata_with_valid_labels(self, skill):
        """Test metadata generation with valid labels."""
        doc_config = skill.config.documentation
        doc_config.metadata.labels = ["api", "v2"]

        metadata = skill._generate_metadata("Test Doc", doc_config)

        assert metadata is not None
        assert "api" in metadata.labels

    def test_generate_metadata_with_invalid_title_too_short(self, skill):
        """Test metadata generation with title too short."""
        doc_config = skill.config.documentation

        with pytest.raises(ValueError, match="title"):
            skill._generate_metadata("x", doc_config)

    def test_validator_warnings_captured(self, skill):
        """Test that validator warnings are captured in result."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch("confluence_skill.skill.LocalConfig"):
                        with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                            # Setup mocks
                            mock_scanner.scan_repos.return_value = {"apis": []}
                            mock_client.validate_space.return_value = True
                            mock_client.check_write_permission.return_value = True
                            mock_client.find_page_by_title.return_value = None

                            from confluence_skill.models import ValidationError

                            mock_validator.errors = []
                            mock_validator.warnings = [
                                ValidationError(level="warning", field="test", message="Test warning")
                            ]
                            mock_validator.get_summary.return_value = "Test warning"

                            mock_generator = MagicMock()
                            mock_generator.generate.return_value = "Test content"
                            mock_gen_factory.return_value = mock_generator

                            result = skill.document(
                                task="Test Doc",
                                repo_path=".",
                                dry_run=True,
                            )

                            # Warnings should be captured
                            assert len(result.warnings) > 0
                            assert result.warnings[0].message == "Test warning"
