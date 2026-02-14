"""Tests for input validation."""

import pytest
from pydantic import ValidationError

from mcp_cloudflare_crunchtools.models import (
    DnsRecordInput,
    DnsRecordUpdateInput,
    ZoneInput,
    validate_record_id,
    validate_rule_id,
    validate_zone_id,
)


class TestZoneIdValidation:
    """Tests for zone_id validation."""

    def test_valid_zone_id(self) -> None:
        """Valid 32-character hex string should pass."""
        zone_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert validate_zone_id(zone_id) == zone_id

    def test_invalid_zone_id_too_short(self) -> None:
        """Zone ID that is too short should fail."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_zone_id("abc123")

    def test_invalid_zone_id_too_long(self) -> None:
        """Zone ID that is too long should fail."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_zone_id("a" * 33)

    def test_invalid_zone_id_non_hex(self) -> None:
        """Zone ID with non-hex characters should fail."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_zone_id("g" * 32)  # 'g' is not hex

    def test_invalid_zone_id_uppercase(self) -> None:
        """Zone ID with uppercase should fail (Cloudflare uses lowercase)."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_zone_id("A" * 32)


class TestRecordIdValidation:
    """Tests for record_id validation."""

    def test_valid_record_id(self) -> None:
        """Valid 32-character hex string should pass."""
        record_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert validate_record_id(record_id) == record_id

    def test_invalid_record_id(self) -> None:
        """Invalid record ID should fail."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_record_id("invalid")


class TestRuleIdValidation:
    """Tests for rule_id validation."""

    def test_valid_rule_id(self) -> None:
        """Valid 32-character hex string should pass."""
        rule_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert validate_rule_id(rule_id) == rule_id

    def test_invalid_rule_id(self) -> None:
        """Invalid rule ID should fail."""
        with pytest.raises(ValueError, match="32-character hex"):
            validate_rule_id("invalid")


class TestZoneInput:
    """Tests for ZoneInput model."""

    def test_valid_zone_id(self) -> None:
        """Valid zone_id should pass."""
        zone = ZoneInput(zone_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4")
        assert zone.zone_id == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"

    def test_valid_zone_name(self) -> None:
        """Valid zone_name should pass."""
        zone = ZoneInput(zone_name="example.com")
        assert zone.zone_name == "example.com"

    def test_invalid_zone_id(self) -> None:
        """Invalid zone_id should fail validation."""
        with pytest.raises(ValidationError):
            ZoneInput(zone_id="invalid")

    def test_extra_fields_rejected(self) -> None:
        """Extra fields should be rejected."""
        with pytest.raises(ValidationError):
            ZoneInput(zone_id="a" * 32, extra_field="value")  # type: ignore[call-arg]


class TestDnsRecordInput:
    """Tests for DnsRecordInput model."""

    def test_valid_a_record(self) -> None:
        """Valid A record should pass."""
        record = DnsRecordInput(
            type="A",
            name="www",
            content="192.168.1.1",
        )
        assert record.type == "A"
        assert record.name == "www"
        assert record.content == "192.168.1.1"
        assert record.ttl == 1
        assert record.proxied is False

    def test_valid_mx_record_with_priority(self) -> None:
        """Valid MX record with priority should pass."""
        record = DnsRecordInput(
            type="MX",
            name="@",
            content="mail.example.com",
            priority=10,
        )
        assert record.priority == 10

    def test_case_insensitive_type(self) -> None:
        """Record type should be normalized to uppercase."""
        record = DnsRecordInput(
            type="aaaa",
            name="www",
            content="2001:db8::1",
        )
        assert record.type == "AAAA"

    def test_invalid_record_type(self) -> None:
        """Invalid record type should fail."""
        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="INVALID",
                name="www",
                content="test",
            )

    def test_name_too_long(self) -> None:
        """Name exceeding max length should fail."""
        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="A",
                name="a" * 256,
                content="192.168.1.1",
            )

    def test_content_too_long(self) -> None:
        """Content exceeding max length should fail."""
        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="TXT",
                name="www",
                content="a" * 2049,
            )

    def test_ttl_range(self) -> None:
        """TTL outside valid range should fail."""
        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="A",
                name="www",
                content="192.168.1.1",
                ttl=0,
            )

        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="A",
                name="www",
                content="192.168.1.1",
                ttl=86401,
            )

    def test_priority_range(self) -> None:
        """Priority outside valid range should fail."""
        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="MX",
                name="@",
                content="mail.example.com",
                priority=-1,
            )

        with pytest.raises(ValidationError):
            DnsRecordInput(
                type="MX",
                name="@",
                content="mail.example.com",
                priority=65536,
            )


class TestDnsRecordUpdateInput:
    """Tests for DnsRecordUpdateInput model."""

    def test_partial_update(self) -> None:
        """Partial update with only some fields should pass."""
        update = DnsRecordUpdateInput(content="192.168.1.2")
        assert update.content == "192.168.1.2"
        assert update.type is None
        assert update.name is None

    def test_all_fields_none(self) -> None:
        """All fields None should be valid (checked at tool level)."""
        update = DnsRecordUpdateInput()
        assert update.type is None
        assert update.content is None
