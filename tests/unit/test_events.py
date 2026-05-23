"""
Unit tests for the Event system (events.py).
"""

import pytest
from tests.expectations import expect


class TestEventSubscribe:
    """Tests for events.subscribe."""

    def test_subscribe_and_trigger(self):
        """Test basic subscribe and trigger."""
        from src.events import subscribe, trigger, event_listeners
        event_listeners.clear()

        results = []
        subscribe("test_event", lambda x: results.append(x))
        trigger("test_event", "hello")
        expect(results).to_contain("hello")

    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event."""
        from src.events import subscribe, trigger, event_listeners
        event_listeners.clear()

        results = []
        subscribe("multi_event", lambda x: results.append(f"a:{x}"))
        subscribe("multi_event", lambda x: results.append(f"b:{x}"))
        trigger("multi_event", "test")
        expect(results).to_have_length(2)
        expect(results).to_contain("a:test")
        expect(results).to_contain("b:test")

    def test_subscribe_creates_list(self):
        """Test that subscribing creates a list for the event."""
        from src.events import subscribe, event_listeners
        event_listeners.clear()

        subscribe("new_event", lambda: None)
        expect(event_listeners).to_have_key("new_event")
        expect(event_listeners["new_event"]).to_be_a(list)


class TestEventUnsubscribe:
    """Tests for events.unsubscribe."""

    def test_unsubscribe_removes_callback(self):
        """Test that unsubscribe removes the callback."""
        from src.events import subscribe, unsubscribe, trigger, event_listeners
        event_listeners.clear()

        results = []
        callback = lambda x: results.append(x)
        subscribe("unsub_event", callback)
        unsubscribe("unsub_event", callback)
        trigger("unsub_event", "should_not_appear")
        expect(results).to_be_empty()

    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribing a callback that was never subscribed."""
        from src.events import unsubscribe, event_listeners
        event_listeners.clear()
        event_listeners["test"] = []
        # Should not raise
        unsubscribe("test", lambda: None)

    def test_unsubscribe_nonexistent_event(self):
        """Test unsubscribing from an event that doesn't exist."""
        from src.events import unsubscribe
        # Should not raise
        unsubscribe("nonexistent", lambda: None)


class TestEventTrigger:
    """Tests for events.trigger."""

    def test_trigger_nonexistent_event(self):
        """Test triggering an event with no subscribers."""
        from src.events import trigger, event_listeners
        event_listeners.clear()
        # Should not raise
        trigger("nonexistent_event", "data")

    def test_trigger_with_multiple_args(self):
        """Test triggering with multiple arguments."""
        from src.events import subscribe, trigger, event_listeners
        event_listeners.clear()

        results = []
        subscribe("args_event", lambda a, b: results.append((a, b)))
        trigger("args_event", "first", "second")
        expect(results).to_contain(("first", "second"))

    def test_trigger_no_args(self):
        """Test triggering with no arguments."""
        from src.events import subscribe, trigger, event_listeners
        event_listeners.clear()

        results = []
        subscribe("no_args_event", lambda: results.append("called"))
        trigger("no_args_event")
        expect(results).to_contain("called")
