from asyncio import run
from httpx import AsyncClient
from app.config.settings import settings
from urllib.parse import urljoin
from datetime import date
from app.schemas.schemas import ScheduleScheme


async def main():
    print("Hello from cctv-recorder!")
    async with AsyncClient(verify=False) as client:
        url = urljoin(settings.CCTV_API, "api/schedule/daily")
        # print(url)
        response = await client.get(url, params={"date": date.today()})
        # print(response.json())
        for item in response.json():
            schedule = ScheduleScheme.model_validate(item)
            print(schedule)



if __name__ == "__main__":
    run(main())
