"""
Vwire Timer Module

Provides timer functionality
Allows scheduling periodic tasks with millisecond precision.
"""

import time
import threading
from typing import Callable, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class TimerTask:
    """Represents a scheduled timer task."""
    id: int
    interval_ms: int
    callback: Callable[[], None]
    last_run: float = 0.0
    enabled: bool = True
    run_count: int = 0
    max_runs: int = 0  # 0 = unlimited


class VwireTimer:
    """
    Timer class for scheduling periodic tasks.
    
    This allows scheduling multiple 
    callbacks to run at specified intervals.
    
    Example:
        timer = VwireTimer()
        
        def send_temperature():
            temp = read_sensor()
            device.virtual_send(0, temp)
        
        def check_buttons():
            # Check button states
            pass
        
        # Run send_temperature every 2 seconds
        timer.set_interval(2000, send_temperature)
        
        # Run check_buttons every 100ms
        timer.set_interval(100, check_buttons)
        
        # Main loop
        while True:
            timer.run()
            time.sleep(0.001)  # Small delay to prevent CPU hogging
    
    Thread-Safe Usage:
        timer = VwireTimer()
        timer.start()  # Starts background thread
        
        # Timer runs automatically
        # ... your code ...
        
        timer.stop()  # Stop timer thread
    """
    
    MAX_TIMERS = 16  # Maximum number of timers (like Arduino BlynkTimer)
    
    def __init__(self):
        """Initialize the timer."""
        self._tasks: Dict[int, TimerTask] = {}
        self._next_id = 0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def set_interval(
        self, 
        interval_ms: int, 
        callback: Callable[[], None],
        max_runs: int = 0
    ) -> int:
        """
        Schedule a callback to run at a regular interval.
        
        Args:
            interval_ms: Interval in milliseconds
            callback: Function to call
            max_runs: Maximum number of runs (0 = unlimited)
            
        Returns:
            Timer ID that can be used to modify or delete the timer
            
        Raises:
            RuntimeError: If maximum number of timers exceeded
            
        Example:
            # Run every 5 seconds
            timer_id = timer.set_interval(5000, my_function)
            
            # Run 10 times, then stop
            timer_id = timer.set_interval(1000, my_function, max_runs=10)
        """
        with self._lock:
            if len(self._tasks) >= self.MAX_TIMERS:
                raise RuntimeError(f"Maximum number of timers ({self.MAX_TIMERS}) exceeded")
            
            timer_id = self._next_id
            self._next_id += 1
            
            self._tasks[timer_id] = TimerTask(
                id=timer_id,
                interval_ms=interval_ms,
                callback=callback,
                last_run=time.time() * 1000,
                max_runs=max_runs
            )
            
            return timer_id
    
    def set_timeout(self, timeout_ms: int, callback: Callable[[], None]) -> int:
        """
        Schedule a callback to run once after a delay.
        
        Args:
            timeout_ms: Delay in milliseconds
            callback: Function to call
            
        Returns:
            Timer ID
            
        Example:
            # Run once after 5 seconds
            timer.set_timeout(5000, my_function)
        """
        return self.set_interval(timeout_ms, callback, max_runs=1)
    
    def delete_timer(self, timer_id: int) -> bool:
        """
        Delete a timer by ID.
        
        Args:
            timer_id: Timer ID returned by set_interval/set_timeout
            
        Returns:
            True if timer was deleted, False if not found
        """
        with self._lock:
            if timer_id in self._tasks:
                del self._tasks[timer_id]
                return True
            return False
    
    def enable_timer(self, timer_id: int) -> bool:
        """
        Enable a timer.
        
        Args:
            timer_id: Timer ID
            
        Returns:
            True if timer was enabled, False if not found
        """
        with self._lock:
            if timer_id in self._tasks:
                self._tasks[timer_id].enabled = True
                return True
            return False
    
    def disable_timer(self, timer_id: int) -> bool:
        """
        Disable a timer (keeps it but doesn't run).
        
        Args:
            timer_id: Timer ID
            
        Returns:
            True if timer was disabled, False if not found
        """
        with self._lock:
            if timer_id in self._tasks:
                self._tasks[timer_id].enabled = False
                return True
            return False
    
    def change_interval(self, timer_id: int, interval_ms: int) -> bool:
        """
        Change the interval of an existing timer.
        
        Args:
            timer_id: Timer ID
            interval_ms: New interval in milliseconds
            
        Returns:
            True if interval was changed, False if timer not found
        """
        with self._lock:
            if timer_id in self._tasks:
                self._tasks[timer_id].interval_ms = interval_ms
                return True
            return False
    
    def restart_timer(self, timer_id: int) -> bool:
        """
        Restart a timer (reset its last run time).
        
        Args:
            timer_id: Timer ID
            
        Returns:
            True if timer was restarted, False if not found
        """
        with self._lock:
            if timer_id in self._tasks:
                self._tasks[timer_id].last_run = time.time() * 1000
                self._tasks[timer_id].run_count = 0
                return True
            return False
    
    def get_num_timers(self) -> int:
        """Get the number of active timers."""
        with self._lock:
            return len(self._tasks)
    
    def run(self) -> int:
        """
        Run all due timers. Call this in your main loop.
        
        Returns:
            Number of timers that were executed
            
        Example:
            while True:
                timer.run()
                device.run()  # Also run Vwire event loop
                time.sleep(0.001)
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        executed = 0
        timers_to_delete: List[int] = []
        
        with self._lock:
            tasks_snapshot = list(self._tasks.values())
        
        for task in tasks_snapshot:
            if not task.enabled:
                continue
            
            elapsed = current_time - task.last_run
            
            if elapsed >= task.interval_ms:
                try:
                    task.callback()
                    task.run_count += 1
                    executed += 1
                except Exception as e:
                    print(f"Timer {task.id} error: {e}")
                
                task.last_run = current_time
                
                # Check if max runs reached
                if task.max_runs > 0 and task.run_count >= task.max_runs:
                    timers_to_delete.append(task.id)
        
        # Clean up completed timers
        for timer_id in timers_to_delete:
            self.delete_timer(timer_id)
        
        return executed
    
    def start(self, interval_ms: int = 10) -> None:
        """
        Start the timer in a background thread.
        
        Args:
            interval_ms: How often to check timers (default: 10ms)
            
        Example:
            timer.start()
            # Timer now runs automatically in background
        """
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(interval_ms,),
            daemon=True,
            name="VwireTimer"
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the background timer thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
    
    def _run_loop(self, interval_ms: int) -> None:
        """Internal timer loop for background thread."""
        while self._running:
            self.run()
            time.sleep(interval_ms / 1000)
    
    def clear(self) -> None:
        """Delete all timers."""
        with self._lock:
            self._tasks.clear()
    
    @property
    def is_running(self) -> bool:
        """Check if background timer thread is running."""
        return self._running
