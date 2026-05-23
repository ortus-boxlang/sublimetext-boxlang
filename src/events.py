"""
Simple pub/sub event system for the BoxLang package.
"""
event_listeners = {}

def subscribe(event_name, callback):
    """Subscribe to an event."""
    if event_name not in event_listeners:
        event_listeners[event_name] = []
    event_listeners[event_name].append(callback)

def trigger(event_name, *event_args):
    """Trigger an event with the given arguments."""
    if event_name in event_listeners:
        for callback in event_listeners[event_name]:
            callback(*event_args)

def unsubscribe(event_name, callback):
    """Unsubscribe from an event."""
    if event_name in event_listeners:
        try:
            event_listeners[event_name].remove(callback)
        except ValueError:
            pass