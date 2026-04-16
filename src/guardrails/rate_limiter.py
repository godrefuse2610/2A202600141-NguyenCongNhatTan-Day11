"""
Lab 11 — Rate Limiter Plugin
Prevent abuse by limiting the number of requests per user in a time window.
"""
import time
from collections import defaultdict, deque
from google.adk.plugins import base_plugin
from google.genai import types

class RateLimitPlugin(base_plugin.BasePlugin):
    """Plugin that blocks users who send too many requests.
    
    Uses a sliding window approach with a deque of timestamps.
    """

    def __init__(self, max_requests=5, window_seconds=60):
        """
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Duration of the sliding window in seconds
        """
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Dictionary mapping user_id to a deque of request timestamps
        self.user_windows = defaultdict(deque)

    async def on_user_message_callback(self, *, invocation_context, user_message):
        """Check if the user has exceeded the rate limit."""
        user_id = invocation_context.user_id if invocation_context else "anonymous"
        now = time.time()
        window = self.user_windows[user_id]

        # Remove expired timestamps from the front
        while window and now - window[0] > self.window_seconds:
            window.popleft()

        # Check if limit reached
        if len(window) >= self.max_requests:
            wait_time = int(self.window_seconds - (now - window[0]))
            return types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
                    )
                ],
            )

        # Allow request and record timestamp
        window.append(now)
        return None

if __name__ == "__main__":
    # Small test script
    import asyncio
    from unittest.mock import MagicMock

    async def test_rate_limiter():
        plugin = RateLimitPlugin(max_requests=2, window_seconds=5)
        mock_ctx = MagicMock()
        mock_ctx.user_id = "test_user"
        
        print("Sending request 1...")
        res = await plugin.on_user_message_callback(invocation_context=mock_ctx, user_message=None)
        print(f"Result: {'Passed' if not res else 'Blocked'}")
        
        print("Sending request 2...")
        res = await plugin.on_user_message_callback(invocation_context=mock_ctx, user_message=None)
        print(f"Result: {'Passed' if not res else 'Blocked'}")
        
        print("Sending request 3 (should be blocked)...")
        res = await plugin.on_user_message_callback(invocation_context=mock_ctx, user_message=None)
        print(f"Result: {'Passed' if not res else 'Blocked'}")
        if res:
            print(f"Block message: {res.parts[0].text}")

    asyncio.run(test_rate_limiter())
