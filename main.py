from asyncio import run, sleep
from typing import Optional, Sequence
from httpx import AsyncClient
from app.config.settings import settings
from urllib.parse import urljoin
from datetime import date
from app.schemas.schemas import ScheduleDaily
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path

# from app.services.stream_manager import stream_manager
from app.services.file_recorder import file_recorder
from app.utils.logger import log



aio_scheduler = AsyncIOScheduler()


async def get_day_schedules(day: date) -> Optional[Sequence[ScheduleDaily]]:
    async with AsyncClient(verify=False, headers={"Authorization": f"Bearer {settings.TOKEN_BEARER}"}) as client:
        response = await client.get(
            url=urljoin(settings.CCTV_API, "api/schedule_daily"),
            params={"date": day},
        )
        if response.json():
            return [ScheduleDaily.model_validate(item) for item in response.json()]
        

async def daily_job():
    log.info("Started daily job")
    current_date = date.today()

    today_schedules = await get_day_schedules(current_date)
    if today_schedules:
        for schedule in today_schedules:
            log.info(f"Added schedule for {schedule.camera_rtsp=} {schedule.id=}")
            stream_id = f"{schedule.id}_{schedule.camera_id}"

            output_dir = f"{settings.VIDEO_RECORD_PATH}/{str(current_date)}"
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)

            output_file = f"{output_dir}/{stream_id}.mp4"

            # Start record
            aio_scheduler.add_job(
                func=file_recorder.add_stream,
                trigger="date",
                args=[
                    schedule.camera_rtsp,
                    output_file,
                    stream_id,
                ],
                run_date=schedule.timestamp_start
            )

            # Stop record
            aio_scheduler.add_job(
                func=file_recorder.remove_stream,
                trigger="date",
                args=[stream_id],
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
