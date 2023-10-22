import os
import pathlib
import re
from collections.abc import Iterator
from typing import Final, TypedDict, Iterable

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

def log_file_list()-> Iterable[ParsedFileName]:
    for path in encoded_root.glob("**/*-enc.log"):
        if m := re.match(r"(?P<basename>\[(?P<ch_id>\w+)]-(?P<title>.*)-(?P<date>(?P<y>\d{4})年(?P<m>\d{2})月(?P<d>\d{2})日(?P<hh>\d{2})時(?P<mm>\d{2})分))-enc\.log$", path.name):
            yield ParsedFileName({"path": path} | m.groupdict())

def encoded_files():
    for dirname, _, files in os.walk(top=encoded_root):
        for filename in files:
            if not filename.endswith(".mp4"):
                continue
            yield os.path.join(dirname, filename)


def run():
    _filename: ParsedFileName
    for c, _filename in enumerate(log_file_list()):
        print(f"{c}: {_filename}")
        pass


if __name__ == "__main__":
    run()
