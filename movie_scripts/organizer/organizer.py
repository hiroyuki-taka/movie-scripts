import os
import pathlib
import re

encoded_root = pathlib.Path(r"w:\movie_temp\encoded")

def log_file_list():
    for path in encoded_root.glob("**/*-enc.log"):
        if m := re.match(r"(?P<basename>\[(?P<ch_id>\w+)]-(?P<title>.*)-(?P<date>(?P<y>\d{4})年(?P<m>\d{2})月(?P<d>\d{2})日(?P<hh>\d{2})時(?P<mm>\d{2})分))-enc\.log$", path.name):
            print(m.groupdict())
            yield path

def encoded_files():
    for dirname, _, files in os.walk(top=encoded_root):
        for filename in files:
            if not filename.endswith(".mp4"):
                continue
            yield os.path.join(dirname, filename)


def run():
    for c, _filename in enumerate(log_file_list()):
        print(f"{c}: {_filename}")


if __name__ == "__main__":
    run()
