"""
Lab 11 — Audit Log Plugin
Record all interactions for security auditing and monitoring.
"""
import json
import time
from datetime import datetime
from google.adk.plugins import base_plugin

class AuditLogPlugin(base_plugin.BasePlugin):
    """Plugin that logs interactions to a file or memory for auditing."""

    def __init__(self, log_file="audit_log.json"):
        """
        Args:
            log_file: Path to the JSON file where logs will be exported
        """
        super().__init__(name="audit_log")
        self.log_file = log_file
        self.logs = []

    async def on_user_message_callback(self, *, invocation_context, user_message):
        """Record the incoming user message."""
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        text = self._extract_text(user_message)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "type": "input",
            "content": text,
            "start_time": time.time()
        }
        self.logs.append(entry)
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        """Record the model response and calculate latency."""
        text = self._extract_text(llm_response)
        end_time = time.time()
        
        # Find the matching input entry (simplification for single-threaded lab)
        latency = 0
        if self.logs and self.logs[-1]["type"] == "input":
            latency = end_time - self.logs[-1]["start_time"]

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "output",
            "content": text,
            "latency_seconds": round(latency, 3),
            "blocked": "blocked" in text.lower() or "cannot provide" in text.lower()
        }
        self.logs.append(entry)
        return llm_response

    def _extract_text(self, content_obj) -> str:
        """Helper to extract text from ADK Content or ModelResponse."""
        if content_obj is None:
            return ""
            
        # If it's already a string
        if isinstance(content_obj, str):
            return content_obj
            
        text = ""
        # Handle ADK Content or objects with parts
        parts = getattr(content_obj, "parts", None)
        if parts:
            for part in parts:
                p_text = getattr(part, "text", None)
                if p_text:
                    text += str(p_text)
                elif isinstance(part, dict):
                    text += part.get("text", "")
        
        # Handle ModelResponse or objects with .content
        if not text and hasattr(content_obj, "content"):
            return self._extract_text(content_obj.content)
            
        # Fallback for dict-like objects
        if not text and isinstance(content_obj, dict):
            return content_obj.get("text", content_obj.get("content", ""))
            
        return text

    def export_json(self, filepath=None):
        """Export logs to a JSON file."""
        path = filepath or self.log_file
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, default=str)
        print(f"Audit log exported to {path}")

if __name__ == "__main__":
    # Test
    plugin = AuditLogPlugin()
    plugin.logs.append({"test": "data"})
    plugin.export_json("test_audit.json")
    import os
    if os.path.exists("test_audit.json"):
        print("Export successful!")
        os.remove("test_audit.json")
