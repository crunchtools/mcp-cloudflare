# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.7.1] - 2026-10-10

### Fixed

- A 403 from Cloudflare was always reported as a token missing a scope. Only
  code 10000 means that. Any other 403 now carries Cloudflare's own message, so
  an account where Zero Trust was never set up says "Access is not enabled"
  instead of naming a permission the token already has.

## [0.7.0] - 2026-10-10

### Added

- Cloudflare Access tools, for putting a hostname behind a Zero Trust login:
  `get_access_organization`, `list_access_apps`, `get_access_app`,
  `create_access_app`, `delete_access_app`, `list_access_policies`,
  `create_access_policy` and `delete_access_policy`. Access belongs to the
  account, so each tool takes a zone ID like every other tool and looks up the
  account that owns it; no account ID goes in the configuration. Applications
  are always `self_hosted`. `list_access_apps` follows pages.
- Policy rules are limited to `email`, `email_domain`, `ip` and `everyone`, and
  are validated before any request is made, along with the application's
  hostname and session duration. Application and policy IDs are validated as
  UUIDs.
- A token refused by an Access endpoint is told which scope it lacks:
  `Account > Access: Apps and Policies (Edit)`, or
  `Account > Access: Organizations, Identity Providers, and Groups (Read)` for
  `get_access_organization`.

## [0.6.0] - 2026-10-10

### Added

- The thirteen tools that only read (`list_zones`, `get_zone`,
  `list_dns_records`, `get_dns_record`, `list_request_header_rules`,
  `list_response_header_rules`, `list_url_rewrite_rules`, `list_page_rules`,
  `list_waf_rules`, `get_zone_analytics`, `get_top_pages`,
  `get_traffic_by_country`, `get_security_events`) publish
  `readOnlyHint: true`. A gateway uses it to decide whether an invalid optional
  argument may be dropped or must refuse the call (crunchtools/constitution#35).
- Tests pin every registered tool into `READ_ONLY` or `WRITES`, and check that
  a read-only tool sends only GET requests, except the four analytics tools,
  whose one POST must be a GraphQL `query` to `/graphql`.

### Changed

- Inherits constitution v1.22.0; the workflow pins and the pre-commit hook rev
  move with it.
- Constitution is now a v1.18.0 manifest: only repo-specific rules stay in
  `.specify/memory/constitution.md`; fleet and profile rules apply by reference.
- Constitution validation is pinned via `constitution.yml`.
- Dependabot auto-merges GitHub Actions minor and patch updates.

### Fixed

- The Containerfile `version` label said 0.5.0 through the 0.5.1 release; it
  carries the release version again.

## [0.5.1] - 2026-09-20

### Fixed

- v0.5.0's container build never reached GHCR. The single combined
  `build-and-push` job pinned `aquasecurity/trivy-action@0.34.1`, which
  Aquasecurity has since deleted from the Marketplace, so the job now fails
  during action resolution before any push step runs, and the historical
  workflow can no longer be replayed to backfill the missing GHCR image.
  CI has since migrated to the two-job `build-and-push-quay` /
  `build-and-push-ghcr` architecture (Constitution Section III) with a
  current Trivy pin, so cutting v0.5.1 is what actually lands the release in
  both registries.

## [0.5.0] - 2026-03-03

WAF rules management, transform rules, page rules, analytics, and comprehensive
security scanning.

### Added
- WAF custom rules (create, update, delete, list).
- Request/response header transform rules.
- URL rewrite transform rules.
- Page rules management.
- Zone analytics (GraphQL).
- Top pages, traffic by country, security events.
- Cache purge operations.
- Constitution-based quality gates and Gourmand code quality checks.
- Container images on Quay.io and GHCR.
