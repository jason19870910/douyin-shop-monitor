"""Plugin-based Rule Engine for Compliance Checking.

Supports multiple rule types:
- KEYWORD: Simple keyword matching (text content)
- REGEX: Regular expression pattern matching (text content)
- ML_MODEL: Machine learning model inference (images, videos, text)
- CUSTOM_SCRIPT: Custom Python/JavaScript logic (extensible)

Each rule type is implemented as a plugin that conforms to the RulePlugin interface.
"""
import abc
import ast
import json
import logging
import re
import importlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Protocol, runtime_checkable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Supported rule types."""
    KEYWORD = "KEYWORD"
    REGEX = "REGEX"
    ML_MODEL = "ML_MODEL"
    CUSTOM_SCRIPT = "CUSTOM_SCRIPT"


class CheckResult(str, Enum):
    """Compliance check result."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class RuleContext:
    """Context passed to rule plugins during evaluation."""
    target_type: str  # 'product', 'video', 'creator', 'image', 'text'
    target_id: str
    target_data: Dict[str, Any]
    rule_config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckOutcome:
    """Result of a single rule check."""
    rule_id: str
    rule_name: str
    rule_type: RuleType
    status: CheckResult
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    matched_content: Optional[str] = None
    confidence: float = 1.0  # For ML_MODEL results
    execution_time_ms: float = 0.0
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@runtime_checkable
class RulePlugin(Protocol):
    """Protocol for rule plugins."""
    
    # Plugin metadata
    rule_type: RuleType
    version: str = "1.0.0"
    description: str = ""
    
    # Configuration schema (JSON Schema)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate rule configuration against schema.
        
        Returns:
            (is_valid, error_message)
        """
        ...
    
    def check(self, context: RuleContext) -> CheckOutcome:
        """Execute the compliance check.
        
        Args:
            context: Rule evaluation context
            
        Returns:
            CheckOutcome with result
        """
        ...
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with global configuration (called once at startup)."""
        ...


