import logging
import sys

from config import load_config
from garmin import GarminClient
from hammerhead import HammerheadClient
from state import State

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    state = State(config.state_file)

    logger.info("Authenticating with Hammerhead…")
    try:
        karoo = HammerheadClient(
            config.hammerhead_client_id,
            config.hammerhead_client_secret,
            config.hammerhead_username,
            config.hammerhead_password,
        )
    except Exception as exc:
        logger.error("Hammerhead authentication failed: %s", exc)
        sys.exit(1)

    logger.info("Authenticating with Garmin Connect…")
    try:
        garmin = GarminClient(
            config.garmin_username, config.garmin_password, config.garmin_tokenstore
        )
        garmin.login()
    except Exception as exc:
        logger.error("Garmin authentication failed: %s", exc)
        sys.exit(1)

    # Deliberately not state.get_last_sync(): a Karoo activity can take a
    # while to reach Hammerhead's cloud, sometimes after the current run's
    # wall-clock time has already passed it. A cursor that advances to
    # "now" on every run would then filter that activity out forever once
    # it does appear. Actual dedup already happens per-activity via
    # state.is_synced()/mark_synced() below, so this only needs to bound
    # the very first run — it stays fixed at SYNC_FROM_DATE.
    since = config.sync_from_date
    if since:
        logger.info("Fetching activities since %s", since.date().isoformat())
    else:
        logger.info("SYNC_FROM_DATE not set — fetching all activities")

    config.data_dir.mkdir(exist_ok=True)

    synced = 0
    skipped = 0

    for activity in karoo.get_activities(since):
        act_id = str(activity["id"])

        if state.is_synced(act_id):
            skipped += 1
            continue

        logger.info("Syncing activity %s…", act_id)
        fit_path = config.data_dir / f"{act_id}.fit"

        try:
            karoo.download_fit(act_id, fit_path)
            uploaded = garmin.import_fit(fit_path)
        except Exception as exc:
            logger.error("Failed to sync activity %s: %s", act_id, exc)
            if fit_path.exists():
                fit_path.unlink()
            continue
        finally:
            if fit_path.exists():
                fit_path.unlink()

        state.mark_synced(act_id)
        state.save()

        if uploaded:
            synced += 1
            logger.info("Uploaded activity %s", act_id)
        else:
            skipped += 1

    state.save()

    logger.info("Done. Uploaded: %d, skipped: %d", synced, skipped)


if __name__ == "__main__":
    main()
