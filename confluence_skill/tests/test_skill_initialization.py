"""Tests for ConfluenceSkill initialization and edge cases."""

from unittest.mock import MagicMock, patch

import pytest

from confluence_skill.models import SkillConfig
from confluence_skill.skill import ConfluenceSkill


class TestSkillInitializationWithConfigErrors:
    """Test skill initialization with configuration errors."""

    def test_init_with_config_validation_errors(self):
        """Test that init raises ValueError when config has validation errors."""
        with patch.object(SkillConfig, "validate_required_fields") as mock_validate:
            mock_validate.return_value = ["Missing confluence.instance_url", "Missing documentation.metadata.owner"]

            config = MagicMock(spec=SkillConfig)
            config.validate_required_fields.return_value = ["Missing confluence.instance_url"]

            with pytest.raises(ValueError, match="Configuration errors"):
                ConfluenceSkill(config)

    def test_init_with_valid_config(self):
        """Test successful initialization with valid config."""
        with patch("confluence_skill.skill.ConfluenceClient"):
            with patch("confluence_skill.skill.CodeScanner"):
                with patch("confluence_skill.skill.GuardailValidator"):
                    with patch("confluence_skill.skill.ApprovalGate"):
                        config = MagicMock(spec=SkillConfig)
                        config.validate_required_fields.return_value = []
                        config.confluence = MagicMock()
                        config.code_analysis = MagicMock()
                        config.guardrails = MagicMock(require_approval=False)

                        skill = ConfluenceSkill(config)

                        assert skill.config == config
                        assert skill.client is not None
                        assert skill.scanner is not None
                        assert skill.validator is not None


class TestLoadAndMergeConfig:
    """Test loading and merging local configuration."""

    def test_load_and_merge_config_with_local_config_exists(self):
        """Test loading and merging when local config exists."""
        config = MagicMock(spec=SkillConfig)
        config.validate_required_fields.return_value = []
        config.confluence = MagicMock()
        config.code_analysis = MagicMock()
        config.guardrails = MagicMock()

        with patch("confluence_skill.skill.ConfluenceClient"):
            with patch("confluence_skill.skill.CodeScanner"):
                with patch("confluence_skill.skill.GuardailValidator"):
                    with patch("confluence_skill.skill.ApprovalGate"):
                        with patch("confluence_skill.skill.LocalConfig.from_yaml") as mock_from_yaml:
                            with patch("confluence_skill.skill.Path.is_absolute", return_value=True):
                                with patch("confluence_skill.skill.Path.exists", return_value=True):
                                    local_config = MagicMock()
                                    mock_from_yaml.return_value = local_config
                                    config.merge.return_value = config  # Merged config

                                    skill = ConfluenceSkill(config)
                                    result = skill._load_and_merge_config("/some/path")

                                    assert result is not None
                                    config.merge.assert_called_once()

    def test_load_and_merge_config_no_local_config(self):
        """Test loading when no local config exists."""
        config = MagicMock(spec=SkillConfig)
        config.validate_required_fields.return_value = []
        config.confluence = MagicMock()
        config.code_analysis = MagicMock()
        config.guardrails = MagicMock()

        with patch("confluence_skill.skill.ConfluenceClient"):
            with patch("confluence_skill.skill.CodeScanner"):
                with patch("confluence_skill.skill.GuardailValidator"):
                    with patch("confluence_skill.skill.ApprovalGate"):
                        with patch("confluence_skill.skill.Path.is_absolute", return_value=True):
                            with patch("confluence_skill.skill.Path.exists", return_value=False):
                                skill = ConfluenceSkill(config)
                                result = skill._load_and_merge_config("/some/path")

                                # Should return original config
                                assert result == config

    def test_load_and_merge_config_with_exception(self):
        """Test loading when local config loading fails."""
        config = MagicMock(spec=SkillConfig)
        config.validate_required_fields.return_value = []
        config.confluence = MagicMock()
        config.code_analysis = MagicMock()
        config.guardrails = MagicMock()

        with patch("confluence_skill.skill.ConfluenceClient"):
            with patch("confluence_skill.skill.CodeScanner"):
                with patch("confluence_skill.skill.GuardailValidator"):
                    with patch("confluence_skill.skill.ApprovalGate"):
                        with patch("confluence_skill.skill.LocalConfig.from_yaml") as mock_from_yaml:
                            with patch("confluence_skill.skill.Path.is_absolute", return_value=True):
                                with patch("confluence_skill.skill.Path.exists", return_value=True):
                                    mock_from_yaml.side_effect = Exception("Invalid YAML")

                                    skill = ConfluenceSkill(config)
                                    result = skill._load_and_merge_config("/some/path")

                                    # Should return original config on exception
                                    assert result == config
