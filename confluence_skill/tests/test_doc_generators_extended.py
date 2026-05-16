"""Extended tests for document generators covering all templates."""

import pytest

from confluence_skill.doc_generators import (
    ADRDocGenerator,
    APIDocGenerator,
    ArchitectureDocGenerator,
    CustomDocGenerator,
    FeatureDocGenerator,
    InfrastructureDocGenerator,
    RunbookDocGenerator,
    TroubleshootingDocGenerator,
    create_generator,
)
from confluence_skill.models import DocumentMetadata, DocumentTemplate


@pytest.fixture
def basic_metadata():
    """Create basic document metadata."""
    return DocumentMetadata(
        title="Test Document",
        owner="test-team",
        audience=["engineers"],
        status="draft",
        version="1.0",
    )


@pytest.fixture
def minimal_metadata():
    """Create minimal document metadata."""
    return DocumentMetadata(
        title="Minimal Document",
    )


@pytest.fixture
def full_metadata():
    """Create full document metadata with all fields."""
    return DocumentMetadata(
        title="Full Document",
        owner="platform-team",
        audience=["engineers", "devops"],
        status="published",
        version="2.0",
        labels=["api", "v2"],
    )


class TestBaseDocGenerator:
    """Test base DocGenerator functionality."""

    def test_add_metadata_section_with_all_fields(self, full_metadata):
        """Test metadata section with all fields populated."""
        gen = APIDocGenerator(full_metadata)
        section = gen._add_metadata_section()

        assert "Document Information" in section
        assert "platform-team" in section
        assert "engineers" in section
        assert "devops" in section
        assert "published" in section
        assert "2.0" in section

    def test_add_metadata_section_owner_only(self):
        """Test metadata section with only owner."""
        metadata = DocumentMetadata(
            title="Test",
            owner="team-a",
        )
        gen = APIDocGenerator(metadata)
        section = gen._add_metadata_section()

        assert "team-a" in section
        assert "Document Information" in section

    def test_add_metadata_section_audience_only(self):
        """Test metadata section with only audience."""
        metadata = DocumentMetadata(
            title="Test",
            audience=["engineers", "devops"],
        )
        gen = APIDocGenerator(metadata)
        section = gen._add_metadata_section()

        assert "engineers" in section
        assert "devops" in section

    def test_add_metadata_section_status_only(self):
        """Test metadata section with only status."""
        metadata = DocumentMetadata(
            title="Test",
            status="draft",
        )
        gen = APIDocGenerator(metadata)
        section = gen._add_metadata_section()

        assert "draft" in section

    def test_add_metadata_section_version_only(self):
        """Test metadata section with only version."""
        metadata = DocumentMetadata(
            title="Test",
            version="1.5",
        )
        gen = APIDocGenerator(metadata)
        section = gen._add_metadata_section()

        assert "1.5" in section

    def test_add_metadata_section_minimal(self, minimal_metadata):
        """Test metadata section with minimal fields."""
        gen = APIDocGenerator(minimal_metadata)
        section = gen._add_metadata_section()

        assert "Document Information" in section
        assert "<table>" in section

    def test_wrap_storage_includes_timestamp(self, basic_metadata):
        """Test that wrap_storage includes timestamp."""
        gen = APIDocGenerator(basic_metadata)
        content = "<p>Test content</p>"
        wrapped = gen._wrap_storage(content)

        assert "Auto-generated on" in wrapped
        assert "Confluence Skill" in wrapped
        assert "<p>Test content</p>" in wrapped
        assert "ac:structured-macro" in wrapped


class TestAPIDocGenerator:
    """Test API documentation generator."""

    def test_generate_with_apis(self, basic_metadata):
        """Test API doc generation with APIs."""
        extracted_info = {
            "apis": [
                {"method": "GET", "path": "/users", "file": "routes.py"},
                {"method": "POST", "path": "/users", "file": "routes.py"},
            ]
        }
        gen = APIDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "API Documentation" in doc
        assert "GET" in doc
        assert "/users" in doc
        assert "routes.py" in doc

    def test_generate_without_apis(self, basic_metadata):
        """Test API doc generation without APIs."""
        gen = APIDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "API Documentation" in doc
        # Should still include metadata
        assert "Document Information" in doc

    def test_generate_with_empty_apis(self, basic_metadata):
        """Test API doc with empty API list."""
        extracted_info = {"apis": []}
        gen = APIDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "API Documentation" in doc
        assert "Endpoints" not in doc

    def test_generate_with_api_defaults(self, basic_metadata):
        """Test API doc with missing method and path."""
        extracted_info = {
            "apis": [
                {"file": "routes.py"},
            ]
        }
        gen = APIDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "GET" in doc  # Default method
        assert "<code></code>" in doc  # Empty path


