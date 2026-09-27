import logging
from pathlib import Path

from garminconnect import Garmin, GarminConnectConnectionError

logger = logging.getLogger(__name__)

_DUPLICATE_MARKER = "already exists (duplicate)"


def _prompt_mfa() -> str:
    """Ask for a Garmin MFA code on stdin.

    Only reached on a fresh login when no (or no longer valid) cached
    session is found in the tokenstore. Requires an interactive terminal —
    once entered, the resulting session is cached and reused by every
    later run (e.g. from cron), so this should only trigger once.
    """
    return input("Enter Garmin Connect MFA code: ").strip()


class GarminClient:
    def __init__(self, username: str, password: str, tokenstore: str | Path):
        self._tokenstore = str(tokenstore)
        self._client = Garmin(username, password, prompt_mfa=_prompt_mfa)

    def login(self) -> None:
        # Reuses a cached session from `tokenstore` when present and still
        # valid, avoiding a fresh username/password/MFA login on every run.
        # The underlying client persists a new session there automatically
        # after a successful login.
        self._client.login(self._tokenstore)

    def import_fit(self, filepath: Path) -> bool:
        """Upload a FIT file as an import.

        Uses import_activity() instead of upload_activity() so Garmin does not
        re-export the activity to connected third parties (e.g. Strava).

        Returns True on success, False if Garmin reports a duplicate (409).
        """
        try:
            self._client.import_activity(str(filepath))
            return True
        except GarminConnectConnectionError as exc:
            if _DUPLICATE_MARKER in str(exc):
                logger.info("Activity already exists in Garmin, skipping: %s", filepath.stem)
                return False
            raise
