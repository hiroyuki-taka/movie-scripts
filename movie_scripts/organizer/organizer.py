import asyncio
import os
import pathlib
import re
from collections.abc import Iterator
from functools import cache
from typing import Final, TypedDict

encoded_root: Final[pathlib.Path] = pathlib.Path(r"w:\movie_temp\encoded")


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

    async def _q1(q: asyncio.Queue):
        @cache
        def file_list(root):
            return [pathlib.Path(p) for p in os.scandir(root)]

        while True:
            log_file: ParsedFileName = await q.get()
            basename = log_file.get("basename")
            path_obj = log_file.get("path")
            parent_dir = path_obj.parent
            print(f" {log_file['path']} - {parent_dir}")

            group_files = {
                p.name.removeprefix(basename): p
                for p in file_list(parent_dir)
                if p.name.startswith(basename) and p != path_obj
            }

            print(group_files)

            q.task_done()

    for c, _filename in enumerate(log_file_list()):
        file_queue.put_nowait(_filename)

    tasks = []
    tasks.append(asyncio.create_task(_q1(file_queue)))
    # tasks.append(asyncio.create_task(_p1(file_queue)))

    await file_queue.join()

    # あとしまつ
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(run())
