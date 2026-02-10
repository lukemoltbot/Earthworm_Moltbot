"""
ScrollOptimizer - Smooth scrolling with predictive rendering.

This module provides event batching, throttling, and predictive rendering
for smooth scrolling performance with large datasets.
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import warnings

try:
    from PyQt6.QtCore import QTimer, QPoint
    PYTQT6_AVAILABLE = True
except ImportError:
    PYTQT6_AVAILABLE = False
    warnings.warn("PyQt6 not available, using mock implementations")


class ScrollMode(Enum):
    """Scroll optimization modes."""
    PRECISE = "precise"        # High precision, lower performance
    SMOOTH = "smooth"          # Balanced smoothness and performance
    PERFORMANCE = "performance"  # Maximum performance, lower precision


@dataclass
class ScrollEvent:
    """Represents a scroll event for batching."""
    timestamp: float
    delta_x: float
    delta_y: float
    position: Tuple[float, float]
    velocity: Tuple[float, float] = (0.0, 0.0)
    processed: bool = False


class ScrollOptimizer:
    """
    Optimizes scrolling performance with event batching and predictive rendering.
    
    Features:
    - Event batching and throttling
    - Predictive rendering based on scroll velocity
    - Smooth scrolling with inertia
    - Frame rate stabilization
    - Adaptive performance tuning
    """
    
    def __init__(self,
                 target_fps: int = 60,
                 scroll_mode: ScrollMode = ScrollMode.SMOOTH,
                 enable_inertia: bool = True,
                 enable_prediction: bool = True):
        """
        Initialize the ScrollOptimizer.
        
        Args:
            target_fps: Target frames per second
            scroll_mode: Scroll optimization mode
            enable_inertia: Enable smooth scrolling with inertia
            enable_prediction: Enable predictive rendering
        """
        self.target_fps = target_fps
        self.frame_interval_ms = 1000.0 / target_fps
        self.scroll_mode = scroll_mode
        self.enable_inertia = enable_inertia
        self.enable_prediction = enable_prediction
        
        # Event management
        self.event_queue: List[ScrollEvent] = []
        self.last_event_time = 0
        self.last_render_time = 0
        self.batch_window_ms = 16  # ~60 FPS
        
        # Velocity tracking for prediction
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.last_velocity_update = 0
        self.velocity_smoothing = 0.8  # Exponential smoothing factor
        
        # Inertia settings
        self.inertia_decay = 0.95  # Velocity decay per frame
        self.min_velocity = 0.1    # Minimum velocity to continue inertia
        
        # Prediction settings
        self.prediction_horizon_ms = 50  # How far ahead to predict
        self.prediction_confidence = 0.7  # Confidence in predictions
        
        # Performance metrics
        self.metrics = {
            "events_received": 0,
            "events_batched": 0,
            "events_processed": 0,
            "frames_rendered": 0,
            "prediction_hits": 0,
            "prediction_misses": 0,
            "inertia_frames": 0,
            "average_fps": 0,
            "frame_time_variance": 0,
            "dropped_frames": 0
        }
        
        # Callbacks
        self.render_callback: Optional[Callable[[float, float, bool], None]] = None
        self.prediction_callback: Optional[Callable[[float, float], Any]] = None
        
        # Adaptive settings
        self.adaptive_settings = {
            "current_fps": 0,
            "target_fps_achieved": True,
            "performance_mode": "normal",
            "last_adjustment_time": 0
        }
        
        # Frame timing
        self.frame_times: List[float] = []
        self.max_frame_history = 60  # Keep 1 second at 60 FPS
        
        # Initialize timer if PyQt6 is available
        self.timer = None
        if PYTQT6_AVAILABLE:
            self.timer = QTimer()
            self.timer.timeout.connect(self._process_batch)
            self.timer.setInterval(int(self.frame_interval_ms))
    
    def handle_scroll_event(self, delta_x: float, delta_y: float, position: Tuple[float, float]):
        """
        Handle a scroll event with optimization.
        
        Args:
            delta_x: Horizontal scroll delta
            delta_y: Vertical scroll delta
            position: Current scroll position
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        self.metrics["events_received"] += 1
        
        # Update velocity
        self._update_velocity(delta_x, delta_y, current_time)
        
        # Create scroll event
        event = ScrollEvent(
            timestamp=current_time,
            delta_x=delta_x,
            delta_y=delta_y,
            position=position,
            velocity=(self.velocity_x, self.velocity_y)
        )
        
        # Add to queue
        self.event_queue.append(event)
        self.metrics["events_batched"] += 1
        
        # Start processing if not already running
        if self.timer and not self.timer.isActive():
            self.timer.start()
        
        # Process immediately if in precise mode
        if self.scroll_mode == ScrollMode.PRECISE:
            self._process_immediate(event)
        elif len(self.event_queue) > 5:  # If queue is getting large
            self._process_batch()
    
    def set_render_callback(self, callback: Callable[[float, float, bool], None]):
        """
        Set callback for rendering.
        
        Args:
            callback: Function called with (delta_x, delta_y, is_prediction)
        """
        self.render_callback = callback
    
    def set_prediction_callback(self, callback: Callable[[float, float], Any]):
        """
        Set callback for predictive rendering.
        
        Args:
            callback: Function called with predicted (delta_x, delta_y)
        """
        self.prediction_callback = callback
    
    def start(self):
        """Start the scroll optimizer."""
        if self.timer:
            self.timer.start()
    
    def stop(self):
        """Stop the scroll optimizer."""
        if self.timer:
            self.timer.stop()
        
        # Process any remaining events
        if self.event_queue:
            self._process_batch()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        # Calculate current FPS
        if self.frame_times:
            recent_times = self.frame_times[-10:]  # Last 10 frames
            avg_frame_time = sum(recent_times) / len(recent_times)
            current_fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
            self.adaptive_settings["current_fps"] = current_fps
            self.adaptive_settings["target_fps_achieved"] = current_fps >= self.target_fps * 0.9
            
            # Update average FPS in metrics
            total_frames = self.metrics["frames_rendered"]
            current_avg = self.metrics["average_fps"]
            self.metrics["average_fps"] = (
                (current_avg * (total_frames - 1) + current_fps) / max(1, total_frames)
            )
        
        metrics = self.metrics.copy()
        metrics.update({
            "queue_size": len(self.event_queue),
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "inertia_active": self._is_inertia_active(),
            "prediction_active": self.enable_prediction and abs(self.velocity_y) > 1.0,
            "adaptive_settings": self.adaptive_settings.copy()
        })
        
        return metrics
    
    def set_scroll_mode(self, mode: ScrollMode):
        """
        Set scroll optimization mode.
        
        Args:
            mode: New scroll mode
        """
        self.scroll_mode = mode
        
        # Adjust settings based on mode
        if mode == ScrollMode.PRECISE:
            self.batch_window_ms = 8  # ~120 FPS equivalent
            self.enable_inertia = False
            self.enable_prediction = False
        elif mode == ScrollMode.SMOOTH:
            self.batch_window_ms = 16  # ~60 FPS
            self.enable_inertia = True
            self.enable_prediction = True
        elif mode == ScrollMode.PERFORMANCE:
            self.batch_window_ms = 32  # ~30 FPS
            self.enable_inertia = True
            self.enable_prediction = True
        
        # Update timer interval if available
        if self.timer:
            self.timer.setInterval(int(self.batch_window_ms))
    
    def reset(self):
        """Reset scroll optimizer state."""
        self.event_queue.clear()
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.frame_times.clear()
        
        if self.timer:
            self.timer.stop()
    
    def cleanup(self):
        """Clean up resources."""
        self.reset()
        if self.timer:
            self.timer.deleteLater()
    
    # Private methods
    
    def _update_velocity(self, delta_x: float, delta_y: float, current_time: float):
        """Update scroll velocity with exponential smoothing."""
        time_delta = current_time - self.last_velocity_update
        
        if time_delta > 0 and self.last_velocity_update > 0:
            # Calculate instantaneous velocity (pixels per ms)
            inst_velocity_x = delta_x / time_delta
            inst_velocity_y = delta_y / time_delta
            
            # Apply exponential smoothing
            self.velocity_x = (self.velocity_smoothing * self.velocity_x + 
                              (1 - self.velocity_smoothing) * inst_velocity_x)
            self.velocity_y = (self.velocity_smoothing * self.velocity_y + 
                              (1 - self.velocity_smoothing) * inst_velocity_y)
        
        self.last_velocity_update = current_time
    
    def _process_immediate(self, event: ScrollEvent):
        """Process a single event immediately."""
        if self.render_callback:
            self.render_callback(event.delta_x, event.delta_y, False)
            self._record_frame_time()
        
        event.processed = True
        self.metrics["events_processed"] += 1
        self.metrics["frames_rendered"] += 1
    
    def _process_batch(self):
        """Process batched events."""
        if not self.event_queue:
            # Check for inertia scrolling
            if self.enable_inertia and self._is_inertia_active():
                self._process_inertia()
            return
        
        current_time = time.time() * 1000
        
        # Filter events within batch window
        recent_events = [
            event for event in self.event_queue
            if current_time - event.timestamp <= self.batch_window_ms
        ]
        
        if not recent_events:
            return
        
        # Calculate aggregated deltas
        total_delta_x = sum(event.delta_x for event in recent_events)
        total_delta_y = sum(event.delta_y for event in recent_events)
        
        # Apply prediction if enabled
        is_prediction = False
        if self.enable_prediction and self.prediction_callback:
            predicted_delta = self._predict_scroll_delta()
            if predicted_delta:
                total_delta_x += predicted_delta[0] * self.prediction_confidence
                total_delta_y += predicted_delta[1] * self.prediction_confidence
                is_prediction = True
                self.metrics["prediction_hits"] += 1
        
        # Render
        if self.render_callback and (abs(total_delta_x) > 0.01 or abs(total_delta_y) > 0.01):
            self.render_callback(total_delta_x, total_delta_y, is_prediction)
            self._record_frame_time()
            
            self.metrics["frames_rendered"] += 1
            self.metrics["events_processed"] += len(recent_events)
        
        # Mark events as processed
        for event in recent_events:
            event.processed = True
        
        # Remove processed events
        self.event_queue = [event for event in self.event_queue if not event.processed]
        
        # Adaptive performance tuning
        self._adaptive_tuning()
    
    def _process_inertia(self):
        """Process inertia scrolling."""
        if abs(self.velocity_x) < self.min_velocity and abs(self.velocity_y) < self.min_velocity:
            return
        
        # Calculate inertia delta based on velocity
        inertia_delta_x = self.velocity_x * self.frame_interval_ms
        inertia_delta_y = self.velocity_y * self.frame_interval_ms
        
        # Apply decay
        self.velocity_x *= self.inertia_decay
        self.velocity_y *= self.inertia_decay
        
        # Render inertia
        if self.render_callback:
            self.render_callback(inertia_delta_x, inertia_delta_y, False)
            self._record_frame_time()
            
            self.metrics["frames_rendered"] += 1
            self.metrics["inertia_frames"] += 1
    
    def _predict_scroll_delta(self) -> Optional[Tuple[float, float]]:
        """Predict scroll delta based on velocity."""
        if abs(self.velocity_x) < 0.1 and abs(self.velocity_y) < 0.1:
            return None
        
        # Predict based on current velocity and horizon
        predicted_delta_x = self.velocity_x * self.prediction_horizon_ms
        predicted_delta_y = self.velocity_y * self.prediction_horizon_ms
        
        # Call prediction callback if available
        if self.prediction_callback:
            try:
                prediction_result = self.prediction_callback(predicted_delta_x, predicted_delta_y)
                if prediction_result:
                    return prediction_result
            except Exception as e:
                warnings.warn(f"Prediction callback error: {e}")
                self.metrics["prediction_misses"] += 1
        
        return (predicted_delta_x, predicted_delta_y)
    
    def _is_inertia_active(self) -> bool:
        """Check if inertia scrolling should be active."""
        current_time = time.time() * 1000
        time_since_last_event = current_time - self.last_velocity_update
        
        # Inertia is active if we have velocity and recent events
        has_velocity = abs(self.velocity_x) > self.min_velocity or abs(self.velocity_y) > self.min_velocity
        is_recent = time_since_last_event < 1000  # 1 second
        
        return has_velocity and is_recent and self.enable_inertia
    
    def _record_frame_time(self):
        """Record frame rendering time."""
        current_time = time.time() * 1000
        
        if self.last_render_time > 0:
            frame_time = current_time - self.last_render_time
            self.frame_times.append(frame_time)
            
            # Keep only recent history
            if len(self.frame_times) > self.max_frame_history:
                self.frame_times.pop(0)
            
            # Check for dropped frames
            expected_frame_time = 1000.0 / self.target_fps
            if frame_time > expected_frame_time * 1.5:  # 50% longer than expected
                dropped_frames = int(frame_time / expected_frame_time) - 1
                self.metrics["dropped_frames"] += max(0, dropped_frames)
        
        self.last_render_time = current_time
    
    def _adaptive_tuning(self):
        """Adaptively tune performance based on current metrics."""
        current_time = time.time()
        
        # Only adjust every 2 seconds
        if current_time - self.adaptive_settings["last_adjustment_time"] < 2.0:
            return
        
        current_fps = self.adaptive_settings["current_fps"]
        target_fps = self.target_fps
        
        if current_fps < target_fps * 0.7:  # Less than 70% of target
            # Switch to performance mode
            self.adaptive_settings["performance_mode"] = "performance"
            self.set_scroll_mode(ScrollMode.PERFORMANCE)
            self.adaptive_settings["last_adjustment_time"] = current_time
            
        elif current_fps > target_fps * 0.9:  # More than 90% of target
            # Can afford smoother scrolling
            if self.adaptive_settings["performance_mode"] == "performance":
                self.adaptive_settings["performance_mode"] = "smooth"
                self.set_scroll_mode(ScrollMode.SMOOTH)
                self.adaptive_settings["last_adjustment_time"] = current_time