"""Session debug logging (NDJSON)."""

import json
import time
from pathlib import Path

DEBUG_LOG_PATH = Path(
    "/Users/iriszhang/Monash/26S1-FIT5120-Industry experience studio project/ElderGo-KL/.cursor/debug-ce83c2.log"
)
SESSION_ID = "ce83c2"


def debug_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    # region agent log
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "sessionId": SESSION_ID,
                        "location": location,
                        "message": message,
                        "data": data,
                        "hypothesisId": hypothesis_id,
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except OSError:
        pass
    # endregion
