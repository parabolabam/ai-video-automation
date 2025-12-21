"""
Async Scheduler Service for managing cron jobs
Uses APScheduler for robust job scheduling
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
import asyncio

from features.platform.runner import DynamicWorkflowRunner

logger = logging.getLogger(__name__)

class SchedulerService:
    """Singleton service for managing scheduled jobs"""

    _instance: Optional['SchedulerService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.scheduler = AsyncIOScheduler()
        self._initialized = True
        logger.info("Scheduler service initialized")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")

    async def _run_workflow_job(self, workflow_id: str, user_id: str, input_text: str):
        """Execute a workflow as a scheduled job"""
        try:
            logger.info(f"Running scheduled workflow: {workflow_id} for user {user_id}")
            runner = DynamicWorkflowRunner(workflow_id, user_id)
            result = await runner.run(input_text)
            logger.info(f"Scheduled workflow {workflow_id} completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled workflow {workflow_id} failed: {e}")

    def add_cron_job(
        self,
        job_id: str,
        workflow_id: str,
        user_id: str,
        input_text: str,
        cron_expression: str,
        replace_existing: bool = True
    ) -> Job:
        """
        Add a cron job to run a workflow on a schedule

        Args:
            job_id: Unique identifier for the job
            workflow_id: ID of the workflow to run
            user_id: User ID who owns this job
            cron_expression: Cron expression (e.g., "0 */6 * * *" for every 6 hours)
            input_text: Input to pass to the workflow
            replace_existing: Whether to replace if job_id already exists

        Returns:
            The created Job instance
        """
        # Parse cron expression
        # Format: minute hour day month day_of_week
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}. Expected 5 parts (minute hour day month day_of_week)")

        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )

        job = self.scheduler.add_job(
            self._run_workflow_job,
            trigger=trigger,
            args=[workflow_id, user_id, input_text],
            id=job_id,
            name=f"Workflow {workflow_id} for user {user_id}",
            replace_existing=replace_existing,
            # Store metadata for later retrieval
            kwargs={},
            misfire_grace_time=3600  # 1 hour grace period for missed jobs
        )

        # Store metadata in job's jobstore
        job.modify(kwargs={
            'workflow_id': workflow_id,
            'user_id': user_id,
            'input_text': input_text,
            'cron_expression': cron_expression
        })

        logger.info(f"Added cron job {job_id}: workflow={workflow_id}, schedule={cron_expression}")
        return job

    def add_interval_job(
        self,
        job_id: str,
        workflow_id: str,
        user_id: str,
        input_text: str,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        replace_existing: bool = True
    ) -> Job:
        """
        Add an interval-based job to run a workflow periodically

        Args:
            job_id: Unique identifier for the job
            workflow_id: ID of the workflow to run
            user_id: User ID who owns this job
            input_text: Input to pass to the workflow
            hours: Run every N hours
            minutes: Run every N minutes
            seconds: Run every N seconds
            replace_existing: Whether to replace if job_id already exists

        Returns:
            The created Job instance
        """
        if hours == 0 and minutes == 0 and seconds == 0:
            raise ValueError("Must specify at least one interval (hours, minutes, or seconds)")

        trigger = IntervalTrigger(
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

        job = self.scheduler.add_job(
            self._run_workflow_job,
            trigger=trigger,
            args=[workflow_id, user_id, input_text],
            id=job_id,
            name=f"Workflow {workflow_id} for user {user_id}",
            replace_existing=replace_existing,
            kwargs={
                'workflow_id': workflow_id,
                'user_id': user_id,
                'input_text': input_text,
                'interval_hours': hours,
                'interval_minutes': minutes,
                'interval_seconds': seconds
            },
            misfire_grace_time=3600
        )

        logger.info(f"Added interval job {job_id}: workflow={workflow_id}, interval={hours}h{minutes}m{seconds}s")
        return job

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job

        Args:
            job_id: ID of the job to remove

        Returns:
            True if job was removed, False if job not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job (stop it from running, but keep it in the scheduler)

        Args:
            job_id: ID of the job to pause

        Returns:
            True if job was paused, False if job not found
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job

        Args:
            job_id: ID of the job to resume

        Returns:
            True if job was resumed, False if job not found
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to resume job {job_id}: {e}")
            return False

    def trigger_job(self, job_id: str) -> bool:
        """
        Manually trigger a job to run immediately (doesn't affect schedule)

        Args:
            job_id: ID of the job to trigger

        Returns:
            True if job was triggered, False if job not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                # Manually trigger the job
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered job {job_id}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to trigger job {job_id}: {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific job

        Args:
            job_id: ID of the job

        Returns:
            Dict with job information or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None

            return self._job_to_dict(job)
        except Exception as e:
            logger.warning(f"Failed to get job {job_id}: {e}")
            return None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Get information about all scheduled jobs

        Returns:
            List of dicts with job information
        """
        jobs = self.scheduler.get_jobs()
        return [self._job_to_dict(job) for job in jobs]

    def get_jobs_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific user

        Args:
            user_id: User ID to filter by

        Returns:
            List of dicts with job information for this user
        """
        all_jobs = self.get_all_jobs()
        return [job for job in all_jobs if job.get('user_id') == user_id]

    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert a Job instance to a dict with useful information"""
        # Extract metadata from job kwargs
        workflow_id = job.kwargs.get('workflow_id', 'unknown')
        user_id = job.kwargs.get('user_id', 'unknown')
        input_text = job.kwargs.get('input_text', '')
        cron_expression = job.kwargs.get('cron_expression')
        interval_hours = job.kwargs.get('interval_hours')
        interval_minutes = job.kwargs.get('interval_minutes')
        interval_seconds = job.kwargs.get('interval_seconds')

        # Determine schedule type and description
        schedule_type = 'cron' if cron_expression else 'interval'
        if cron_expression:
            schedule_description = cron_expression
        else:
            parts = []
            if interval_hours:
                parts.append(f"{interval_hours}h")
            if interval_minutes:
                parts.append(f"{interval_minutes}m")
            if interval_seconds:
                parts.append(f"{interval_seconds}s")
            schedule_description = " ".join(parts) if parts else "unknown"

        return {
            'job_id': job.id,
            'name': job.name,
            'workflow_id': workflow_id,
            'user_id': user_id,
            'input_text': input_text,
            'schedule_type': schedule_type,
            'schedule': schedule_description,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'paused': job.next_run_time is None,
            'trigger': str(job.trigger),
        }


# Global scheduler instance
_scheduler_service: Optional[SchedulerService] = None

def get_scheduler() -> SchedulerService:
    """Get the global scheduler service instance"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
