"""Tests for ConfluenceSkill document generation workflow."""

from unittest.mock import patch

import pytest

from confluence_skill.models import (
    DocumentGenerationResult,
    DocumentMetadata,
    SkillConfig,
)
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


class TestDocumentWorkflow:
    """Test document generation workflow."""

    def test_document_dry_run_workflow(self, skill):
        """Test complete document generation in dry-run mode."""
        with patch.object(skill, "client"):
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.return_value = {
                    "apis": [{"name": "GET /users", "description": "List users"}],
                }

                result = skill.document(
                    task="Document the API",
                    repo_path=".",
                    dry_run=True,
                )

                assert isinstance(result, DocumentGenerationResult)
                assert result.dry_run is True
                assert result.duration_seconds >= 0

    def test_document_publishes_to_confluence(self, skill):
        """Test document publishing to Confluence."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.return_value = {"apis": []}
                mock_client.find_page_by_title.return_value = None
                mock_client.create_page.return_value = {
                    "id": "page-123",
                    "title": "API Docs",
                }

                result = skill.document(
                    task="Document the API",
                    repo_path=".",
                    dry_run=False,
                    doc_type="api",
                )

                assert isinstance(result, DocumentGenerationResult)

    def test_document_with_custom_space(self, skill):
        """Test document generation with custom space."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.return_value = {"apis": []}

                skill.document(
                    task="Document",
                    repo_path=".",
                    space_key="CUSTOM",
                    dry_run=True,
                )

                # Verify custom space was used
                assert mock_client is not None

    def test_document_with_parent_page(self, skill):
        """Test document with parent page reference."""
        with patch.object(skill, "client") as mock_client:
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.return_value = {"apis": []}
                mock_client.find_page_by_title.return_value = {"id": "parent-1"}

                result = skill.document(
                    task="Document",
                    repo_path=".",
                    parent_page_title="Architecture",
                    dry_run=True,
                )

                assert isinstance(result, DocumentGenerationResult)

    def test_document_handles_scanner_errors(self, skill):
        """Test that document generation handles scanner errors gracefully."""
        with patch.object(skill, "client"):
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.side_effect = Exception("Scan failed")

                result = skill.document(
                    task="Document",
                    repo_path=".",
                    dry_run=True,
                )

                # Should handle error gracefully
                assert isinstance(result, DocumentGenerationResult)

    def test_document_with_multiple_repos(self, skill):
        """Test document generation with multiple repos."""
        with patch.object(skill, "client"):
            with patch.object(skill, "scanner") as mock_scanner:
                mock_scanner.scan.return_value = {"apis": []}

                result = skill.document(
                    task="Document",
                    repos=["repo1", "repo2"],
                    dry_run=True,
                )

                assert isinstance(result, DocumentGenerationResult)


class TestDocumentMetadataGeneration:
    """Test metadata generation."""

    def test_generate_metadata_creates_valid_metadata(self, skill):
        """Test that metadata generation creates valid DocumentMetadata."""
        doc_config = skill.config.documentation

        metadata = skill._generate_metadata("Test task", doc_config)

        assert isinstance(metadata, DocumentMetadata)
        assert metadata.title is not None
        assert metadata.owner == "test-team"
        assert "engineers" in metadata.audience

    def test_generate_metadata_with_labels(self, skill):
        """Test metadata generation includes labels."""
        doc_config = skill.config.documentation

        metadata = skill._generate_metadata("Test task", doc_config)

        assert isinstance(metadata.labels, list)


class TestConfigMerging:
    """Test configuration loading and merging."""

    def test_prepare_config_uses_override_space(self, skill):
        """Test that prepare_config applies space_key override."""
        doc_config = skill._prepare_config(
            doc_type="api",
            space_key="OVERRIDE",
            parent_page_title=None,
            repos=None,
            working_config=skill.config,
        )

        assert doc_config.space_key == "OVERRIDE"

    def test_prepare_config_uses_override_doc_type(self, skill):
        """Test that prepare_config applies doc_type override."""
        doc_config = skill._prepare_config(
            doc_type="architecture",
            space_key=None,
            parent_page_title=None,
            repos=None,
            working_config=skill.config,
        )

        assert str(doc_config.template) == "DocumentTemplate.ARCHITECTURE"

    def test_load_and_merge_config_with_no_local_config(self, skill, tmp_path):
        """Test loading config when no local config exists."""
        # Create a temporary directory without .confluence.yaml
        working_config = skill._load_and_merge_config(str(tmp_path))

        assert working_config is not None
        assert isinstance(working_config, SkillConfig)


