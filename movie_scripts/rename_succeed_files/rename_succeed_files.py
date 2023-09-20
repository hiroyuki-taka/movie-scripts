import os
import re

"""
ファイル名正規化
ソートの邪魔になるテキストを消去
"""

movie_root = [r"w:\movie\temp\succeeded", r"W:\movie\20123Q 岩合光昭の世界ネコ歩き"]


class RenameSucceedFiles:
    @property
    def target_files(self):
        pattern = re.compile(r"\[無]|\[新]|\[終]|\[初]|\[字]")

        for root in movie_root:
            for dirname, _, files in os.walk(top=root):
                for file in files:
                    if dirname.endswith("succeeded") and file.endswith(".ts") and re.search(pattern, file):
                        yield dirname, file, re.sub(pattern, "", file)
                        continue

                    if re.search(pattern, file):
                        yield dirname, file, re.sub(pattern, "", file)
                        continue

def run():
    for _dirname, _file, _newname in RenameSucceedFiles().target_files:
        print(f"[RENAME] {_dirname}\n  {_file} -> {_newname}")
        os.rename(os.path.join(_dirname, _file), os.path.join(_dirname, _newname))


if __name__ == "__main__":
    run()
