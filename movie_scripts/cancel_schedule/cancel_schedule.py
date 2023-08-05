import pprint
from functools import cache

import requests

epg_host = "http://192.168.0.170:8888"


@cache
def target_channel_info():
    cancel_target_channel = ('ＢＳアニマックス', 'キッズステーション', 'ＴＢＳチャンネル２', 'ＷＯＷＯＷプライム', 'ＷＯＷＯＷプラス')

    response = requests.get(f"{epg_host}/api/channels").json()
    return [data for data in response if data.get('name') in cancel_target_channel]


@cache
def reserves() -> list[int]:
    response = requests.get(f"{epg_host}/api/reserves/all").json()
    id_list: list[int] = []

    if "reserves" in response:
        for r in response["reserves"]:
            id_list.append(r.get("programId"))

    if "conflicts" in response:
        for r in response["conflicts"]:
            id_list.append(r.get("programId"))

    return id_list


@cache
def schedule(channel_id: int, days: int = 8):
    return requests.get(f"{epg_host}/api/schedule/{channel_id}?days={days}").json()


def cancel(program_id):
    return requests.delete(f"{epg_host}/api/reserves/{program_id}")


if __name__ == "__main__":
    # 予約リスト
    _reserves = reserves()

    for _channel_info in target_channel_info():
        _channel_id = _channel_info.get('id')
        _channel_name = _channel_info.get('name')

        for day_schedule in schedule(channel_id=_channel_id):
            for _program in day_schedule.get('programs'):
                match _program:
                    case {"id": _program_id, "name": _program_name, "isFree": False} if _program_id in _reserves:
                        cancel(_program_id)
                        print(f"{_channel_name}:{_program_name} - 予約をキャンセルしました。")
