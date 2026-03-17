from asyncio import run
from typing import Optional, Sequence
from httpx import AsyncClient
from app.config.settings import settings
from urllib.parse import urljoin
from datetime import date
from app.schemas.schemas import ScheduleScheme
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.stream_manager import stream_manager


aio_scheduler = AsyncIOScheduler()


async def get_today_schedules() -> Optional[Sequence[ScheduleScheme]]:
    async with AsyncClient(verify=False) as client:
        response = await client.get(
            url=urljoin(settings.CCTV_API, "api/schedule/daily"),
            params={"date": date.today()},
        )
        if response.json():
            return [ScheduleScheme.model_validate(item) for item in response.json()]
        

async def daily_job():
    today_schedules = await get_today_schedules()
    if today_schedules:
        for schedule in today_schedules:
            base = settings.media_server_rtsp_base_url.rstrip("/")
            output_url = f"{base}/{schedule.id}"

            # Start record
            aio_scheduler.add_job(
                func=stream_manager.add_stream,
                trigger="date",
                args=[
                    "source_uri", # TODO: add rtsp
                    output_url,
                    schedule.id,
                ],
                run_date=schedule.timestamp_start
            )

            # Stop record
            aio_scheduler.add_job(
                func=stream_manager.remove_stream,
                trigger="date",
                args=[schedule.id],
                run_date=schedule.timestamp_end
            )


async def main():
    print("Hello from cctv-recorder!")
    aio_scheduler.add_job(
        daily_job,
        CronTrigger(hour=0, minute=10),
        id="daily_async_job"
    )

    # Start the scheduler
    aio_scheduler.start()
    print("Scheduler started. Running event loop forever.")
    



if __name__ == "__main__":
    try:
        run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