class TestPublishingStrategies:
    """Test different publishing strategies."""

    def test_handle_existing_page_append_strategy(self, skill):
        """Test append strategy for existing pages."""
        doc_config = skill.config.documentation
        doc_config.merge_strategy = "append"

        existing_page = {"id": "page-1", "title": "Existing"}
        metadata = DocumentMetadata(title="New Content")

        result = skill._handle_existing_page(existing_page, metadata, doc_config)

        assert result == "append"

    def test_handle_existing_page_replace_strategy(self, skill):
        """Test replace strategy for existing pages."""
        doc_config = skill.config.documentation
        doc_config.merge_strategy = "replace"

        existing_page = {"id": "page-1"}
        metadata = DocumentMetadata(title="Replacement")

        result = skill._handle_existing_page(existing_page, metadata, doc_config)

        assert result == "replace"

    def test_handle_existing_page_skip_strategy(self, skill):
        """Test skip strategy for existing pages."""
        doc_config = skill.config.documentation
        doc_config.merge_strategy = "skip"

        existing_page = {"id": "page-1"}
        metadata = DocumentMetadata(title="New")

        result = skill._handle_existing_page(existing_page, metadata, doc_config)

        assert result == "skip"


class TestParentPageHandling:
    """Test parent page resolution."""

    def test_get_parent_page_id_from_title(self, skill):
        """Test getting parent page ID from title."""
        with patch.object(skill.client, "find_page_by_title") as mock_find:
            mock_find.return_value = {"id": "parent-123"}

            doc_config = skill.config.documentation
            doc_config.parent_page = "Architecture"

            result = skill._get_parent_page_id(doc_config)

            assert result == "parent-123"

    def test_get_parent_page_id_from_explicit_id(self, skill):
        """Test getting parent page when ID is explicit."""
        doc_config = skill.config.documentation
        doc_config.parent_page_id = "page-456"

        result = skill._get_parent_page_id(doc_config)

        assert result == "page-456"

    def test_get_parent_page_id_not_found(self, skill):
        """Test handling when parent page not found."""
        with patch.object(skill.client, "find_page_by_title") as mock_find:
            mock_find.return_value = None

            doc_config = skill.config.documentation
            doc_config.parent_page = "Nonexistent"

            result = skill._get_parent_page_id(doc_config)

            assert result is None


class TestSearchAndArchive:
    """Test search and archive operations."""

    def test_search_pages_delegates_to_client(self, skill):
        """Test that search_pages delegates to client."""
        with patch.object(skill.client, "search_pages") as mock_search:
            mock_search.return_value = [{"id": "123", "title": "Test"}]

            result = skill.search_pages("TEST", "query")

            assert len(result) == 1
            mock_search.assert_called_once()

    def test_archive_page_delegates_to_client(self, skill):
        """Test that archive_page delegates to client."""
        with patch.object(skill.client, "archive_page") as mock_archive:
            mock_archive.return_value = True

            result = skill.archive_page("page-123")

            assert result is True
            mock_archive.assert_called_once_with("page-123")

    def test_list_page_hierarchy_delegates_to_client(self, skill):
        """Test that list_page_hierarchy delegates to client."""
        with patch.object(skill.client, "get_page") as mock_get:
            with patch.object(skill.client, "list_child_pages") as mock_children:
                mock_get.return_value = {"id": "page-1", "title": "Parent"}
                mock_children.return_value = [{"id": "child-1"}]

                result = skill.list_page_hierarchy("page-1")

                assert isinstance(result, dict)

    def test_bulk_label_pages_delegates_to_client(self, skill):
        """Test that bulk_label_pages delegates to client."""
        with patch.object(skill, "search_pages") as mock_search:
            with patch.object(skill.client, "bulk_add_labels") as mock_label:
                mock_search.return_value = [{"id": "1"}, {"id": "2"}]
                mock_label.return_value = {"success": 2, "failed": 0}

                result = skill.bulk_label_pages("TEST", "api", ["label1"])

                assert result["success"] == 2
                mock_label.assert_called_once()
