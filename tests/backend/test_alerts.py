"""Unit tests for Alert Manager."""

import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from alerts import AlertManager, send_alert, save_config, get_config


class TestAlertManager:
    """Test AlertManager class."""

    def setup_method(self):
        """Reset environment and config before each test."""
        # Clear environment variables
        env_vars = [
            "SMTP_SERVER", "SMTP_PORT", "EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO",
            "WECOM_WEBHOOK_URL", "DINGTALK_WEBHOOK_URL", "ALERT_CONFIG_FILE"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_default_config(self):
        """Test default configuration from environment."""
        manager = AlertManager()
        assert manager.smtp_server == "smtp.gmail.com"
        assert manager.smtp_port == 587
        assert manager.email_from == ""
        assert manager.email_password == ""
        assert manager.email_to == []
        assert manager.wecom_webhook_url == ""
        assert manager.dingtalk_webhook_url == ""

    def test_custom_env_config(self):
        """Test configuration from environment variables."""
        os.environ["SMTP_SERVER"] = "smtp.custom.com"
        os.environ["SMTP_PORT"] = "465"
        os.environ["EMAIL_FROM"] = "test@example.com"
        os.environ["EMAIL_PASSWORD"] = "password123"
        os.environ["EMAIL_TO"] = "a@b.com,c@d.com"
        os.environ["WECOM_WEBHOOK_URL"] = "https://wecom.example.com/webhook"
        os.environ["DINGTALK_WEBHOOK_URL"] = "https://dingtalk.example.com/webhook"

        manager = AlertManager()
        assert manager.smtp_server == "smtp.custom.com"
        assert manager.smtp_port == 465
        assert manager.email_from == "test@example.com"
        assert manager.email_password == "password123"
        assert manager.email_to == ["a@b.com", "c@d.com"]
        assert manager.wecom_webhook_url == "https://wecom.example.com/webhook"
        assert manager.dingtalk_webhook_url == "https://dingtalk.example.com/webhook"

    def test_load_user_config_file_exists(self):
        """Test loading user config from JSON file."""
        config_data = {
            "thresholds": {"待支付": 100},
            "channels": {"email": True, "wecom": False}
        }
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                manager = AlertManager()
                assert manager.user_config == config_data

    def test_load_user_config_file_not_exists(self):
        """Test loading user config when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            manager = AlertManager()
            assert manager.user_config == {}

    def test_load_user_config_invalid_json(self):
        """Test loading user config with invalid JSON."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                manager = AlertManager()
                assert manager.user_config == {}

    def test_apply_user_config_thresholds(self):
        """Test applying user thresholds config."""
        config_data = {
            "thresholds": {"待支付": 100, "异常包裹": 20},
            "channels": {}
        }
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                manager = AlertManager()
                assert manager.thresholds["待支付"] == 100
                assert manager.thresholds["异常包裹"] == 20
                # Default thresholds should remain for unspecified
                assert manager.thresholds["待处理售后"] == 20

    def test_apply_user_config_channels(self):
        """Test applying user channels config."""
        config_data = {
            "thresholds": {},
            "channels": {"email": True, "wecom": True, "dingtalk": False}
        }
        os.environ["EMAIL_FROM"] = "test@example.com"
        os.environ["EMAIL_PASSWORD"] = "password"
        os.environ["EMAIL_TO"] = "a@b.com"
        os.environ["WECOM_WEBHOOK_URL"] = "https://wecom.example.com"

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                manager = AlertManager()
                assert manager.channel_email is True
                assert manager.channel_wecom is True
                assert manager.channel_dingtalk is False

    def test_is_enabled_with_channels(self):
        """Test is_enabled returns True when channels configured."""
        os.environ["EMAIL_FROM"] = "test@example.com"
        os.environ["EMAIL_PASSWORD"] = "password"
        os.environ["EMAIL_TO"] = "a@b.com"

        manager = AlertManager()
        assert manager.is_enabled() is True

    def test_is_enabled_without_channels(self):
        """Test is_enabled returns False when no channels configured."""
        manager = AlertManager()
        assert manager.is_enabled() is False

    def test_send_no_channels_configured(self):
        """Test send returns False when no channels configured."""
        manager = AlertManager()
        result = manager.send("Test Title", "Test Content")
        assert result is False

    @patch("alerts.AlertManager._send_email")
    def test_send_email_channel(self, mock_send_email):
        """Test sending email alert."""
        os.environ["EMAIL_FROM"] = "test@example.com"
        os.environ["EMAIL_PASSWORD"] = "password"
        os.environ["EMAIL_TO"] = "a@b.com"

        manager = AlertManager()
        result = manager.send("Test Title", "Test Content", level="WARNING")

        assert result is True
        mock_send_email.assert_called_once_with("Test Title", "Test Content", "WARNING")

    @patch("alerts.AlertManager._send_wecom")
    def test_send_wecom_channel(self, mock_send_wecom):
        """Test sending WeCom alert."""
        os.environ["WECOM_WEBHOOK_URL"] = "https://wecom.example.com/webhook"

        manager = AlertManager()
        result = manager.send("Test Title", "Test Content", level="ERROR")

        assert result is True
        mock_send_wecom.assert_called_once_with("Test Title", "Test Content", "ERROR", None)

    @patch("alerts.AlertManager._send_dingtalk")
    def test_send_dingtalk_channel(self, mock_send_dingtalk):
        """Test sending DingTalk alert."""
        os.environ["DINGTALK_WEBHOOK_URL"] = "https://dingtalk.example.com/webhook"

        manager = AlertManager()
        result = manager.send("Test Title", "Test Content", level="CRITICAL")

        assert result is True
        mock_send_dingtalk.assert_called_once_with("Test Title", "Test Content", "CRITICAL", None)

    @patch("alerts.AlertManager._send_email")
    @patch("requests.post")
    def test_send_continues_on_email_failure(self, mock_post, mock_send_email):
        """Test send continues to other channels when email fails."""
        os.environ["EMAIL_FROM"] = "test@example.com"
        os.environ["EMAIL_PASSWORD"] = "password"
        os.environ["EMAIL_TO"] = "a@b.com"
        os.environ["WECOM_WEBHOOK_URL"] = "https://wecom.example.com/webhook"

        mock_send_email.side_effect = Exception("SMTP error")
        # Mock WeCom response
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        manager = AlertManager()
        result = manager.send("Test Title", "Test Content")

        assert result is True  # WeCom should still succeed
        mock_send_email.assert_called_once()
        mock_post.assert_called_once()

    def test_send_with_extra_data(self):
        """Test send includes extra_data in WeCom message."""
        os.environ["WECOM_WEBHOOK_URL"] = "https://wecom.example.com/webhook"

        with patch("alerts.AlertManager._send_wecom") as mock_send_wecom:
            manager = AlertManager()
            extra = {"product_id": "123", "sales_drop": "30%"}
            manager.send("Test Title", "Test Content", level="WARNING", extra_data=extra)

            mock_send_wecom.assert_called_once_with(
                "Test Title", "Test Content", "WARNING", extra
            )

    @patch("smtplib.SMTP")
    def test_send_email_implementation(self, mock_smtp):
        """Test _send_email implementation."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        manager = AlertManager()
        manager.email_from = "from@example.com"
        manager.email_to = ["to@example.com"]
        manager.smtp_server = "smtp.example.com"
        manager.smtp_port = 587
        manager.email_password = "password"

        manager._send_email("Test Subject", "Test Body", "INFO")

        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("from@example.com", "password")
        mock_server.sendmail.assert_called_once()

    @patch("requests.post")
    def test_send_wecom_implementation(self, mock_post):
        """Test _send_wecom implementation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        manager = AlertManager()
        manager.wecom_webhook_url = "https://wecom.example.com/webhook"
        manager.level_colors = {"WARNING": "#faad14"}

        manager._send_wecom("Test Title", "Test Content", "WARNING", {"key": "value"})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://wecom.example.com/webhook"
        assert call_args[1]["json"]["msgtype"] == "markdown"
        assert "Test Title" in call_args[1]["json"]["markdown"]["content"]
        assert "WARNING" in call_args[1]["json"]["markdown"]["content"]
        assert "- **key**: value" in call_args[1]["json"]["markdown"]["content"]

    @patch("requests.post")
    def test_send_wecom_implementation_error(self, mock_post):
        """Test _send_wecom raises error on API failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 40001, "errmsg": "invalid webhook"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        manager = AlertManager()
        manager.wecom_webhook_url = "https://wecom.example.com/webhook"

        with pytest.raises(Exception, match="企微 API 错误"):
            manager._send_wecom("Test Title", "Test Content", "WARNING")

    @patch("requests.post")
    def test_send_dingtalk_implementation(self, mock_post):
        """Test _send_dingtalk implementation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errcode": 0}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        manager = AlertManager()
        manager.dingtalk_webhook_url = "https://dingtalk.example.com/webhook"
        manager.level_colors = {"ERROR": "#ff4d4f"}

        manager._send_dingtalk("Test Title", "Test Content", "ERROR", {"detail": "info"})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://dingtalk.example.com/webhook"
        assert call_args[1]["json"]["msgtype"] == "markdown"
        assert "Test Title" in call_args[1]["json"]["markdown"]["text"]
        assert "ERROR" in call_args[1]["json"]["markdown"]["text"]
        assert "- **detail**: info" in call_args[1]["json"]["markdown"]["text"]


class TestSendAlertFunction:
    """Test send_alert convenience function."""

    def setup_method(self):
        """Clear environment before each test."""
        env_vars = [
            "SMTP_SERVER", "SMTP_PORT", "EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO",
            "WECOM_WEBHOOK_URL", "DINGTALK_WEBHOOK_URL", "ALERT_CONFIG_FILE"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    @patch("alerts.alert_manager.send")
    def test_send_alert_calls_manager(self, mock_send):
        """Test send_alert delegates to global manager."""
        mock_send.return_value = True
        result = send_alert("Title", "Content", "INFO", {"extra": "data"})
        assert result is True
        mock_send.assert_called_once_with("Title", "Content", "INFO", {"extra": "data"})


class TestSaveConfig:
    """Test save_config function."""

    def setup_method(self):
        """Clear environment before each test."""
        if "ALERT_CONFIG_FILE" in os.environ:
            del os.environ["ALERT_CONFIG_FILE"]

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_config_creates_directory_and_file(self, mock_open_func, mock_makedirs):
        """Test save_config creates directory and writes file."""
        from alerts import alert_manager
        alert_manager.config_file = "/tmp/test_config.json"

        result = save_config({"thresholds": {}, "channels": {}})

        assert result is True
        mock_makedirs.assert_called_once_with(os.path.dirname("/tmp/test_config.json"), exist_ok=True)
        mock_open_func.assert_called_once_with("/tmp/test_config.json", 'w', encoding='utf-8')

    @patch("os.makedirs", side_effect=Exception("Permission denied"))
    def test_save_config_handles_error(self, mock_makedirs):
        """Test save_config handles errors gracefully."""
        from alerts import alert_manager
        alert_manager.config_file = "/tmp/test_config.json"

        result = save_config({"thresholds": {}})

        assert result is False


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_returns_current_settings(self):
        """Test get_config returns current alert settings."""
        from alerts import alert_manager
        alert_manager.thresholds = {"待支付": 50}
        alert_manager.channel_email = True
        alert_manager.channel_wecom = False
        alert_manager.channel_dingtalk = True
        alert_manager.config_file = "/tmp/alert_config.json"

        config = get_config()

        assert config["thresholds"] == {"待支付": 50}
        assert config["channels"]["email"] is True
        assert config["channels"]["wecom"] is False
        assert config["channels"]["dingtalk"] is True
        assert config["config_file"] == "/tmp/alert_config.json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])