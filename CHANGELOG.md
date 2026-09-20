# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

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
