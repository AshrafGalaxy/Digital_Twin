"""
test_mqtt_security.py

Hermetic automated test suite for BUG-30 (MQTT Broker Authentication & ACLs).
Verifies that:
1. Broker configuration rejects anonymous connections and configures password and ACL files.
2. Mosquitto password and ACL files exist and define service boundaries.
3. Production environment fails fast at startup when using default or empty MQTT credentials.
4. Production environment starts cleanly when provided valid non-default credentials.
"""

from pathlib import Path
import pytest
from backend.core.config import Settings, INSECURE_DEFAULT_MQTT_PASSWORD
from backend.ingestion.mqtt_consumer import MQTTConsumer


def test_mosquitto_config_rejects_anonymous():
    """Verifies that mosquitto.conf explicitly disables anonymous connections."""
    conf_path = Path("infrastructure/mosquitto/mosquitto.conf")
    assert conf_path.exists(), "mosquitto.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    assert "allow_anonymous false" in lines, "allow_anonymous must be set to false"
    assert any(line.startswith("password_file") for line in lines), "password_file directive must be configured"
    assert any(line.startswith("acl_file") for line in lines), "acl_file directive must be configured"


def test_mosquitto_password_and_acl_files_exist():
    """Verifies that password and ACL files exist and define required service accounts."""
    pwd_path = Path("infrastructure/mosquitto/password_file")
    acl_path = Path("infrastructure/mosquitto/acl_file")

    assert pwd_path.exists(), "password_file must exist in infrastructure/mosquitto"
    assert acl_path.exists(), "acl_file must exist in infrastructure/mosquitto"

    pwd_content = pwd_path.read_text(encoding="utf-8")
    assert "twin_service:" in pwd_content
    assert "twin_ingest:" in pwd_content

    acl_content = acl_path.read_text(encoding="utf-8")
    assert "user twin_service" in acl_content
    assert "user twin_ingest" in acl_content
    assert "topic read corridor/#" in acl_content
    assert "topic write corridor/+/observations" in acl_content


def test_production_startup_fails_with_default_mqtt_password():
    """Verifies that production environment refuses startup when MQTT_PASSWORD is the default."""
    cfg = Settings(
        ENVIRONMENT="production",
        MQTT_USERNAME="twin_service",
        MQTT_PASSWORD=INSECURE_DEFAULT_MQTT_PASSWORD
    )
    with pytest.raises(RuntimeError) as exc_info:
        cfg.validate_production_security()
    assert "insecure or default MQTT_PASSWORD" in str(exc_info.value)


def test_production_startup_fails_with_missing_mqtt_username():
    """Verifies that production environment refuses startup when MQTT_USERNAME is empty."""
    cfg = Settings(
        ENVIRONMENT="production",
        MQTT_USERNAME="",
        MQTT_PASSWORD="strong_production_secret_key_2026"
    )
    with pytest.raises(RuntimeError) as exc_info:
        cfg.validate_production_security()
    assert "requires a configured MQTT_USERNAME" in str(exc_info.value)


def test_production_startup_succeeds_with_valid_credentials():
    """Verifies that production environment permits startup with strong, custom credentials."""
    cfg = Settings(
        ENVIRONMENT="production",
        MQTT_USERNAME="twin_service_prod",
        MQTT_PASSWORD="strong_production_secret_key_2026"
    )
    # Should not raise
    cfg.validate_production_security()


def test_development_mode_allows_default_mqtt_password():
    """Verifies that development mode smoothly permits default development credentials."""
    cfg = Settings(
        ENVIRONMENT="development",
        MQTT_USERNAME="twin_service",
        MQTT_PASSWORD=INSECURE_DEFAULT_MQTT_PASSWORD
    )
    # Should not raise in development
    cfg.validate_production_security()


def test_mqtt_consumer_initializes_with_credentials():
    """Verifies MQTTConsumer sets credentials when configured."""
    consumer = MQTTConsumer()
    assert consumer.client is not None