class BaseRulePlugin:
    """Base implementation of RulePlugin with common functionality."""
    
    rule_type: RuleType = RuleType.KEYWORD
    version: str = "1.0.0"
    description: str = ""
    config_schema: Dict[str, Any] = {}
    
    def __init__(self):
        self._initialized = False
        self._global_config: Dict[str, Any] = {}
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate rule configuration using JSON Schema."""
        if not self.config_schema:
            return True, None
        
        try:
            import jsonschema
            jsonschema.validate(instance=config, schema=self.config_schema)
            return True, None
        except ImportError:
            logger.warning("jsonschema not installed, skipping config validation")
            return True, None
        except jsonschema.ValidationError as e:
            return False, f"Config validation failed: {e.message}"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with global configuration."""
        self._global_config = config
        self._initialized = True
    
    def check(self, context: RuleContext) -> CheckOutcome:
        """Execute the compliance check (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement check()")
    
    def _create_outcome(
        self,
        rule_id: str,
        rule_name: str,
        status: CheckResult,
        message: str,
        details: Dict[str, Any] = None,
        matched_content: str = None,
        confidence: float = 1.0,
        execution_time_ms: float = 0.0
    ) -> CheckOutcome:
        """Helper to create CheckOutcome."""
        return CheckOutcome(
            rule_id=rule_id,
            rule_name=rule_name,
            rule_type=self.rule_type,
            status=status,
            message=message,
            details=details or {},
            matched_content=matched_content,
            confidence=confidence,
            execution_time_ms=execution_time_ms
        )


class KeywordRulePlugin(BaseRulePlugin):
    """KEYWORD rule type - simple keyword matching in text fields."""
    
    rule_type = RuleType.KEYWORD
    description = "Simple keyword matching in text content"
    config_schema = {
        "type": "object",
        "properties": {
            "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "fields": {"type": "array", "items": {"type": "string"}, "default": ["product_name", "description", "title"]},
            "case_sensitive": {"type": "boolean", "default": False},
            "match_all": {"type": "boolean", "default": False}
        },
        "required": ["keywords"]
    }
    
    def check(self, context: RuleContext) -> CheckOutcome:
        import time
        start_time = time.time()
        
        keywords = context.rule_config.get("keywords", [])
        fields = context.rule_config.get("fields", ["product_name", "description", "title"])
        case_sensitive = context.rule_config.get("case_sensitive", False)
        match_all = context.rule_config.get("match_all", False)
        
        if not keywords:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Keyword Rule"),
                status=CheckResult.SKIPPED,
                message="No keywords configured",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Extract text content from target data
        text_parts = []
        for field in fields:
            value = context.target_data.get(field)
            if value:
                text_parts.append(str(value))
        
        full_text = " ".join(text_parts)
        if not case_sensitive:
            full_text = full_text.lower()
            keywords = [k.lower() for k in keywords]
        
        # Check matches
        matched_keywords = []
        for kw in keywords:
            if kw in full_text:
                matched_keywords.append(kw)
                if not match_all:
                    break
        
        execution_time = (time.time() - start_time) * 1000
        
        if matched_keywords:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Keyword Rule"),
                status=CheckResult.FAIL,
                message=f"Found {len(matched_keywords)} prohibited keyword(s)",
                details={"matched_keywords": matched_keywords, "checked_fields": fields},
                matched_content=", ".join(matched_keywords[:5]),
                execution_time_ms=execution_time
            )
        
        return self._create_outcome(
            rule_id=context.rule_config.get("rule_id", "unknown"),
            rule_name=context.rule_config.get("rule_name", "Keyword Rule"),
            status=CheckResult.PASS,
            message="No prohibited keywords found",
            details={"checked_fields": fields, "keyword_count": len(keywords)},
            execution_time_ms=execution_time
        )


class RegexRulePlugin(BaseRulePlugin):
    """REGEX rule type - regular expression pattern matching."""
    
    rule_type = RuleType.REGEX
    description = "Regular expression pattern matching in text content"
    config_schema = {
        "type": "object",
        "properties": {
            "patterns": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "fields": {"type": "array", "items": {"type": "string"}, "default": ["product_name", "description", "title"]},
            "flags": {"type": "integer", "default": 0}
        },
        "required": ["patterns"]
    }
    
    def check(self, context: RuleContext) -> CheckOutcome:
        import time
        start_time = time.time()
        
        patterns = context.rule_config.get("patterns", [])
        fields = context.rule_config.get("fields", ["product_name", "description", "title"])
        flags = context.rule_config.get("flags", 0)
        
        if not patterns:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Regex Rule"),
                status=CheckResult.SKIPPED,
                message="No patterns configured",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Compile patterns
        compiled_patterns = []
        for p in patterns:
            try:
                compiled_patterns.append(re.compile(p, flags))
            except re.error as e:
                return self._create_outcome(
                    rule_id=context.rule_config.get("rule_id", "unknown"),
                    rule_name=context.rule_config.get("rule_name", "Regex Rule"),
                    status=CheckResult.ERROR,
                    message=f"Invalid regex pattern: {p} - {e}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
        
        # Extract text content
        text_parts = []
        for field in fields:
            value = context.target_data.get(field)
            if value:
                text_parts.append(str(value))
        
        full_text = " ".join(text_parts)
        
        # Check matches
        matched_patterns = []
        for pattern in compiled_patterns:
            match = pattern.search(full_text)
            if match:
                matched_patterns.append({
                    "pattern": pattern.pattern,
                    "match": match.group(0),
                    "span": match.span()
                })
        
        execution_time = (time.time() - start_time) * 1000
        
        if matched_patterns:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Regex Rule"),
                status=CheckResult.FAIL,
                message=f"Found {len(matched_patterns)} regex match(es)",
                details={"matched_patterns": matched_patterns, "checked_fields": fields},
                matched_content=", ".join([m["match"][:50] for m in matched_patterns[:3]]),
                execution_time_ms=execution_time
            )
        
        return self._create_outcome(
            rule_id=context.rule_config.get("rule_id", "unknown"),
            rule_name=context.rule_config.get("rule_name", "Regex Rule"),
            status=CheckResult.PASS,
            message="No regex matches found",
            details={"checked_fields": fields, "pattern_count": len(patterns)},
            execution_time_ms=execution_time
        )


class MLModelRulePlugin(BaseRulePlugin):
    """ML_MODEL rule type - machine learning model inference for images/videos/text.
    
    Supports:
    - Image classification (NSFW, violence, etc.)
    - Video frame analysis
    - Text classification (spam, sentiment, etc.)
    - Custom model endpoints
    """
    
    rule_type = RuleType.ML_MODEL
    description = "Machine learning model inference for content analysis"
    config_schema = {
        "type": "object",
        "properties": {
            "model_endpoint": {"type": "string", "format": "uri"},
            "model_type": {"type": "string", "enum": ["image_classification", "video_analysis", "text_classification", "custom"]},
            "input_field": {"type": "string", "description": "Field containing input data (URL, text, etc.)"},
            "threshold": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5},
            "labels": {"type": "array", "items": {"type": "string"}},
            "timeout_seconds": {"type": "integer", "default": 30},
            "headers": {"type": "object"}
        },
        "required": ["model_endpoint", "model_type", "input_field"]
    }
    
    def __init__(self):
        super().__init__()
        self._http_client = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        try:
            import httpx
            self._http_client = httpx.AsyncClient(timeout=30.0)
        except ImportError:
            logger.warning("httpx not installed, ML_MODEL plugin will use fallback")
    
    def check(self, context: RuleContext) -> CheckOutcome:
        import time
        start_time = time.time()
        
        model_endpoint = context.rule_config.get("model_endpoint")
        model_type = context.rule_config.get("model_type")
        input_field = context.rule_config.get("input_field")
        threshold = context.rule_config.get("threshold", 0.5)
        labels = context.rule_config.get("labels", [])
        timeout = context.rule_config.get("timeout_seconds", 30)
        headers = context.rule_config.get("headers", {})
        
        if not model_endpoint or not model_type or not input_field:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "ML Model Rule"),
                status=CheckResult.ERROR,
                message="Missing required configuration: model_endpoint, model_type, input_field",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Get input data
        input_data = context.target_data.get(input_field)
        if not input_data:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "ML Model Rule"),
                status=CheckResult.SKIPPED,
                message=f"Input field '{input_field}' not found in target data",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Prepare request payload based on model type
        payload = self._prepare_payload(model_type, input_data, context.target_data)
        
        # Call ML model endpoint
        try:
            import requests
            response = requests.post(
                model_endpoint,
                json=payload,
                headers={"Content-Type": "application/json", **headers},
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
        except ImportError:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "ML Model Rule"),
                status=CheckResult.ERROR,
                message="requests library not available",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except requests.RequestException as e:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "ML Model Rule"),
                status=CheckResult.ERROR,
                message=f"ML model request failed: {e}",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        # Parse result
        execution_time = (time.time() - start_time) * 1000
        return self._parse_result(
            context=context,
            result=result,
            labels=labels,
            threshold=threshold,
            execution_time=execution_time
        )
    
    def _prepare_payload(self, model_type: str, input_data: Any, target_data: Dict) -> Dict:
        """Prepare payload based on model type."""
        if model_type == "image_classification":
            return {"image_url": input_data, "metadata": target_data}
        elif model_type == "video_analysis":
            return {"video_url": input_data, "metadata": target_data}
        elif model_type == "text_classification":
            return {"text": input_data, "metadata": target_data}
        else:
            return {"input": input_data, "metadata": target_data}
    
    def _parse_result(
        self,
        context: RuleContext,
        result: Dict,
        labels: List[str],
        threshold: float,
        execution_time: float
    ) -> CheckOutcome:
        """Parse ML model response."""
        rule_id = context.rule_config.get("rule_id", "unknown")
        rule_name = context.rule_config.get("rule_name", "ML Model Rule")
        
        # Expected response format:
        # {"predictions": [{"label": "nsfw", "score": 0.95}, ...]}
        # or {"class": "nsfw", "confidence": 0.95}
        
        predictions = result.get("predictions") or result.get("results") or []
        if not predictions and "class" in result:
            predictions = [{"label": result["class"], "score": result.get("confidence", 0)}]
        
        if not predictions:
            return self._create_outcome(
                rule_id=rule_id,
                rule_name=rule_name,
                status=CheckResult.WARNING,
                message="No predictions returned from model",
                details={"raw_result": result},
                execution_time_ms=execution_time
            )
        
        # Check against threshold
        violations = []
        for pred in predictions:
            label = pred.get("label", "")
            score = pred.get("score", pred.get("confidence", 0))
            
            if score >= threshold and (not labels or label in labels):
                violations.append({"label": label, "score": score})
        
        if violations:
            max_violation = max(violations, key=lambda x: x["score"])
            return self._create_outcome(
                rule_id=rule_id,
                rule_name=rule_name,
                status=CheckResult.FAIL,
                message=f"ML model detected {len(violations)} violation(s)",
                details={"violations": violations, "threshold": threshold, "labels": labels},
                matched_content=f"{max_violation['label']}: {max_violation['score']:.2%}",
                confidence=max_violation["score"],
                execution_time_ms=execution_time
            )
        
        return self._create_outcome(
            rule_id=rule_id,
            rule_name=rule_name,
            status=CheckResult.PASS,
            message="Content passed ML model check",
            details={"predictions": predictions, "threshold": threshold},
            execution_time_ms=execution_time
        )


class CustomScriptRulePlugin(BaseRulePlugin):
    """CUSTOM_SCRIPT rule type - execute custom Python/JavaScript logic.
    
    WARNING: Only enable in trusted environments!
    Supports:
    - Python code snippets (executed in restricted namespace)
    - JavaScript via Node.js (if available)
    - External script files
    """
    
    rule_type = RuleType.CUSTOM_SCRIPT
    description = "Custom script execution for complex compliance logic"
    config_schema = {
        "type": "object",
        "properties": {
            "script": {"type": "string", "description": "Inline script code"},
            "script_file": {"type": "string", "description": "Path to external script file"},
            "language": {"type": "string", "enum": ["python", "javascript"], "default": "python"},
            "timeout_seconds": {"type": "integer", "default": 10},
            "allowed_imports": {"type": "array", "items": {"type": "string"}, "default": ["json", "re", "datetime"]}
        },
        "oneOf": [
            {"required": ["script"]},
            {"required": ["script_file"]}
        ]
    }
    
    def check(self, context: RuleContext) -> CheckOutcome:
        import time
        start_time = time.time()
        
        script = context.rule_config.get("script")
        script_file = context.rule_config.get("script_file")
        language = context.rule_config.get("language", "python")
        timeout = context.rule_config.get("timeout_seconds", 10)
        allowed_imports = context.rule_config.get("allowed_imports", ["json", "re", "datetime"])
        
        if not script and not script_file:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message="Either 'script' or 'script_file' must be provided",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        if script_file:
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    script = f.read()
            except Exception as e:
                return self._create_outcome(
                    rule_id=context.rule_config.get("rule_id", "unknown"),
                    rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                    status=CheckResult.ERROR,
                    message=f"Failed to read script file: {e}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
        
        if language == "python":
            return self._execute_python(context, script, allowed_imports, start_time)
        elif language == "javascript":
            return self._execute_javascript(context, script, timeout, start_time)
        else:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message=f"Unsupported language: {language}",
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _execute_python(
        self,
        context: RuleContext,
        script: str,
        allowed_imports: List[str],
        start_time: float
    ) -> CheckOutcome:
        """Execute Python script in restricted namespace."""
        import time
        try:
            self._validate_python_script(script)
        except ValueError as exc:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message=f"Unsafe script rejected: {exc}",
                execution_time_ms=(time.time() - start_time) * 1000
            )

        # Create restricted namespace
        safe_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "print": lambda *args: None,
            },
            "context": context,
            "target": context.target_data,
            "config": context.rule_config,
        }

        # Add allowed imports
        for mod_name in allowed_imports:
            try:
                safe_globals[mod_name] = __import__(mod_name)
            except ImportError:
                pass

        # Add result dict for script to populate
        result = {"status": CheckResult.PASS, "message": "", "details": {}}
        safe_globals["result"] = result

        try:
            exec(script, safe_globals)

            execution_time = (time.time() - start_time) * 1000
            status = result.get("status", CheckResult.PASS)
            if isinstance(status, str):
                try:
                    status = CheckResult(status)
                except ValueError:
                    status = CheckResult.PASS

            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=status,
                message=result.get("message", "Script executed successfully"),
                details=result.get("details", {}),
                matched_content=result.get("matched_content"),
                confidence=result.get("confidence", 1.0),
                execution_time_ms=execution_time
            )
        except Exception as e:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message=f"Script execution failed: {e}",
                execution_time_ms=(time.time() - start_time) * 1000
            )

    @staticmethod
    def _validate_python_script(script: str) -> None:
        """Reject dangerous Python constructs before execution."""
        if not script or not script.strip():
            raise ValueError("Script body is empty")

        try:
            tree = ast.parse(script, mode='exec')
        except SyntaxError as exc:
            raise ValueError(f"Invalid Python syntax: {exc.msg}") from exc

        denied_names = {
            '__import__', 'eval', 'exec', 'compile', 'open', 'input', 'globals', 'locals', 'vars',
            'breakpoint', 'help', 'dir', 'super', 'type', 'object', 'staticmethod', 'classmethod', 'property',
            'os', 'sys', 'subprocess', 'socket', 'pathlib', 'importlib', 'builtins', 'pickle', 'marshal',
            'shutil', 'tempfile', 'requests', 'http', 'ftplib', 'sqlite3', 'ctypes', 'asyncio', 'threading',
        }
        denied_attrs = {
            '__class__', '__bases__', '__subclasses__', '__globals__', '__mro__', '__dict__',
            '__code__', '__func__', '__call__', '__getattribute__', '__setattr__', '__delattr__',
            '__get__', '__set__', '__del__', '__import__', 'mro', 'format_map'
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("Imports are not allowed in custom script rules")
            if isinstance(node, ast.Name) and node.id in denied_names:
                raise ValueError(f"Name '{node.id}' is not allowed")
            if isinstance(node, ast.Attribute) and node.attr in denied_attrs:
                raise ValueError(f"Attribute access '{node.attr}' is not allowed")
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in denied_names:
                    raise ValueError(f"Call to '{func.id}' is not allowed")
                if isinstance(func, ast.Attribute) and func.attr in denied_attrs:
                    raise ValueError(f"Method call '{func.attr}' is not allowed")

    def _execute_javascript(
        self,
        context: RuleContext,
        script: str,
        timeout: int,
        start_time: float
    ) -> CheckOutcome:
        """Execute JavaScript via Node.js."""
        import subprocess
        import json as json_module
        import time
        
        # Prepare input data
        input_data = {
            "target": context.target_data,
            "config": context.rule_config,
            "metadata": context.metadata
        }
        
        # Wrap script to accept input and return JSON
        wrapped_script = f"""
