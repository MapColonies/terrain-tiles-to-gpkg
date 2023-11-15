import watchdog
from src.utils import patterns_match
from src.constants import TEMP_FILES_PATTERNS
import logging

logger = logging.getLogger(__name__)

class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, watch_patterns, event_queue):
        super().__init__(patterns=watch_patterns, ignore_directories=True, case_sensitive=False)
        self.event_queue = event_queue
        self.watch_patterns = watch_patterns

    def on_moved(self, event):
        src_path, dest_path = event.src_path, event.dest_path
        logger.debug(f"File moved: {src_path} to {dest_path}")
        if patterns_match(src_path, TEMP_FILES_PATTERNS) and patterns_match(dest_path, self.watch_patterns):
            self.event_queue.put(dest_path)

    def on_created(self, event):
        src_path = event.src_path
        logger.debug(f"File created: {src_path}")
        if not patterns_match(src_path, TEMP_FILES_PATTERNS) and patterns_match(src_path, self.watch_patterns):
            self.event_queue.put(src_path)

    def on_closed(self, event):
        closed_file_path = event.src_path
        logger.debug(f"File closed: {closed_file_path}")
        self.event_queue.put(closed_file_path)
