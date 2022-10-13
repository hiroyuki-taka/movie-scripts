import os
import re

"""
ファイル名正規化
ソートの邪魔になるテキストを消去
"""

movie_root = "w:\\movie\\temp"


class RenameSucceedFiles:
    def target_files(self):
        pattern = re.compile(r"\[無]|\[新]|\[終]")

        for dirname, _, files in os.walk(top=movie_root):
            for file in files:
                if dirname.endswith("succeeded") and file.endswith(".ts") and re.search(pattern, file):
                    yield dirname, file, re.sub(pattern, "", file)


if __name__ == "__main__":
    for _dirname, _file, _newname in RenameSucceedFiles().target_files():
        print(f"[RENAME] {_dirname}\n  {_file} -> {_newname}")
        os.rename(os.path.join(_dirname, _file), os.path.join(_dirname, _newname))
