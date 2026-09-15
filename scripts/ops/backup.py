"""Local database/filesystem-media backups with checksums and isolated restore.

Database commands use PG* environment variables; credentials never enter command arguments.
Restore requires an empty database and empty media directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
from urllib.parse import unquote, urlsplit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['backup', 'restore'])
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--media', type=Path, required=True)
    args = parser.parse_args()
    url = urlsplit(os.environ['CQ_DATABASE_URL'].replace('postgresql+psycopg:', 'postgresql:'))
    env = {**os.environ, 'PGHOST': url.hostname or 'localhost', 'PGPORT': str(url.port or 5432),
           'PGDATABASE': url.path.lstrip('/'), 'PGUSER': unquote(url.username or ''),
           'PGPASSWORD': unquote(url.password or '')}
    binary = Path(os.environ.get('PG_BIN', '/usr/bin'))
    def run(program, *arguments, capture=False):
        return subprocess.run([str(binary / program), *arguments], env=env, check=True,
                              text=True, capture_output=capture)
    archive = args.archive.resolve()
    media = args.media.resolve()
    if args.command == 'backup':
        archive.mkdir(parents=True, exist_ok=False)
        run('pg_dump', '--format=custom', '--file', str(archive / 'database.dump'))
        with tarfile.open(archive / 'media.tar.gz', 'w:gz') as tar:
            tar.add(media, arcname='media')
        checksums = {name: hashlib.sha256((archive / name).read_bytes()).hexdigest()
                     for name in ['database.dump', 'media.tar.gz']}
        (archive / 'manifest.json').write_text(json.dumps({'version': 1, 'sha256': checksums}, indent=2))
    else:
        manifest = json.loads((archive / 'manifest.json').read_text())
        for name in ['database.dump', 'media.tar.gz']:
            if hashlib.sha256((archive / name).read_bytes()).hexdigest() != manifest['sha256'][name]:
                raise SystemExit('Backup checksum mismatch')
        count = run('psql', '-XAt', '-c', "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename!='spatial_ref_sys'", capture=True)
        if int(count.stdout.strip()) != 0:
            raise SystemExit('Refusing restore into a nonempty database')
        if media.exists() and any(media.iterdir()):
            raise SystemExit('Refusing restore into a nonempty media directory')
        with tarfile.open(archive / 'media.tar.gz', 'r:gz') as tar:
            for member in tar.getmembers():
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0] != 'media' or member.issym() or member.islnk():
                    raise SystemExit('Unsafe media archive entry')
            run('pg_restore', '--exit-on-error', '--no-owner', '--dbname', env['PGDATABASE'], str(archive / 'database.dump'))
            media.mkdir(parents=True, exist_ok=True)
            for member in tar.getmembers():
                destination = media.joinpath(*Path(member.name).parts[1:])
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source:
                        destination.write_bytes(source.read())
    print(args.command + ' completed: ' + str(archive))


if __name__ == '__main__':
    main()