class TestArchitectureDocGenerator:
    """Test architecture documentation generator."""

    def test_generate_with_architecture(self, basic_metadata):
        """Test architecture doc with architecture info."""
        extracted_info = {
            "architecture": [
                {"type": "file_structure", "summary": "Layered architecture with models, services, and routes"},
            ]
        }
        gen = ArchitectureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "Architecture Documentation" in doc
        assert "System Architecture" in doc
        assert "Layered architecture" in doc

    def test_generate_with_dependencies(self, basic_metadata):
        """Test architecture doc with dependencies."""
        extracted_info = {
            "dependencies": [
                {"name": "flask", "spec": "2.0.0"},
                {"name": "sqlalchemy", "spec": "1.4.0"},
            ]
        }
        gen = ArchitectureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "Dependencies" in doc
        assert "flask" in doc
        assert "sqlalchemy" in doc

    def test_generate_dependencies_limit(self, basic_metadata):
        """Test that dependencies are limited to 20."""
        deps = [{"name": f"dep-{i}", "spec": "1.0"} for i in range(30)]
        extracted_info = {"dependencies": deps}
        gen = ArchitectureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        # Should contain first 20 deps
        assert "dep-0" in doc
        assert "dep-19" in doc
        # Should not contain dep beyond 20
        assert "dep-29" not in doc

    def test_generate_without_architecture_or_deps(self, basic_metadata):
        """Test architecture doc without extracted info."""
        gen = ArchitectureDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "Architecture Documentation" in doc


class TestRunbookDocGenerator:
    """Test runbook documentation generator."""

    def test_generate_runbook(self, basic_metadata):
        """Test runbook generation."""
        gen = RunbookDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "Runbook" in doc
        assert "Prerequisites" in doc
        assert "Troubleshooting Steps" in doc
        assert "Escalation" in doc
        assert "Document Information" in doc

    def test_generate_runbook_structure(self, basic_metadata):
        """Test runbook has proper structure."""
        gen = RunbookDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "<h1>" in doc
        assert "<h2>" in doc
        assert "<ul>" in doc
        assert "<ol>" in doc


class TestADRDocGenerator:
    """Test Architecture Decision Record generator."""

    def test_generate_adr(self):
        """Test ADR generation."""
        metadata = DocumentMetadata(title="Use PostgreSQL", status="accepted")
        gen = ADRDocGenerator(metadata)
        doc = gen.generate()

        assert "Architecture Decision Record" in doc
        assert "Status" in doc
        assert "ACCEPTED" in doc
        assert "Context" in doc
        assert "Decision" in doc
        assert "Consequences" in doc

    def test_generate_adr_draft_status(self):
        """Test ADR with draft status."""
        metadata = DocumentMetadata(title="Proposed Decision", status="draft")
        gen = ADRDocGenerator(metadata)
        doc = gen.generate()

        assert "DRAFT" in doc


class TestFeatureDocGenerator:
    """Test feature documentation generator."""

    def test_generate_feature(self, basic_metadata):
        """Test feature doc generation."""
        gen = FeatureDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "Feature Documentation" in doc
        assert "Overview" in doc
        assert "Use Cases" in doc
        assert "Implementation Details" in doc

    def test_generate_feature_with_apis(self, basic_metadata):
        """Test feature doc with API endpoints."""
        extracted_info = {
            "apis": [
                {"method": "GET", "path": "/products"},
                {"method": "POST", "path": "/products"},
            ]
        }
        gen = FeatureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "API Endpoints" in doc
        assert "GET /products" in doc
        assert "POST /products" in doc

    def test_generate_feature_apis_limit(self, basic_metadata):
        """Test that feature doc limits APIs to 10."""
        apis = [{"method": "GET", "path": f"/endpoint-{i}"} for i in range(15)]
        extracted_info = {"apis": apis}
        gen = FeatureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        # Should contain first 10
        assert "/endpoint-0" in doc
        assert "/endpoint-9" in doc
        # Should not contain beyond 10
        assert "/endpoint-14" not in doc


