---
name: confluence
version: 1.2.0
description: Enterprise-grade Confluence Cloud documentation skill for Claude — generate docs from code, manage pages at scale, link to Jira, use multiple templates.
---

# Confluence Skill

Invoke Confluence documentation generation and management commands directly. The `confluence` command is available system-wide.

## Quick Commands

```bash
confluence document "Document the payment API" --doc-type api --dry-run  # Preview docs
confluence search "payment API" --space-key ENGINEERING                   # Search pages
confluence archive 123456 --reason "Obsolete"                            # Archive page
```

## Available Commands

Run `confluence --help` to see all available commands:
- `document` — Generate documentation from code and publish to Confluence
- `search` — Search for pages in a Confluence space
- `archive` — Archive a page safely
- `mcp-help` — Show MCP server help

## Documentation Templates

Supported template types via `--doc-type` parameter:
- `api` — REST/GraphQL endpoint documentation
- `architecture` — System design and architecture
- `adr` — Architecture Decision Records
- `runbook` — Operational procedures
- `feature` — Feature specifications
- `infrastructure` — Infrastructure setup guides
- `troubleshooting` — Common issues and fixes
- `custom` — Custom template

## Configuration

**Master config**: `~/.confluence.yaml`
- Confluence instance URL
- Default space key
- Jira integration settings (optional)
- Documentation metadata

**Environment variables** (required):
- `CONFLUENCE_TOKEN` — API token from https://id.atlassian.com/manage-profile/security/api-tokens

**Optional environment variables**:
- `JIRA_TOKEN` — Jira API token (if Jira integration enabled)

## Usage Examples

### Generate Documentation

```bash
# Preview (dry run)
confluence document "Document the payment API" --doc-type api --dry-run

# Publish
confluence document "Document the payment API" --doc-type api --publish
```

### Search Pages

```bash
confluence search "payment API" --space-key ENGINEERING --max-results 10
```

### Archive Pages

```bash
confluence archive 123456 --reason "Superseded by new design"
```

## Key Features

- **Code-to-Docs**: Generate documentation automatically from repository code
- **Multiple Templates**: 8 professional documentation templates
- **Jira Integration**: Link pages to Jira tickets automatically
- **Bulk Operations**: Label, archive, and manage pages at scale
- **Safe Operations**: Always preview with `--dry-run` before publishing
- **Rate Limiting**: Automatic backoff respects Confluence's 60 req/min limit

## Security & Best Practices

**IMPORTANT**:
- ✅ Store credentials in environment variables only
- ✅ Use `.confluence.example.yaml` as template, never commit `.confluence.yaml`
- ✅ Never hardcode API tokens in code
- ✅ Always use `--dry-run` to preview changes first
- ✅ Review generated documentation before publishing

## Installation Verification

```bash
confluence --version       # Should show version
confluence --help          # Should show all commands
which confluence           # Should show path to confluence binary
```

If `confluence: command not found`:
1. Reinstall: `pip install -e /Users/craighoad/Repos/confluence-skill`
2. Verify PATH: `which confluence`
3. Check CONFLUENCE_TOKEN: `echo $CONFLUENCE_TOKEN`

## Related Skills

- **Jira Skill** (`/jira`) — Manage Jira tickets and epics
- **CloudCtl Skill** (`/cloudctl`) — Cloud context management

## Support

- 📖 Full documentation: https://github.com/rhyscraig/confluence-skill
- 🐛 Bug reports: https://github.com/rhyscraig/confluence-skill/issues
- 💬 Feature requests: https://github.com/rhyscraig/confluence-skill/discussions
