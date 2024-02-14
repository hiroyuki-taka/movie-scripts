import itertools
import pprint
import time
from collections.abc import Iterator
from functools import cache

import requests

epg_host = "http://192.168.0.175:8888"


@cache
def target_channel_info() -> dict[int, str]:
    cancel_target_channel = ("ＢＳアニマックス", "キッズステーション", "ＴＢＳチャンネル２", "ＷＯＷＯＷプライム", "ＷＯＷＯＷプラス")

    response = requests.get(f"{epg_host}/api/channels").json()
    return {data.get("id"): data.get("name") for data in response if data.get("name") in cancel_target_channel}


def reserves() -> Iterator[dict]:
    offset = 0
    limit = 24

    reserve_list = None
    while reserve_list is None or reserve_list:
        response = requests.get(
            f"{epg_host}/api/reserves?offset={offset}&limit={limit}&isHalfWidth=true&type=all"
        ).json()

        if "reserves" in response:
            reserve_list = response["reserves"]
            yield from reserve_list
        else:
            reserve_list = []
        offset += limit


@cache
def schedule(channel_id: int, days: int = 8):
    now = int(time.time()) * 1000
    ch_programs = requests.get(
        f"{epg_host}/api/schedules/{channel_id}?startAt={now}&days={days}&isHalfWidth=true"
    ).json()

    return {
        program.get("id"): program
        for program in itertools.chain.from_iterable([p.get("programs") for p in ch_programs])
    }


def cancel(program_id):
    return requests.delete(f"{epg_host}/api/reserves/{program_id}")


def run():
    cancel_target_channels = target_channel_info()

    for program in reserves():
        channel_id = program.get("channelId")
        program_id = program.get("programId")
        if channel_id in cancel_target_channels:
            s = schedule(channel_id=channel_id).get(program_id)
            if s and s.get("isFree") is False:
                cancel(program_id)
                print(f"{cancel_target_channels[channel_id]}:{s.get('name')} - 予約をキャンセルしました。")


if __name__ == "__main__":
    run()