class TestInfrastructureDocGenerator:
    """Test infrastructure documentation generator."""

    def test_generate_infrastructure(self, basic_metadata):
        """Test infrastructure doc generation."""
        gen = InfrastructureDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "Infrastructure Documentation" in doc
        assert "System Architecture" in doc
        assert "Deployment" in doc
        assert "Monitoring" in doc

    def test_generate_with_components(self, basic_metadata):
        """Test infrastructure with components."""
        extracted_info = {
            "dependencies": [
                {"name": "Kubernetes", "spec": "1.20"},
                {"name": "Prometheus", "spec": "latest"},
            ]
        }
        gen = InfrastructureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        assert "Components" in doc
        assert "Kubernetes" in doc
        assert "Prometheus" in doc

    def test_generate_components_limit(self, basic_metadata):
        """Test that components are limited to 20."""
        deps = [{"name": f"component-{i}", "spec": "1.0"} for i in range(25)]
        extracted_info = {"dependencies": deps}
        gen = InfrastructureDocGenerator(basic_metadata, extracted_info)
        doc = gen.generate()

        # Should contain first 20
        assert "component-0" in doc
        assert "component-19" in doc
        # Should not contain beyond 20
        assert "component-24" not in doc


class TestTroubleshootingDocGenerator:
    """Test troubleshooting guide generator."""

    def test_generate_troubleshooting(self, basic_metadata):
        """Test troubleshooting guide generation."""
        gen = TroubleshootingDocGenerator(basic_metadata)
        doc = gen.generate()

        assert "Troubleshooting Guide" in doc
        assert "Common Issues" in doc
        assert "Debug Tips" in doc
        assert "Getting Help" in doc
        assert "Symptoms" in doc
        assert "Root Cause" in doc
        assert "Resolution" in doc


class TestCustomDocGenerator:
    """Test custom documentation generator."""

    def test_generate_custom(self):
        """Test custom doc generation."""
        metadata = DocumentMetadata(title="My Custom Guide")
        gen = CustomDocGenerator(metadata)
        doc = gen.generate()

        assert "My Custom Guide" in doc
        assert "Content" in doc
        assert "Document Information" in doc

    def test_generate_custom_with_special_chars(self):
        """Test custom doc with special characters in title."""
        metadata = DocumentMetadata(title="Guide: How to & Why")
        gen = CustomDocGenerator(metadata)
        doc = gen.generate()

        assert "Guide: How to & Why" in doc


class TestCreateGeneratorFactory:
    """Test create_generator factory function."""

    def test_create_api_generator(self, basic_metadata):
        """Test factory creates API generator."""
        gen = create_generator(
            DocumentTemplate.API,
            basic_metadata,
        )
        assert isinstance(gen, APIDocGenerator)

    def test_create_architecture_generator(self, basic_metadata):
        """Test factory creates architecture generator."""
        gen = create_generator(
            DocumentTemplate.ARCHITECTURE,
            basic_metadata,
        )
        assert isinstance(gen, ArchitectureDocGenerator)

    def test_create_runbook_generator(self, basic_metadata):
        """Test factory creates runbook generator."""
        gen = create_generator(
            DocumentTemplate.RUNBOOK,
            basic_metadata,
        )
        assert isinstance(gen, RunbookDocGenerator)

    def test_create_adr_generator(self, basic_metadata):
        """Test factory creates ADR generator."""
        gen = create_generator(
            DocumentTemplate.ADR,
            basic_metadata,
        )
        assert isinstance(gen, ADRDocGenerator)

    def test_create_feature_generator(self, basic_metadata):
        """Test factory creates feature generator."""
        gen = create_generator(
            DocumentTemplate.FEATURE,
            basic_metadata,
        )
        assert isinstance(gen, FeatureDocGenerator)

    def test_create_infrastructure_generator(self, basic_metadata):
        """Test factory creates infrastructure generator."""
        gen = create_generator(
            DocumentTemplate.INFRASTRUCTURE,
            basic_metadata,
        )
        assert isinstance(gen, InfrastructureDocGenerator)

    def test_create_troubleshooting_generator(self, basic_metadata):
        """Test factory creates troubleshooting generator."""
        gen = create_generator(
            DocumentTemplate.TROUBLESHOOTING,
            basic_metadata,
        )
        assert isinstance(gen, TroubleshootingDocGenerator)

    def test_create_custom_generator(self, basic_metadata):
        """Test factory creates custom generator."""
        gen = create_generator(
            DocumentTemplate.CUSTOM,
            basic_metadata,
        )
        assert isinstance(gen, CustomDocGenerator)

    def test_create_with_extracted_info(self, basic_metadata):
        """Test factory passes extracted info to generator."""
        extracted_info = {
            "apis": [
                {"method": "GET", "path": "/test"},
            ]
        }
        gen = create_generator(
            DocumentTemplate.API,
            basic_metadata,
            extracted_info,
        )
        assert gen.extracted_info == extracted_info

    def test_create_without_extracted_info(self, basic_metadata):
        """Test factory creates generator without extracted info."""
        gen = create_generator(
            DocumentTemplate.API,
            basic_metadata,
        )
        assert gen.extracted_info == {}

    def test_factory_unknown_template_defaults_to_custom(self, basic_metadata):
        """Test factory defaults to custom for unknown templates."""
        # Create a mock/invalid template
        gen = create_generator(
            None,  # Invalid template
            basic_metadata,
        )
        # Should default to CustomDocGenerator
        assert isinstance(gen, CustomDocGenerator)


