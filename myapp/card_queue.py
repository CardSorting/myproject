from typing import Dict, Any, Optional, List, Deque
from collections import deque
import asyncio
from datetime import datetime
import logging
import json
from enum import Enum, auto
from myapp.card_service import generate_card_wrapper
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from django.conf import settings
from myapp.models import Task, TaskState
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from cards.models import Card

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CardGenerationError(Exception):
    """Base exception for card generation errors."""
    def __init__(self, message: str, state: TaskState):
        self.message = message
        self.state = state
        super().__init__(message)

class QueueFullError(CardGenerationError):
    """Raised when the queue is at capacity."""
    def __init__(self):
        super().__init__("Queue is at capacity", TaskState.FAILED)

class TaskNotFoundError(CardGenerationError):
    """Raised when a task is not found."""
    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} not found", TaskState.NOT_FOUND)

class CardGenerationQueue:
    def __init__(self, max_queue_size: int = 100, max_concurrent_tasks: int = 3):
        self.queue: Deque[Task] = deque(maxlen=max_queue_size)
        self.processing: Dict[str, Task] = {}
        self.completed: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._stop_event = asyncio.Event()
        
    async def add_to_queue(self, task_id: str, user_id: str, rarity: Optional[str] = None) -> str:
        """Add a card generation task to the queue."""
        try:
            if len(self.queue) >= self.queue.maxlen:
                raise QueueFullError()
                
            async with self._lock:
                task = Task.objects.create(
                    task_id=task_id,
                    user_id=user_id,
                    rarity=rarity,
                    state=TaskState.QUEUED
                )
                self.queue.append(task)
                logger.info(f"Added task {task_id} to queue. Queue size: {len(self.queue)}")
                return task_id
        except QueueFullError:
            raise
        except Exception as e:
            logger.error(f"Error adding task to queue: {e}")
            raise CardGenerationError(str(e), TaskState.FAILED)
            
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task."""
        try:
            # Check processing tasks
            if task_id in self.processing:
                return self.processing[task_id].__dict__
                
            # Check completed tasks
            if task_id in self.completed:
                return self.completed[task_id].__dict__
                
            # Check queue
            for task in self.queue:
                if task.task_id == task_id:
                    return task.__dict__
            
            # Check database
            task = Task.objects.filter(task_id=task_id).first()
            if task:
                return task.__dict__
                    
            raise TaskNotFoundError(task_id)
            
        except TaskNotFoundError as e:
            return {'state': e.state, 'task_id': task_id}
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {
                'state': TaskState.FAILED,
                'task_id': task_id,
                'error': 'Failed to get task status'
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _generate_card(self, task: Task) -> None:
        """Generate a card with retries."""
        try:
            task.update_state(TaskState.GENERATING)
            
            # Generate card data
            card_data = generate_card_wrapper(task.rarity)
            
            task.update_state(TaskState.SAVING)
            
            # Create card in database
            Card.objects.create(
                name=card_data['name'],
                manaCost=card_data.get('manaCost'),
                type=card_data['type'],
                abilities=card_data.get('abilities'),
                flavorText=card_data.get('flavorText'),
                rarity=card_data['rarity'],
                set_name=card_data['set_name'],
                card_number=card_data['card_number'],
                powerToughness=card_data.get('powerToughness'),
            )
            
        except Exception as e:
            logger.error(f"Error generating card: {e}")
            raise

    async def process_next(self) -> Optional[Dict[str, Any]]:
        """Process the next card in the queue."""
        async with self._lock:
            if not self.queue:
                return None
                
            task = self.queue.popleft()
            self.processing[task.task_id] = task
            
        try:
            async with self._semaphore:
                try:
                    await self._generate_card(task)
                    task.update_state(TaskState.COMPLETED)
                    
                except RetryError as e:
                    task.update_state(TaskState.FAILED, "Maximum retries exceeded")
                    
                except Exception as e:
                    task.update_state(TaskState.FAILED, str(e))
                
                # Move to completed
                self.completed[task.task_id] = task
                return task.__dict__
                
        finally:
            # Always clean up processing state
            if task.task_id in self.processing:
                del self.processing[task.task_id]
            
    async def process_queue(self) -> None:
        """Continuously process the queue."""
        while not self._stop_event.is_set():
            try:
                if self.queue:
                    await self.process_next()
                await asyncio.sleep(1)  # Prevent CPU overuse
            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(5)  # Back off on error
            
    def clean_old_results(self, max_age_hours: int = 24) -> None:
        """Clean up old results."""
        try:
            current_time = timezone.now()
            to_remove = []
            
            for task_id, task in self.completed.items():
                if task.completed_at and (current_time - task.completed_at).total_seconds() > max_age_hours * 3600:
                    to_remove.append(task_id)
                    
            for task_id in to_remove:
                del self.completed[task_id]
                Task.objects.filter(task_id=task_id).delete()
                
        except Exception as e:
            logger.error(f"Error cleaning old results: {e}")

    async def shutdown(self) -> None:
        """Gracefully shut down the queue."""
        self._stop_event.set()
        # Wait for current processing to complete
        if self.processing:
            await asyncio.sleep(5)

# Create global queue instance
card_queue = CardGenerationQueue()

# Background task to process queue
async def run_queue_processor() -> None:
    try:
        await card_queue.process_queue()
    except Exception as e:
        logger.error(f"Queue processor error: {e}")
        # Attempt to restart the processor
        await asyncio.sleep(5)
        await run_queue_processor()

# Function to start queue processor
def start_queue_processor() -> None:
    """Start the queue processor as a Django background task."""
    from background_task import background
    
    @background(schedule=0)
    def run_processor():
        import asyncio
        asyncio.run(run_queue_processor())
    
    run_processor()

# Function to clean old results periodically
def clean_old_results() -> None:
    """Clean old results as a Django background task."""
    from background_task import background
    
    @background(schedule=3600)  # Run every hour
    def run_cleanup():
        card_queue.clean_old_results()
    
    run_cleanup()