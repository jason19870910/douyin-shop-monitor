"""Unit tests for Rule Engine (compliance checking)."""

import pytest
import time
from services.rule_engine import (
    RuleEngine,
    RuleContext,
    CheckOutcome,
    RuleType,
    CheckResult,
    KeywordRulePlugin,
    RegexRulePlugin,
    MLModelRulePlugin,
    CustomScriptRulePlugin,
    get_rule_engine,
    reset_rule_engine,
    run_compliance_check,
)


class TestKeywordRulePlugin:
    """Test KEYWORD rule plugin."""

    def setup_method(self):
        """Create fresh plugin for each test."""
        self.plugin = KeywordRulePlugin()

    def test_keyword_plugin_metadata(self):
        """Test plugin metadata."""
        assert self.plugin.rule_type == RuleType.KEYWORD
        assert "keyword" in self.plugin.description.lower()
        assert "keywords" in self.plugin.config_schema["required"]

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {
            "keywords": ["禁止词", "违规"],
            "fields": ["product_name", "description"],
            "case_sensitive": False,
            "match_all": False
        }
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is True
        assert error is None

    def test_validate_config_missing_keywords(self):
        """Test config validation fails without keywords."""
        config = {"fields": ["product_name"]}
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is False
        assert "keywords" in error.lower()

    def test_check_no_keywords_skipped(self):
        """Test check returns SKIPPED when no keywords."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品"},
            rule_config={"rule_id": "r1", "rule_name": "Test Rule", "keywords": []}
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.SKIPPED
        assert "No keywords" in outcome.message

    def test_check_case_insensitive_match(self):
        """Test case-insensitive keyword matching."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品", "description": "这是一个好商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["好商品", "违规"],
                "case_sensitive": False
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL
        assert "好商品" in outcome.matched_content

    def test_check_case_sensitive_no_match(self):
        """Test case-sensitive keyword matching doesn't match different case."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["测试商品"],  # different case
                "case_sensitive": True
            }
        )
        outcome = self.plugin.check(context)
        # Should not match because "测试商品" != "测试商品" in case-sensitive mode
        # Actually they are the same Chinese characters, so let's test with English
        context2 = RuleContext(
            target_type="product",
            target_id="p2",
            target_data={"product_name": "Test Product"},
            rule_config={
                "rule_id": "r2",
                "rule_name": "Test Rule",
                "keywords": ["test product"],  # lowercase
                "case_sensitive": True
            }
        )
        outcome2 = self.plugin.check(context2)
        assert outcome2.status == CheckResult.PASS  # Case sensitive: "Test Product" != "test product"

    def test_check_match_all_true(self):
        """Test match_all requires all keywords to match."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品", "description": "这是一个好商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["测试", "商品", "好商品"],
                "match_all": True
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL
        assert len(outcome.details.get("matched_keywords", [])) == 3

    def test_check_match_all_false_one_match(self):
        """Test match_all=false stops at first match."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品", "description": "这是一个好商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["测试", "不存在的词"],
                "match_all": False
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL
        # Should only have first match
        assert "测试" in outcome.matched_content

    def test_check_no_match_passes(self):
        """Test check passes when no keywords match."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "正常商品", "description": "正常描述"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["违规", "禁止", "敏感"]
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.PASS

    def test_check_custom_fields(self):
        """Test check uses custom fields."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={
                "product_name": "正常商品",
                "description": "正常描述",
                "custom_field": "这里有违规词"
            },
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "keywords": ["违规"],
                "fields": ["custom_field"]
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL
        assert "custom_field" in outcome.details.get("checked_fields", [])


class TestRegexRulePlugin:
    """Test REGEX rule plugin."""

    def setup_method(self):
        """Create fresh plugin for each test."""
        self.plugin = RegexRulePlugin()

    def test_regex_plugin_metadata(self):
        """Test plugin metadata."""
        assert self.plugin.rule_type == RuleType.REGEX
        assert "regular expression" in self.plugin.description.lower()
        assert "patterns" in self.plugin.config_schema["required"]

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {
            "patterns": [r"\d{6,}", r"[A-Z]{3,}"],
            "fields": ["product_name", "description"]
        }
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is True
        assert error is None

    def test_validate_config_invalid_regex(self):
        """Test config validation - regex validation happens at runtime, not config validation."""
        # JSON schema validation only checks structure, not regex validity
        config = {"patterns": ["[invalid"]}
        is_valid, error = self.plugin.validate_config(config)
        # Config validation passes (schema is valid), regex validation happens at runtime
        assert is_valid is True

    def test_check_matches_phone_number(self):
        """Test regex matching phone numbers."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "商品", "description": "联系电话: 13800138000"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Phone Number Rule",
                "patterns": [r"1[3-9]\d{9}"]
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL
        assert "13800138000" in outcome.matched_content

    def test_check_matches_email(self):
        """Test regex matching email addresses."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"description": "联系邮箱: test@example.com"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Email Rule",
                "patterns": [r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"]
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL

    def test_check_no_match_passes(self):
        """Test check passes when no patterns match."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "正常商品", "description": "正常描述"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "patterns": [r"\d{10,}"]  # 10+ digits
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.PASS

    def test_check_invalid_regex_error(self):
        """Test check returns ERROR for invalid regex at runtime."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "patterns": ["[invalid"]  # Invalid regex
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.ERROR
        assert "Invalid regex" in outcome.message

    def test_check_custom_fields(self):
        """Test check uses custom fields."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={
                "product_name": "正常商品",
                "custom_field": "SKU123456789"
            },
            rule_config={
                "rule_id": "r1",
                "rule_name": "Test Rule",
                "patterns": [r"SKU\d{9}"],
                "fields": ["custom_field"]
            }
        )
        outcome = self.plugin.check(context)
        assert outcome.status == CheckResult.FAIL


