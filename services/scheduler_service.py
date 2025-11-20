"""Scheduler service for follow-up messages using APScheduler."""

from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from utils.logging_config import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Service for scheduling follow-up messages."""

    def __init__(self, database_url: str = "sqlite:///./sales_bot.db"):
        """
        Initialize scheduler service.

        Args:
            database_url: Database URL for job persistence
        """
        # Convert async SQLite URL to sync URL for APScheduler
        # APScheduler's SQLAlchemyJobStore doesn't support aiosqlite
        sync_database_url = database_url.replace("sqlite+aiosqlite:", "sqlite:")

        # Configure job store
        jobstores = {
            "default": SQLAlchemyJobStore(url=sync_database_url)
        }

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)
        self.scheduler.start()

        logger.info(f"Scheduler service initialized and started with {sync_database_url}")

    async def add_follow_up_job(
        self,
        job_id: str,
        phone: str,
        message: str,
        scheduled_time: datetime,
        send_function,
    ) -> str:
        """
        Schedule a follow-up message.

        Args:
            job_id: Unique job identifier
            phone: Recipient phone number
            message: Message to send
            scheduled_time: When to send the message
            send_function: Async function to call for sending message

        Returns:
            Job ID
        """
        try:
            # Remove existing job with same ID if exists
            existing_job = self.scheduler.get_job(job_id)
            if existing_job:
                logger.info(f"Removing existing job: {job_id}")
                self.scheduler.remove_job(job_id)

            # Schedule new job
            self.scheduler.add_job(
                send_function,
                "date",
                run_date=scheduled_time,
                args=[phone, message],
                id=job_id,
                replace_existing=True,
            )

            logger.info(f"Scheduled follow-up job {job_id} for {scheduled_time}")
            return job_id

        except Exception as e:
            logger.error(f"Error scheduling follow-up job: {e}")
            raise

    def cancel_follow_up_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled follow-up job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if job not found
        """
        try:
            existing_job = self.scheduler.get_job(job_id)
            if existing_job:
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled follow-up job: {job_id}")
                return True
            else:
                logger.warning(f"Job not found for cancellation: {job_id}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling follow-up job: {e}")
            return False

    def get_job_info(self, job_id: str) -> Optional[dict]:
        """
        Get information about a scheduled job.

        Args:
            job_id: Job ID

        Returns:
            Job info dict or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    "id": job.id,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger),
                }
            return None

        except Exception as e:
            logger.error(f"Error getting job info: {e}")
            return None

    def get_all_jobs(self) -> list:
        """
        Get all scheduled jobs.

        Returns:
            List of job info dicts
        """
        try:
            jobs = self.scheduler.get_jobs()
            return [
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger),
                }
                for job in jobs
            ]
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return []

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler service shut down")


# Global instance (will be initialized in app.py)
scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    global scheduler_service
    if scheduler_service is None:
        scheduler_service = SchedulerService()
    return scheduler_service
