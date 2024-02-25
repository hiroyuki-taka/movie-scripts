import os
import pathlib
import re
from collections.abc import Iterator
from typing import Final, TypedDict

encoded_root: Final[pathlib.Path] = pathlib.Path(r"w:\movie_temp\encoded")


class ParsedFileName(TypedDict):
    path: pathlib.Path
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
            path.name):
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
        path.name.removeprefix(basename): path for path in
        [p for p in path.parent.glob("*") if p.name.startswith(basename)]
    }


async def run():
    _filename: ParsedFileName
    for c, _filename in enumerate(log_file_list()):
        print(f"{c}: {_filename.get('path').parent}, {_filename.get('basename')}")
        x = find_related_file(_filename.get("path"), _filename.get("basename"))
        # for k, v in x.items():
        #     print(f"  {k}: {v}")


if __name__ == "__main__":
    run()
