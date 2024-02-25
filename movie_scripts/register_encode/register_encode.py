import asyncio
import logging
import re
import sys
from datetime import datetime, timedelta
from os.path import expanduser
from pathlib import Path
from typing import Iterator

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
                    ts_info = TsInformation(str(file)).extract()
                    title = ts_info.get("program", {}).get("title", "")

                    print("origin: {}".format(title))

                    rel = file.relative_to(search_root)
                    win_path = movie_root.joinpath(rel)

                    yield win_path, output_base, ts_info, self.get_profile(
                        file, ts_info.get("channel"), ts_info.get("program")
                    )
                except IndexError:
                    print("エラーが発生しました。スキップします: {}".format(str(file)))

    def get_profile(self, file: Path, channel: dict, program: dict):
        network_id = channel.get("network_id", 0)
        filename = file.name

        if network_id == 32391:
            return "デフォルト(MX)"
        if [x for x in program.get("genre") if x.get("major") == "アニメ・特撮" and x.get("middle") in ["国内アニメ", "海外アニメ"]]:
            if network_id == 7 and len(re.findall(r"#[0-9]+", filename)) > 1:
                return "デフォルト(アニメ-ATX分割)"
            elif re.search(r"#[0-9]+,[0-9]+", filename) is not None:
                return "デフォルト(アニメ-ATX分割)"
            elif (
                "水星の魔女" in filename or "推しの子" in filename or "青春ブタ野郎" in filename or channel.get("channel_type") == "BS"
            ):
                return "デフォルト(アニメ) 810p"
            else:
                return "デフォルト(アニメ)"
        return "デフォルト(実写)"


def run():
    asyncio.run(_run())


async def _run():
    proc_list = []
    for _ts_name, _out_dir, _ts_info, _profile in RegisterEncode().search_ts():
        proc_list.append(start_subprocess(use_mono=use_mono, file=_ts_name, out_dir=_out_dir, profile=_profile))

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
    asyncio.run(_run())
