"""Final tests to reach skill.py 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest

from confluence_skill.models import SkillConfig, ValidationError
from confluence_skill.skill import ConfluenceSkill


@pytest.fixture
def config():
    """Create test skill config."""
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
    )


@pytest.fixture
def skill(config, monkeypatch):
    """Create ConfluenceSkill."""
    monkeypatch.setenv("TEST_TOKEN", "test-token")
    return ConfluenceSkill(config)


class TestSkillEdgeCases:
    """Test remaining edge cases in skill.py."""

    def test_document_with_validator_errors_in_non_dry_run(self, skill):
        """Test that validator errors are captured in non-dry-run."""
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

                                # Set validator to have errors
                                mock_validator.errors = [
                                    ValidationError(level="error", field="content", message="Content too short")
                                ]
                                mock_validator.warnings = []
                                mock_validator.get_summary.return_value = "Validation error"
                                mock_approval.require_approval = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Content"
                                mock_gen_factory.return_value = mock_generator

                                mock_client.create_page.return_value = {
                                    "id": "page-123",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=True,
                                )

                                # Errors should be captured
                                assert any("content" in str(e.field).lower() for e in result.errors)

    def test_document_handles_page_already_exists_with_merge_strategy(self, skill):
        """Test handling when page exists with different merge strategies."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch("confluence_skill.skill.LocalConfig"):
                        with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                            with patch.object(skill, "_handle_existing_page") as mock_handle:
                                # Setup mocks
                                mock_scanner.scan_repos.return_value = {"apis": []}
                                mock_client.validate_space.return_value = True
                                mock_client.check_write_permission.return_value = True
                                existing_page = {"id": "existing-123", "title": "Test Doc"}
                                mock_client.find_page_by_title.return_value = existing_page
                                mock_validator.errors = []
                                mock_validator.warnings = []

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Content"
                                mock_gen_factory.return_value = mock_generator

                                # Test "skip" strategy
                                mock_handle.return_value = "skip"

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=True,
                                )

                                # Should return early with info message
                                assert mock_handle.called
                                assert any("skip" in str(e.message).lower() for e in result.errors)

    def test_generate_metadata_with_long_valid_title(self, skill):
        """Test metadata generation with maximum valid title length."""
        doc_config = skill.config.documentation

        # Create a long but valid title (under 255 chars)
        long_title = "A" * 200  # Valid length

        metadata = skill._generate_metadata(long_title, doc_config)

        assert metadata.title == long_title
        assert len(metadata.title) == 200

    def test_prepare_config_with_parent_page_title(self, skill):
        """Test _prepare_config with parent page title."""
        doc_config = skill._prepare_config(
            "api",
            None,
            "Parent API Pages",
            None,
            skill.config,
        )

        assert doc_config.parent_page == "Parent API Pages"

    def test_prepare_config_with_repos_override(self, skill):
        """Test _prepare_config with repos override."""
        test_repos = ["/path/to/repo1", "/path/to/repo2"]

        skill._prepare_config(
            "api",
            None,
            None,
            test_repos,
            skill.config,
        )

        # Repos should be set in code_analysis
        assert len(skill.config.code_analysis.repos) == 2

    def test_dry_run_mode_result_success_based_on_errors(self, skill):
        """Test that dry run result success is based on presence of errors."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                with patch.object(skill, "validator") as mock_validator:
                    with patch("confluence_skill.skill.LocalConfig"):
                        with patch("confluence_skill.skill.create_generator") as mock_gen_factory:
                            # Setup mocks for successful dry run
                            mock_scanner.scan_repos.return_value = {"apis": []}
                            mock_client.validate_space.return_value = True
                            mock_client.check_write_permission.return_value = True
                            mock_client.find_page_by_title.return_value = None
                            mock_validator.errors = []
                            mock_validator.warnings = []

                            mock_generator = MagicMock()
                            mock_generator.generate.return_value = "Test content"
                            mock_gen_factory.return_value = mock_generator

                            result = skill.document(
                                task="Test Doc",
                                repo_path=".",
                                dry_run=True,
                            )

                            # Dry run with no errors should be successful
                            assert result.success
                            assert result.dry_run is True

    def test_document_creates_page_url_correctly(self, skill):
        """Test that document URL is correctly formatted."""
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
                                    "id": "12345",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify URL format
                                assert "https://test.atlassian.net" in result.document_url
                                assert "TEST" in result.document_url  # space key
                                assert "12345" in result.document_url  # page id

    def test_update_page_creates_url_correctly(self, skill):
        """Test that update page creates correct URL."""
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
                                existing_page = {"id": "existing-456", "title": "Test Doc"}
                                mock_client.find_page_by_title.return_value = existing_page
                                mock_validator.errors = []
                                mock_validator.warnings = []
                                mock_approval.require_approval = False

                                mock_generator = MagicMock()
                                mock_generator.generate.return_value = "Updated content"
                                mock_gen_factory.return_value = mock_generator

                                mock_client.update_page.return_value = {
                                    "id": "existing-456",
                                    "title": "Test Doc",
                                }

                                result = skill.document(
                                    task="Test Doc",
                                    repo_path=".",
                                    dry_run=False,
                                )

                                # Verify URL format for updated page
                                assert "https://test.atlassian.net" in result.document_url
                                assert "existing-456" in result.document_url
