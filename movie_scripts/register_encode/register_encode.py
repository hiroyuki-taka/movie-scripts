import asyncio
import logging
import re
import sys
from datetime import datetime, timedelta
from os.path import expanduser
from pathlib import Path
from traceback import print_exc
from typing import Iterator

import av

from movie_scripts.register_encode.ts_information import TsInformation

dir_pairs = [
    ("w:\\movie\\temp", "w:\\movie\\temp", "w:\\movie\\temp\\encoded"),
    ("v:\\movie_recorded", "v:\\movie_recorded", "v:\\movie_recorded\\out"),
    ("/srv/movie_recorded", "v:\\movie_recorded", "v:\\movie_recorded\\out"),
]

match sys.platform:
    case str() as uname if uname.startswith("linux"):
        amatsukaze_root = f"{expanduser('~')}/.local/Amatsukaze"
        use_mono = True
    case _:
        amatsukaze_root = f"{expanduser('~')}\\bin\\Amatsukaze"
        use_mono = False

logger = logging.getLogger("register_encode")
logger.setLevel(logging.INFO)


class RegisterEncode:
    def search_ts(self) -> Iterator[tuple[Path, Path, dict, str]]:
        for search_dir, in_dir, out_dir in dir_pairs:
            search_root = Path(search_dir)
            movie_root = Path(in_dir)
            output_base = Path(out_dir)

            for file in search_root.glob("**/*.ts"):
                if file.parent.name in ["succeeded", "failed", "out"]:
                    continue

                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if datetime.now() - mtime < timedelta(minutes=30):
                    # 30分以内に更新されたファイルはスキップ(録画中かも)
                    continue

                try:
                    with av.open(file) as container:
                        for stream in container.streams:
                            print(f"{stream.index: ,}, {stream.id}, name:{stream.name}, ")
                        print(f"video flame count: {len(container.streams.video)}")
                        print(f"video flame dimension: {container.streams.video[0].width}x{container.streams.video[0].height}")
                        video_width = container.streams.video[0].width

                    with TsInformation(str(file)) as ts_info:
                        title = ts_info.get("program", {}).get("title", "")

                        rel = file.relative_to(search_root)
                        win_path = movie_root.joinpath(rel)

                    yield win_path, output_base, ts_info, self.get_profile(
                        file, ts_info.get("channel"), ts_info.get("program"), video_width == 1920
                    )
                    print(str(file))
                    print("   title: {}".format(title))
                except IndexError:
                    print("エラーが発生しました。スキップします: {}".format(str(file)))
                    print_exc()

    def get_profile(self, file: Path, channel: dict, program: dict, is_full_hd: bool):
        network_id = channel.get("network_id", 0)
        filename = file.name

        if network_id == 32391:
            return "デフォルト(MX)"
        if [x for x in program.get("genre") if x.get("major") == "アニメ・特撮" and x.get("middle") in ["国内アニメ", "海外アニメ"]]:
            if network_id == 7 and len(re.findall(r"#[0-9]+", filename)) > 1:
                return "デフォルト(アニメ-ATX分割)"
            elif re.search(r"#[0-9]+,[0-9]+", filename) is not None:
                return "デフォルト(アニメ-ATX分割)"
            elif is_full_hd:
                return "デフォルト(アニメ) 810p"
            else:
                return "デフォルト(アニメ)"
        return "デフォルト(実写)"


def run():
    asyncio.run(_run())


async def _run():
    proc_list = []
    for _ts_name, _out_dir, _ts_info, _profile in RegisterEncode().search_ts():
        task = asyncio.create_task(start_subprocess(use_mono=use_mono, file=_ts_name, out_dir=_out_dir, profile=_profile))
        proc_list.append(task)

    await asyncio.gather(*proc_list)


async def start_subprocess(use_mono: bool, file: Path, out_dir: Path, profile: str):
    cmd = []
    if use_mono:
        cmd.append("mono")
    cmd.extend(
        [
            str(Path(amatsukaze_root).joinpath("exe_files", "AmatsukazeAddTask.exe")),
            "-f",
            str(file),
            "-ip",
            "192.168.0.166",
            "-p",
            "32768",
            "--priority",
            "3",
            "-o",
            str(out_dir),
            "-s",
            profile,
            "--no-move",
        ]
    )
    proc = await asyncio.create_subprocess_exec(
        cmd[0], *cmd[1:], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    print(cmd)


if __name__ == "__main__":
    av.logging.set_level(av.logging.FATAL)
    asyncio.run(_run())
