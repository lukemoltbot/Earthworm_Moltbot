"""
SyncStateTracker - Prevents infinite loops in scroll synchronization.

This class provides debouncing and state tracking to prevent
recursive synchronization calls between widgets.
"""

import time


class SyncStateTracker:
    """
    Tracks synchronization state to prevent infinite loops.
    
    Features:
    - Debouncing to prevent rapid recursive calls
    - State tracking to prevent re-entrant synchronization
    - Configurable debounce delay
    """
    
    def __init__(self, debounce_ms=50):
        """
        Initialize the sync state tracker.
        
        Args:
            debounce_ms: Minimum time between sync operations in milliseconds
        """
        self.sync_in_progress = False
        self.last_sync_time = 0
        self.sync_debounce_ms = debounce_ms
        
    def should_sync(self):
        """
        Check if synchronization should proceed.
        
        Returns:
            True if synchronization should proceed, False otherwise
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Check if sync is already in progress
        if self.sync_in_progress:
            return False
            
        # Check if enough time has passed since last sync
        time_since_last_sync = current_time - self.last_sync_time
        if time_since_last_sync < self.sync_debounce_ms:
            return False
            
        return True
        
    def begin_sync(self):
        """
        Mark the beginning of a synchronization operation.
        
        This should be called before starting any synchronization
        that could trigger recursive calls.
        """
        self.sync_in_progress = True
        self.last_sync_time = time.time() * 1000
        
    def end_sync(self):
        """
        Mark the end of a synchronization operation.
        
        This should be called after synchronization is complete.
        """
        self.sync_in_progress = False
        
    def force_sync(self):
        """
        Force synchronization to proceed regardless of debounce.
        
        Use with caution - only when manual override is needed.
        """
        self.begin_sync()
        return True
        
    def get_status(self):
        """
        Get current synchronization status.
        
        Returns:
            Dictionary with sync status information
        """
        return {
            'sync_in_progress': self.sync_in_progress,
            'last_sync_time': self.last_sync_time,
            'sync_debounce_ms': self.sync_debounce_ms,
            'time_since_last_sync': (time.time() * 1000) - self.last_sync_time
        }