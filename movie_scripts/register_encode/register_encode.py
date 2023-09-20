import os
import re
import subprocess

from movie_scripts.register_encode.ts_information import TsInformation

movie_root = "w:\\movie\\temp"
encoded_dir = "w:\\movie_temp\\encoded"
add_task = f"{os.environ.get('HOMEDRIVE')}{os.environ.get('HOMEPATH')}/bin/Amatsukaze/exe_files/AmatsukazeAddTask.exe"


class RegisterEncode:
    def search_ts(self):
        for dirname, _, files in os.walk(top=movie_root):
            for file in files:
                if dirname.endswith("succeeded") or dirname.endswith("failed") or not file.endswith(".ts"):
                    continue

                file_path = os.path.join(dirname, file)
                ts_info = TsInformation(file_path).extract()
                yield file_path, ts_info, self.get_profile(file_path, ts_info.get('channel'), ts_info.get('program'))

    def get_profile(self, filename, channel, program):
        if channel.get('network_id') == 32391:
            return "デフォルト(MX)"
        if [
            x for x in program.get('genre') if
            x.get('major') == 'アニメ・特撮' and x.get('middle') in ['国内アニメ', '海外アニメ']
        ]:
            if channel.get('network_id') == 7 and len(re.findall(r"#[0-9]+", filename)) > 1:
                return "デフォルト(アニメ-ATX分割)"
            elif re.search(r"#[0-9]+,[0-9]+", filename) is not None:
                return "デフォルト(アニメ-ATX分割)"
            elif "水星の魔女" in filename or "推しの子" in filename or "青春ブタ野郎" in filename:
                return "デフォルト(アニメ) 810p"
            else:
                return "デフォルト(アニメ)"
        return "デフォルト(実写)"


def run():
    for _ts_name, _ts_info, _profile in RegisterEncode().search_ts():
        print(_ts_name, _ts_info.get('channel').get('network_id'), _ts_info.get('program').get('genre'), _profile)
        subprocess_args = [
            add_task,
            "-f", _ts_name,
            "-ip", "localhost",
            "-p", "32768",
            "--priority", "3",
            "-o", encoded_dir,
            "-s", _profile,
            "--no-move"
        ]

        print('[EXEC]', subprocess_args)
        subprocess.run(subprocess_args, capture_output=True)

if __name__ == "__main__":
    run()
