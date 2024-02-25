import asyncio
import datetime


class SyoboiClient:


    def __init__(self):
        self.sem = asyncio.Semaphore()

    async def program_by_pid(self, pid, start: datetime.date, days=31, tid = None, chid = None):
        async with self.sem:
            parameter_dict={
                "Req": "ProgramByPID",
                "PID": pid,
                "Start": start.isoformat(),
                "Days":days
            }
            if tid is not None:
                parameter_dict["TID"] = tid
            if chid is not None:
                parameter_dict["ChID"] = chid

            try:
                

                pass
            finally:
                await asyncio.sleep(1)