const input = {json_module.dumps(input_data)};
let result = {{status: 'pass', message: '', details: {{}}}};
try {{
    {script}
}} catch (e) {{
    result.status = 'error';
    result.message = e.message;
}}
console.log(JSON.stringify(result));
"""
        
        try:
            proc = subprocess.run(
                ["node", "-e", wrapped_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if proc.returncode != 0:
                return self._create_outcome(
                    rule_id=context.rule_config.get("rule_id", "unknown"),
                    rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                    status=CheckResult.ERROR,
                    message=f"Node.js execution failed: {proc.stderr}",
                    execution_time_ms=execution_time
                )
            
            result = json_module.loads(proc.stdout.strip())
            status = result.get("status", "pass")
            if isinstance(status, str):
                try:
                    status = CheckResult(status)
                except ValueError:
                    status = CheckResult.PASS
            
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=status,
                message=result.get("message", "Script executed successfully"),
                details=result.get("details", {}),
                matched_content=result.get("matched_content"),
                confidence=result.get("confidence", 1.0),
                execution_time_ms=execution_time
            )
        except subprocess.TimeoutExpired:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message=f"Script timeout after {timeout}s",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return self._create_outcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Custom Script Rule"),
                status=CheckResult.ERROR,
                message=f"JavaScript execution failed: {e}",
                execution_time_ms=(time.time() - start_time) * 1000
            )


class RuleEngine:
    """Main rule engine that manages plugins and executes compliance checks."""
    
    def __init__(self, global_config: Dict[str, Any] = None):
        self.global_config = global_config or {}
        self.plugins: Dict[RuleType, RulePlugin] = {}
        self._register_builtin_plugins()
        self._load_custom_plugins()
    
    def _register_builtin_plugins(self):
        """Register built-in rule plugins."""
        self.register_plugin(KeywordRulePlugin())
        self.register_plugin(RegexRulePlugin())
        self.register_plugin(MLModelRulePlugin())
        self.register_plugin(CustomScriptRulePlugin())
        logger.info("Registered built-in rule plugins: KEYWORD, REGEX, ML_MODEL, CUSTOM_SCRIPT")
    
    def _load_custom_plugins(self):
        """Load custom plugins from configuration."""
        custom_plugins = self.global_config.get("custom_rule_plugins", [])
        for plugin_spec in custom_plugins:
            try:
                self.load_plugin(plugin_spec)
            except Exception as e:
                logger.error(f"Failed to load custom plugin {plugin_spec}: {e}")
    
    def register_plugin(self, plugin: RulePlugin) -> None:
        """Register a rule plugin."""
        plugin.initialize(self.global_config)
        self.plugins[plugin.rule_type] = plugin
        logger.info(f"Registered rule plugin: {plugin.rule_type.value} v{plugin.version}")
    
    def load_plugin(self, plugin_spec: Dict[str, Any]) -> None:
        """Load a plugin from module path.
        
        plugin_spec format:
        {
            "module": "my_plugins.custom_rules",
            "class": "MyCustomPlugin",
            "config": {...}
        }
        """
        module_path = plugin_spec.get("module")
        class_name = plugin_spec.get("class")
        if not module_path or not class_name:
            raise ValueError("Plugin spec must contain 'module' and 'class'")
        
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)
        plugin = plugin_class()
        plugin.initialize(plugin_spec.get("config", {}))
        self.register_plugin(plugin)
    
    def get_plugin(self, rule_type: RuleType) -> Optional[RulePlugin]:
        """Get plugin for rule type."""
        return self.plugins.get(rule_type)
    
    def validate_rule_config(self, rule_type: RuleType, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate rule configuration against plugin schema."""
        plugin = self.get_plugin(rule_type)
        if not plugin:
            return False, f"No plugin registered for rule type: {rule_type.value}"
        return plugin.validate_config(config)
    
    def check_rule(self, context: RuleContext) -> CheckOutcome:
        """Execute a single rule check."""
        rule_type_str = context.rule_config.get("rule_type", "KEYWORD")
        try:
            rule_type = RuleType(rule_type_str)
        except ValueError:
            return CheckOutcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Unknown Rule"),
                rule_type=RuleType.KEYWORD,
                status=CheckResult.ERROR,
                message=f"Unknown rule type: {rule_type_str}",
                execution_time_ms=0
            )
        
        plugin = self.get_plugin(rule_type)
        if not plugin:
            return CheckOutcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Unknown Rule"),
                rule_type=rule_type,
                status=CheckResult.ERROR,
                message=f"No plugin available for rule type: {rule_type.value}",
                execution_time_ms=0
            )
        
        try:
            return plugin.check(context)
        except Exception as e:
            logger.error(f"Rule check failed for {context.rule_config.get('rule_id')}: {e}")
            return CheckOutcome(
                rule_id=context.rule_config.get("rule_id", "unknown"),
                rule_name=context.rule_config.get("rule_name", "Unknown Rule"),
                rule_type=rule_type,
                status=CheckResult.ERROR,
                message=f"Rule execution error: {e}",
                execution_time_ms=0
            )
    
    def check_all(self, rules: List[Dict[str, Any]], target_data: Dict[str, Any], target_type: str, target_id: str) -> List[CheckOutcome]:
        """Execute multiple rules against a target."""
        outcomes = []
        
        for rule in rules:
            if not rule.get("enabled", True):
                continue
            
            rule_ctx = RuleContext(
                target_type=target_type,
                target_id=target_id,
                target_data=target_data,
                rule_config=rule,
                metadata={"rule": rule}
            )
            
            outcome = self.check_rule(rule_ctx)
            outcomes.append(outcome)
        
        return outcomes


# Global rule engine instance
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine(global_config: Dict[str, Any] = None) -> RuleEngine:
    """Get or create global rule engine instance."""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine(global_config)
    return _rule_engine


def reset_rule_engine():
    """Reset global rule engine (for testing)."""
    global _rule_engine
    _rule_engine = None


# Convenience functions
def run_compliance_check(
    target_data: Dict[str, Any],
    target_type: str,
    target_id: str,
    rules: List[Dict[str, Any]] = None
) -> List[CheckOutcome]:
    """Run compliance checks using global rule engine."""
    from services.fetcher import cache, CACHE_KEYS
    
    if rules is None:
        rules = cache.get(CACHE_KEYS.get('compliance_rules', 'compliance_rules'), [])
    
    engine = get_rule_engine()
    return engine.check_all(rules, target_data, target_type, target_id)