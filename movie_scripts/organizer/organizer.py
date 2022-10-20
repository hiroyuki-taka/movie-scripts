import os

encoded_root = "w:\\movie_temp\\encoded"


def encoded_files():
    for dirname, _, files in os.walk(top=encoded_root):
        for filename in files:
            if not filename.endswith(".mp4"):
                continue
            yield os.path.join(dirname, filename)


if __name__ == "__main__":
    for _filename in encoded_files():
        print(_filename)
