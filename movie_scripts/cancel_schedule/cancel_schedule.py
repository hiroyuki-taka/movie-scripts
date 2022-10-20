import pprint
from functools import cache

import requests

epg_host = "http://192.168.0.170:8888"


@cache
def target_channel_info():
    cancel_target_channel = ('ＢＳアニマックス', 'キッズステーション', 'ＷＯＷＯＷプライム', 'ＷＯＷＯＷプラス')

    response = requests.get(f"{epg_host}/api/channels").json()
    return [data for data in response if data.get('name') in cancel_target_channel]


@cache
def reserves() -> list[int]:
    response = requests.get(f"{epg_host}/api/reserves/all").json()
    id_list: list[int] = []
    for p in response.get('reserves', []):
        id_list.append(p.get('programId'))
    for p in response.get('conflicts', []):
        id_list.append(p.get('programId'))

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

        for day_schedule in schedule(channel_id=_channel_id):
            for _program in day_schedule.get('programs'):
                if _program.get('id') in _reserves and _program.get('isFree') is False:
                    cancel(_program.get('id'))
                    print(f"{_channel_info.get('name')}:{_program.get('name')} - 予約をキャンセルしました。")