class TestGeneratorIntegration:
    """Integration tests across generators."""

    def test_all_generators_produce_html(self, basic_metadata):
        """Test that all generators produce valid HTML."""
        templates = [
            DocumentTemplate.API,
            DocumentTemplate.ARCHITECTURE,
            DocumentTemplate.RUNBOOK,
            DocumentTemplate.ADR,
            DocumentTemplate.FEATURE,
            DocumentTemplate.INFRASTRUCTURE,
            DocumentTemplate.TROUBLESHOOTING,
            DocumentTemplate.CUSTOM,
        ]

        for template in templates:
            gen = create_generator(template, basic_metadata)
            doc = gen.generate()

            # All should produce HTML
            assert "<" in doc
            assert ">" in doc
            assert len(doc) > 0
            # All should include metadata
            assert "Document Information" in doc

    def test_custom_generator_includes_title(self, basic_metadata):
        """Test that custom generator includes the document title."""
        gen = create_generator(DocumentTemplate.CUSTOM, basic_metadata)
        doc = gen.generate()

        assert basic_metadata.title in doc

    def test_all_generators_produce_valid_documents(self, basic_metadata):
        """Test that all generators produce non-empty valid documents."""
        templates = [
            DocumentTemplate.API,
            DocumentTemplate.ARCHITECTURE,
            DocumentTemplate.RUNBOOK,
            DocumentTemplate.ADR,
            DocumentTemplate.FEATURE,
            DocumentTemplate.INFRASTRUCTURE,
            DocumentTemplate.TROUBLESHOOTING,
            DocumentTemplate.CUSTOM,
        ]

        for template in templates:
            gen = create_generator(template, basic_metadata)
            doc = gen.generate()

            # All should produce valid HTML with h1 tag
            assert len(doc) > 0
            assert "<h1>" in doc

    def test_generator_with_complex_extracted_info(self, basic_metadata):
        """Test generators with complex extracted information."""
        extracted_info = {
            "apis": [
                {"method": "GET", "path": "/api/v1/users", "file": "api/routes.py"},
                {"method": "POST", "path": "/api/v1/users", "file": "api/routes.py"},
                {"method": "DELETE", "path": "/api/v1/users/{id}", "file": "api/routes.py"},
            ],
            "architecture": [
                {"type": "file_structure", "summary": "MVC pattern with models, views, and controllers"},
            ],
            "dependencies": [
                {"name": "flask", "spec": "2.0.0"},
                {"name": "sqlalchemy", "spec": "1.4.0"},
                {"name": "pytest", "spec": "6.2.0"},
            ],
        }

        # Test multiple generators with the same info
        for template in [DocumentTemplate.API, DocumentTemplate.FEATURE]:
            gen = create_generator(template, basic_metadata, extracted_info)
            doc = gen.generate()
            assert len(doc) > 0
