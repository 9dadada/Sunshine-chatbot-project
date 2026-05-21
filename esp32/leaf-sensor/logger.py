# local data logger (rotating jsonl)

import os

LOG_FILE      = "data.jsonl"
LOG_MAX_BYTES = 200 * 1024  # rotate at ~200KB

def append_data(line):
    try:
        try:
            if os.stat(LOG_FILE)[6] > LOG_MAX_BYTES:
                try:
                    os.remove(LOG_FILE + ".old")
                except OSError:
                    pass
                os.rename(LOG_FILE, LOG_FILE + ".old")
        except OSError:
            pass
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Log error: {e}")
