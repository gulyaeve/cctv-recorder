from asyncio import run, sleep
from typing import Optional, Sequence
from httpx import AsyncClient
from app.config.settings import settings
from urllib.parse import urljoin
from datetime import date
from app.schemas.schemas import ScheduleDaily
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.stream_manager import stream_manager
from app.utils.logger import log



aio_scheduler = AsyncIOScheduler()


async def get_today_schedules() -> Optional[Sequence[ScheduleDaily]]:
    async with AsyncClient(verify=False, headers={"Authorization": f"Bearer {settings.TOKEN_BEARER}"}) as client:
        response = await client.get(
            url=urljoin(settings.CCTV_API, "api/schedule/daily"),
            params={"date": date.today()},
        )
        if response.json():
            return [ScheduleDaily.model_validate(item) for item in response.json()]
        

async def daily_job():
    log.info("Started daily job")
    today_schedules = await get_today_schedules()
    if today_schedules:
        for schedule in today_schedules:
            log.info(f"Added schedule {schedule.camera_rtsp}")
            base = settings.media_server_rtsp_base_url.rstrip("/")
            output_url = f"{base}/{schedule.id}_{schedule.camera_id}"

            log.info(output_url)

            # Start record
            aio_scheduler.add_job(
                func=stream_manager.add_stream,
                trigger="date",
                args=[
                    schedule.camera_rtsp,
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
    log.info("Hello from cctv-recorder!")
    await daily_job()
    aio_scheduler.add_job(
        daily_job,
        CronTrigger(hour=0, minute=10),
        id="daily_async_job"
    )

    # Start the scheduler
    aio_scheduler.start()
    log.info("Scheduler started. Running event loop forever.")

    # Keep the main task alive indefinitely
    while True:
        await sleep(60) # Sleep for a while to avoid busy waiting



if __name__ == "__main__":
    try:
        run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
