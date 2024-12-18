from django.db import models
from django.utils import timezone
from enum import Enum
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    MYTHIC_RARE = "mythic"

class TaskState(str, Enum):
    """Explicit states for task processing."""
    QUEUED = "queued"         # Task is in queue
    GENERATING = "generating" # Generating card data
    CREATING_IMAGE = "creating_image" # Creating card image
    SAVING = "saving"         # Saving to database
    COMPLETED = "completed"   # Task completed successfully
    FAILED = "failed"         # Task failed
    NOT_FOUND = "not_found"   # Task doesn't exist

class Task(models.Model):
    """Represents a card generation task."""
    task_id = models.CharField(max_length=255, primary_key=True)
    user_id = models.CharField(max_length=255)
    rarity = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, choices=[(tag.name, tag.value) for tag in TaskState], default=TaskState.QUEUED)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    card_id = models.CharField(max_length=255, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    def update_state(self, new_state: TaskState, error: Optional[str] = None) -> None:
        """Update task state with logging."""
        old_state = self.state
        self.state = new_state
        self.updated_at = timezone.now()
        if error:
            self.error = error
        if new_state == TaskState.COMPLETED:
            self.completed_at = self.updated_at
        logger.info(f"Task {self.task_id} state changed: {old_state} -> {new_state}")
        self.save()

    class Meta:
        app_label = 'myapp'