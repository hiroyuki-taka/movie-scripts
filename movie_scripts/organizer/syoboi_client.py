import asyncio
import re
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass, Field, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

import aiohttp
from async_lru import alru_cache


@dataclass
class Title:
    TID: str
    Title: str
    TitleYomi: str
    Cat: str
    FirstCh: str
    FirstYear: int
    FirstMonth: int
    FirstEndYear: int | None
    FirstEndMonth: int | None
    TitleFlag: int
    Keywords: str
    SubTitles: str
    UserPoint: int
    UserPointRank: int
    TitleViewCount: int
    Comment: str
    ShortTitle: str
    TitleEN: str

    subtitles: dict[int, str] = field(init=False)

    def __post_init__(self):
        pattern = re.compile(r"\*(\d+)\*(.*)$")
        subtitles = self.SubTitles.split("\r\n")
        self.subtitles = {int(m.group(1)): m.group(2) for line in subtitles if (m := re.match(pattern, line))}


@dataclass
class Program:
    PID: int
    TID: str
    ChID: int
    ChName: str
    ChEPGURL: str
    Count: int | None
    StTime: int
    EdTime: int
    SubTitle2: str
    ProgComment: str
    ConfFlag: str | None

    start: datetime = field(init=False)
    end: datetime = field(init=False)

    def __post_init__(self):
        self.start = datetime.fromtimestamp(int(self.StTime), ZoneInfo("Asia/Tokyo"))
        self.end = datetime.fromtimestamp(int(self.EdTime), ZoneInfo("Asia/Tokyo"))
        self.Count = int(self.Count) if self.Count else None
        self.ChID = int(self.ChID)


@dataclass
class P:
    ChName: str
    Count: int | None
    Title: str
    SubTitle: str
    TitleInitial: str

    ChID: int
    start: datetime
    end: datetime

    TitleYomi: str
    TID: str


class SyoboiClient:
    def __init__(self, session):
        self.sem = asyncio.Semaphore()
        self.session = session

    @alru_cache()
    async def program_by_date(self, start: date, days=31) -> dict[int, list[P]]:
        async with self.sem:
            parameter_dict = {"Req": "ProgramByDate,TitleFull", "start": start.strftime("%Y-%m-%d"), "days": days}

            try:
                result = defaultdict(list)

                async with self.session.get(
                    f"https://cal.syoboi.jp/json?{urllib.parse.urlencode(parameter_dict)}"
                ) as response:
                    response_json = await response.json()

                    titles = response_json.get("Titles")
                    programs = response_json.get("Programs")

                    all_title: dict[str, Title] = dict()
                    for title_dict in titles.values():
                        title = Title(**title_dict)
                        all_title[title.TID] = title

                    for program_dict in programs.values():
                        program = Program(**program_dict)
                        if title := all_title.get(program.TID):
                            initial_base = title.TitleYomi
                            if not initial_base and re.match("^[\u3041-\u309F]+", title.Title):  # titleYomiが入ってないもの救済
                                initial_base = title.Title

                            if initial_base:
                                if initial_base.startswith("う゛"):
                                    initial = "ゔ"
                                else:
                                    initial = initial_base[0]
                            else:
                                initial = None

                            p_dict = {
                                "ChID": program.ChID,
                                "ChName": program.ChName,
                                "Count": program.Count,
                                "start": program.start,
                                "end": program.end,
                                "Title": title.Title,
                                "TitleInitial": initial,
                                "TitleYomi": title.TitleYomi,
                                "SubTitle": title.subtitles.get(program.Count, ""),
                                "TID": program.TID,
                            }
                            result[program.ChID].append(P(**p_dict))
                for l in result.values():
                    l.sort(key=lambda p: (p.TID, p.Count if p.Count else 0))
                return result
            finally:
                await asyncio.sleep(1)


if __name__ == "__main__":

    async def x():
        async with aiohttp.ClientSession() as session:
            for chid, x in (
                await SyoboiClient(session=session).program_by_date(start=date.today().replace(day=1), days=31)
            ).items():
                print(chid)
                for _x in x:
                    print(f"{id(_x)},{_x}")

    asyncio.run(x())
