"""Development inventory helpers; the released Rust compiler remains authoritative."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tomllib


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value):
        raise ValueError('invalid package identifier')
    return value


def resources(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('package must be a real directory')
    files = []
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('linked package resource')
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            relative.encode('ascii')
            content = path.read_bytes()
            if len(content) > 32 * 1024:
                raise ValueError('resource exceeds package limit')
            content.decode('utf-8')
            files.append((relative, content))
    if not 1 <= len(files) <= 17 or sum(len(data) for _, data in files) > 128 * 1024:
        raise ValueError('invalid package size')
    if 'SKILL.md' not in [name for name, _ in files]:
        raise ValueError('missing methodology')
    return files


def package_hash(directory):
    files = resources(directory)
    data = bytearray(b'irmind-skill-package-v1\0')
    data.extend(struct.pack('>Q', len(files)))
    for name, content in files:
        name = name.encode('ascii')
        data.extend(struct.pack('>Q', len(name)))
        data.extend(name)
        data.extend(struct.pack('>Q', len(content)))
        data.extend(hashlib.sha256(content).digest())
    return hashlib.sha256(data).hexdigest()


def metadata(directory):
    text = (Path(directory) / 'SKILL.md').read_text()
    if not text.startswith('+++\n'):
        raise ValueError('missing frontmatter')
    fields = tomllib.loads(text.split('+++', 2)[1])
    if identifier(fields['name']) != Path(directory).name:
        raise ValueError('package directory and metadata name differ')
    return fields


def packages(repository, family):
    root = Path(repository) / family
    for entry in root.iterdir():
        if entry.is_symlink():
            raise ValueError('linked package directory')
        if entry.is_dir():
            identifier(entry.name)
            if not (entry / 'SKILL.md').is_file():
                raise ValueError('package directory has no SKILL.md')
    return sorted(root.glob('*/SKILL.md'))


def compile_package(compiler, directory):
    expected = package_hash(directory)
    result = subprocess.run([str(compiler), str(directory)], capture_output=True,
                            text=True, check=True, timeout=30)
    fields = result.stdout.strip().split()
    meta = metadata(directory)
    if fields != [meta['name'], meta['version'], expected]:
        raise ValueError('released compiler and package inventory disagree')
    return meta, expected


def safe_data_path(repository, relative):
    if not isinstance(relative, str) or relative.startswith('/') or '\\' in relative:
        raise ValueError('invalid data path')
    parts = relative.split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise ValueError('invalid data path component')
    root = Path(repository).resolve()
    path = root.joinpath(*parts)
    for parent in [path, *path.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError('linked data path')
    if not path.resolve().is_relative_to(root):
        raise ValueError('data path escapes repository')
    return path
