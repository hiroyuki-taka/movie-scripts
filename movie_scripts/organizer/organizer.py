import asyncio
import logging
import os
import pathlib
import re
from collections.abc import Iterator
from datetime import datetime
from enum import Enum
from functools import cache
from typing import Final, TypedDict
from zoneinfo import ZoneInfo

import aiohttp

from movie_scripts.organizer.syoboi_client import SyoboiClient

encoded_root: Final[pathlib.Path] = pathlib.Path("V:\\movie_recorded\\out")
initial_root: Final[pathlib.Path] = pathlib.Path("V:\\movie2\\Initial")
store_root: Final[pathlib.Path] = pathlib.Path("V:\\movie2\\All")
season_root: Final[pathlib.Path] = pathlib.Path("V:\\movie2\\Season")


class Channel(Enum):
    C27 = (1, "NHK総合")
    C26 = (2, "NHK Eテレ")
    C21 = (3, "フジテレビ")
    C25 = (4, "日テレ")
    C22 = (5, "TBS")
    C24 = (6, "テレビ朝日")
    C23 = (7, "テレビ東京")
    C18 = (8, "tvk")
    C30 = (13, "チバテレビ")
    C14 = (14, "テレ玉")
    BS01_2 = (15, "BSテレ東")
    BS01_1 = (16, "BS-TBS")
    BS13_1 = (17, "BSフジ")
    BS01_0 = (18, "BS朝日")
    C16 = (19, "TOKYO MX")
    CS16 = (20, "AT-X")
    BS09_0 = (128, "BS11")
    BS09_2 = (129, "BS12トゥエルビ")


class ParsedFileName(TypedDict):
    path: pathlib.Path
    group: dict[str, pathlib.Path]
    basename: str
    ch_id: str
    title: str
    date: str
    y: str
    m: str
    d: str
    hh: str
    mm: str


def log_file_list() -> Iterator[ParsedFileName]:
    for path in encoded_root.glob("**/*-enc.log"):
        if m := re.match(
            r"(?P<basename>\[(?P<ch_id>\w+)]-(?P<title>.*)-(?P<date>(?P<y>\d{4})年(?P<m>\d{2})月(?P<d>\d{2})日(?P<hh>\d{2})時(?P<mm>\d{2})分))-enc\.log$",
            path.name,
        ):
            yield ParsedFileName(**({"path": path} | m.groupdict()))


def encoded_files():
    for dirname, _, files in os.walk(top=encoded_root):
        for filename in files:
            if not filename.endswith(".mp4"):
                continue
            yield os.path.join(dirname, filename)


def find_related_file(path: pathlib.Path, basename: str):
    print(f"  root={path.parent}, pattern={basename.replace('[', '[[]')}")
    for p in path.parent.glob(f"{basename.replace('[', '[[]')}"):
        print(p)
    return {
        path.name.removeprefix(basename): path
        for path in [p for p in path.parent.glob("*") if p.name.startswith(basename)]
    }


async def run():
    _filename: ParsedFileName
    file_queue = asyncio.Queue()

    async def _q1(q: asyncio.Queue, syoboi_client: SyoboiClient):
        @cache
        def file_list(root):
            return [pathlib.Path(p) for p in os.scandir(root)]

        async def find_program(channel: str, broadcast_date: datetime):
            search_date = broadcast_date.date().replace(day=1)
            ch_id = f"C{channel}" if re.match(r"^[0-9]+$", channel) else channel
            if not hasattr(Channel, ch_id):
                return None

            channel = Channel[ch_id]

            program_dict = await syoboi_client.program_by_date(start=search_date)
            ch_programs = program_dict.get(channel.value[0])

            if ch_programs is not None:
                for p in ch_programs:
                    if p.start == broadcast_date:
                        return p
            return None

        while True:
            log_file: ParsedFileName = await q.get()
            basename = log_file.get("basename")
            path_obj = log_file.get("path")
            parent_dir = path_obj.parent

            group_files = {
                p.name.removeprefix(basename): p for p in file_list(parent_dir) if p.name.startswith(basename)
            }

            broadcast_date = datetime(
                year=int(log_file.get("y")),
                month=int(log_file.get("m")),
                day=int(log_file.get("d")),
                hour=int(log_file.get("hh")),
                minute=int(log_file.get("mm")),
                second=0,
                tzinfo=ZoneInfo("Asia/Tokyo"),
            )

            try:
                program = await find_program(log_file.get("ch_id"), broadcast_date=broadcast_date)
                if program is not None and (count := program.Count) is not None:
                    title = program.Title
                    sub_title = program.SubTitle
                    new_title = f"{program.q_season} {title}"
                    new_base_name = f"[{log_file.get('ch_id')}] #{count:02} {sub_title}-{log_file.get('date')}"

                    print("------------------------------")
                    # allに移動
                    for ext, file in group_files.items():
                        move_to = store_root / new_title / f"{new_base_name}{ext}"
                        print(f"mkdir: {move_to.parent}")
                        os.makedirs(move_to.parent, exist_ok=True)
                        print(f"move: {file}")
                        print(f"  -> {move_to}")

                    # initialにリンク作成
                    initial_path = initial_root / program.TitleInitial
                    print(f"mkdir: {initial_path}")
                    os.makedirs(initial_path, exist_ok=True)
                    print(f"link: {initial_path / new_title} -> {store_root / new_title}")

                    # seasonにリンク作成
                    season_path = season_root / program.y / program.q
                    print(f"mkdir: {season_path}")
                    os.makedirs(season_path, exist_ok=True)
                    print(f"link: {season_path / new_title} -> {store_root / new_title}")
            finally:
                q.task_done()

    async with aiohttp.ClientSession() as session:
        syoboi_client = SyoboiClient(session)

        for c, _filename in enumerate(log_file_list()):
            file_queue.put_nowait(_filename)

        tasks = []
        tasks.append(asyncio.create_task(_q1(file_queue, syoboi_client)))
        # tasks.append(asyncio.create_task(_p1(file_queue)))

        await file_queue.join()

        # あとしまつ
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    asyncio.run(run())