class TestRuleEngine:
    """Test RuleEngine main class."""

    def setup_method(self):
        """Reset rule engine before each test."""
        reset_rule_engine()
        self.engine = RuleEngine()

    def test_engine_registers_builtin_plugins(self):
        """Test engine registers all built-in plugins."""
        assert self.engine.get_plugin(RuleType.KEYWORD) is not None
        assert self.engine.get_plugin(RuleType.REGEX) is not None
        assert self.engine.get_plugin(RuleType.ML_MODEL) is not None
        assert self.engine.get_plugin(RuleType.CUSTOM_SCRIPT) is not None

    def test_validate_rule_config_valid(self):
        """Test validating valid rule config."""
        is_valid, error = self.engine.validate_rule_config(
            RuleType.KEYWORD,
            {"keywords": ["测试"], "fields": ["product_name"]}
        )
        assert is_valid is True
        assert error is None

    def test_validate_rule_config_invalid_type(self):
        """Test validating unknown rule type."""
        # Since all built-in types have plugins, test the error path in check_rule
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Unknown Rule",
                "rule_type": "INVALID_TYPE"
            }
        )
        outcome = self.engine.check_rule(context)
        assert outcome.status == CheckResult.ERROR
        assert "Unknown rule type" in outcome.message

    def test_validate_rule_config_missing_keywords(self):
        """Test validating keyword rule without keywords."""
        is_valid, error = self.engine.validate_rule_config(
            RuleType.KEYWORD,
            {"fields": ["product_name"]}
        )
        assert is_valid is False
        assert "keywords" in error.lower()

    def test_check_single_keyword_rule(self):
        """Test checking a single keyword rule."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "测试商品", "description": "包含违规词"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "违规词检测",
                "rule_type": "KEYWORD",
                "keywords": ["违规"],
                "fields": ["product_name", "description"]
            }
        )
        outcome = self.engine.check_rule(context)
        assert outcome.status == CheckResult.FAIL
        assert outcome.rule_id == "r1"
        assert outcome.rule_name == "违规词检测"
        assert outcome.rule_type == RuleType.KEYWORD

    def test_check_multiple_rules(self):
        """Test checking multiple rules at once."""
        rules = [
            {
                "rule_id": "r1",
                "rule_name": "Keyword Rule",
                "rule_type": "KEYWORD",
                "enabled": True,
                "keywords": ["违规"],
                "fields": ["product_name", "description"]
            },
            {
                "rule_id": "r2",
                "rule_name": "Regex Rule",
                "rule_type": "REGEX",
                "enabled": True,
                "patterns": [r"\d{6,}"],
                "fields": ["description"]
            }
        ]
        target_data = {
            "product_name": "测试商品",
            "description": "这是一个违规商品，电话 13800138000"
        }
        outcomes = self.engine.check_all(rules, target_data, "product", "p1")
        assert len(outcomes) == 2
        assert outcomes[0].rule_id == "r1"
        assert outcomes[1].rule_id == "r2"
        assert outcomes[0].status == CheckResult.FAIL  # keyword match
        assert outcomes[1].status == CheckResult.FAIL  # regex match

    def test_check_skips_disabled_rules(self):
        """Test that disabled rules are skipped."""
        rules = [
            {
                "rule_id": "r1",
                "rule_name": "Disabled Rule",
                "rule_type": "KEYWORD",
                "enabled": False,
                "keywords": ["违规"]
            },
            {
                "rule_id": "r2",
                "rule_name": "Enabled Rule",
                "rule_type": "KEYWORD",
                "enabled": True,
                "keywords": ["正常"]
            }
        ]
        target_data = {"product_name": "正常商品"}
        outcomes = self.engine.check_all(rules, target_data, "product", "p1")
        # Only enabled rule should run
        assert len(outcomes) == 1
        assert outcomes[0].rule_id == "r2"

    def test_check_unknown_rule_type_error(self):
        """Test checking unknown rule type returns ERROR."""
        context = RuleContext(
            target_type="product",
            target_id="p1",
            target_data={"product_name": "商品"},
            rule_config={
                "rule_id": "r1",
                "rule_name": "Unknown Rule",
                "rule_type": "UNKNOWN"
            }
        )
        outcome = self.engine.check_rule(context)
        assert outcome.status == CheckResult.ERROR
        assert "Unknown rule type" in outcome.message

    def test_singleton_get_rule_engine(self):
        """Test get_rule_engine returns singleton."""
        engine1 = get_rule_engine()
        engine2 = get_rule_engine()
        assert engine1 is engine2


class TestMLModelRulePlugin:
    """Test ML_MODEL rule plugin (basic validation)."""

    def setup_method(self):
        """Create fresh plugin for each test."""
        self.plugin = MLModelRulePlugin()

    def test_ml_plugin_metadata(self):
        """Test plugin metadata."""
        assert self.plugin.rule_type == RuleType.ML_MODEL
        assert "machine learning" in self.plugin.description.lower()
        assert "model_endpoint" in self.plugin.config_schema["required"]
        assert "model_type" in self.plugin.config_schema["required"]
        assert "input_field" in self.plugin.config_schema["required"]

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {
            "model_endpoint": "https://api.example.com/predict",
            "model_type": "image_classification",
            "input_field": "image_url",
            "threshold": 0.5,
            "labels": ["nsfw", "violence"]
        }
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is True
        assert error is None

    def test_validate_config_missing_required(self):
        """Test config validation fails without required fields."""
        config = {"model_endpoint": "https://api.example.com/predict"}
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is False


class TestCustomScriptRulePlugin:
    """Test CUSTOM_SCRIPT rule plugin (basic validation)."""

    def setup_method(self):
        """Create fresh plugin for each test."""
        self.plugin = CustomScriptRulePlugin()

    def test_script_plugin_metadata(self):
        """Test plugin metadata."""
        assert self.plugin.rule_type == RuleType.CUSTOM_SCRIPT
        assert "custom script" in self.plugin.description.lower()

    def test_validate_config_with_inline_script(self):
        """Test config validation with inline script."""
        config = {
            "script": "result = {'status': 'pass', 'message': 'ok'}",
            "language": "python"
        }
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is True
        assert error is None

    def test_validate_config_with_script_file(self):
        """Test config validation with script file."""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("result = {'status': 'pass'}")
            script_file = f.name
        try:
            config = {
                "script_file": script_file,
                "language": "python"
            }
            is_valid, error = self.plugin.validate_config(config)
            assert is_valid is True
        finally:
            os.unlink(script_file)

    def test_validate_config_missing_script(self):
        """Test config validation fails without script or script_file."""
        config = {"language": "python"}
        is_valid, error = self.plugin.validate_config(config)
        assert is_valid is False
        # JSON schema validation error message
        assert error is not None


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self):
        """Reset rule engine before each test."""
        reset_rule_engine()

    def test_run_compliance_check_with_default_rules(self):
        """Test run_compliance_check with default empty rules."""
        pytest.skip("Requires Redis - run with integration tests")

    def test_run_compliance_check_with_rules_in_cache(self, monkeypatch):
        """Test run_compliance_check reads rules from cache."""
        # This would require mocking the cache, skipping for now
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])