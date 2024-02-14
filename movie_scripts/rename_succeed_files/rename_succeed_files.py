import pathlib
import re

"""
ファイル名正規化
ソートの邪魔になるテキストを消去
"""

movie_root = [r"w:\movie\temp\succeeded", r"W:\movie\20123Q 岩合光昭の世界ネコ歩き", r"V:\movie_recorded\succeeded"]


class RenameSucceedFiles:
    @property
    def target_files(self):
        pattern = re.compile(r"\[(無|新|終|初|字|再)]")

        for root in movie_root:
            root_path = pathlib.Path(root)
            for p in root_path.glob("**/*.ts"):
                if re.search(pattern, p.name):
                    yield p, re.sub(pattern, "", p.name)


def run():
    for _file, _newname in RenameSucceedFiles().target_files:
        print(f"[RENAME] {_file} -> {_newname}")
        _file.rename(_file.with_name(_newname))


if __name__ == "__main__":
    run()
