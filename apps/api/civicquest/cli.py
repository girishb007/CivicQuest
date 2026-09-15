import argparse
import csv
import json
from pathlib import Path

from sqlalchemy import select

from .db import SessionLocal


def main():
    p = argparse.ArgumentParser(prog="civicquest")
    p.add_argument(
        "command",
        choices=[
            "seed",
            "worker",
            "drain",
            "openapi",
            "rebuild",
            "import-boundaries",
            "import-representatives",
            "install-mumbai-reference",
            "import-postal",
            "import-bmc-offices",
            "refresh-reference",
            "retry-jobs",
            "retention",
        ],
    )
    p.add_argument("--file")
    p.add_argument("--metadata")
    args = p.parse_args()
    if args.command == "worker":
        from .worker import main as worker

        worker()
        return
    if args.command == "drain":
        from .worker import drain

        print("Processed jobs:", drain())
        return
    if args.command == "openapi":
        from .main import app

        target = Path("packages/contracts/openapi.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(app.openapi(), indent=2))
        print(target)
        return
    with SessionLocal.begin() as db:
        if args.command == "retention":
            from .operations import retain_originals

            print("Purged originals:", retain_originals(db))
        if args.command == "seed":
            from .seed import seed

            seed(db)
        elif args.command == "rebuild":
            from .attention import rebuild_hotspots
            from .models import User
            from .progress import rebuild_progress

            rebuild_hotspots(db)
            for uid in db.scalars(select(User.id).where(User.status == "active")):
                rebuild_progress(db, uid)
        elif args.command == "import-boundaries":
            from .geo import import_geojson

            if not args.file or not args.metadata:
                p.error("--file and --metadata are required")
            import_geojson(
                db, json.loads(Path(args.file).read_text()), json.loads(Path(args.metadata).read_text())
            )
        elif args.command == "import-representatives":
            from .reference_data import import_representatives

            if not args.file:
                p.error("--file is required")
            print("Imported representatives:", len(import_representatives(db, json.loads(Path(args.file).read_text()))))
        elif args.command == "install-mumbai-reference":
            from .geo import import_geojson
            from .models import Area, Dataset
            from .reference_data import import_representatives

            root = Path(args.file or "data/reference")
            bundles = [
                ("mumbai-bmc-administrative-wards.geojson", "bmc-wards.metadata.json"),
                ("mumbai-assembly-constituencies.geojson", "mumbai-assembly.metadata.json"),
                ("mumbai-parliamentary-constituencies.geojson", "mumbai-parliamentary.metadata.json"),
            ]
            datasets = []
            for geo_name, metadata_name in bundles:
                datasets.append(import_geojson(db, json.loads((root / geo_name).read_text()),
                                               json.loads((root / metadata_name).read_text())))
            for area in db.scalars(select(Area).where(Area.dataset_id.in_([item.id for item in datasets]))):
                area.active = True
            # The seed fixture remains in the database for tests/history but must
            # not overlap the reviewed Mumbai reference layers used by the app.
            synthetic_ids = select(Dataset.id).where(Dataset.synthetic.is_(True))
            for area in db.scalars(select(Area).where(Area.dataset_id.in_(synthetic_ids))):
                area.active = False
            reps = import_representatives(db, json.loads((root / "mumbai-representatives-2026-09-13.json").read_text()))
            print("Installed Mumbai datasets:", len(datasets), "representatives:", len(reps))
        elif args.command == "import-postal":
            from .reference_data import import_postal_places

            if not args.file or not args.metadata:
                p.error("--file and --metadata are required")
            with Path(args.file).open(encoding="latin1", newline="") as source:
                rows = list(csv.DictReader(source))
            print("Imported postal places:", len(import_postal_places(
                db, rows, json.loads(Path(args.metadata).read_text()))))
        elif args.command == "import-bmc-offices":
            from .reference_data import import_bmc_ward_offices

            if not args.file or not args.metadata:
                p.error("--file and --metadata are required")
            print("Imported BMC contacts:", len(import_bmc_ward_offices(
                db, json.loads(Path(args.file).read_text()), json.loads(Path(args.metadata).read_text()))))
        elif args.command == "refresh-reference":
            from .reference_refresh import refresh_reference_data

            print("Reference refresh:", json.dumps(refresh_reference_data(db), sort_keys=True))
        elif args.command == "retry-jobs":
            from .db import now
            from .models import Outbox

            for e in db.scalars(select(Outbox).where(Outbox.state == "dead")):
                e.state = "pending"
                e.attempts = 0
                e.available_at = now()
                e.dispatched_at = None
    print(args.command + " completed")


if __name__ == "__main__":
    main()
