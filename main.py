import argparse
from pathlib import Path
import sys
import json
import hashlib
import zlib
from typing import Dict, List, Tuple
import time


# ==============================================
# Base Git Object Class
# ==============================================
class GitObject:
    def __init__(self, obj_type: str, content: bytes) -> None:
        self.type = obj_type
        self.content = content

    def hash(self):
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()

    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def deserialize(cls, data: bytes) -> 'GitObject':
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b'\0')
        header = decompressed[:null_idx]
        content = decompressed[null_idx + 1:]
        obj_type, _ = header.split(b' ')
        return cls(obj_type.decode(), content)


# ==============================================
# Blob Object
# ==============================================
class Blob(GitObject):
    def __init__(self, content: bytes) -> None:
        super().__init__('blob', content)

    def get_content(self) -> bytes:
        return self.content


# ==============================================
# Tree Object
# ==============================================
class Tree(GitObject):
    def __init__(self, entries: List[Tuple[str, str, str]] = None) -> None:
        self.entries = entries or []
        content = self._serialize_entries()
        super().__init__('tree', content)

    def _serialize_entries(self) -> bytes:
        result = b''
        for mode, name, hash in self.entries:
            result += f"{mode} {name}\0".encode() + bytes.fromhex(hash)
        return result

    def add_entry(self, mode: str, name: str, hash: str):
        self.entries.append((mode, name, hash))
        self.content = self._serialize_entries()

    @classmethod
    def from_content(cls, data: bytes) -> 'Tree':
        tree = cls()
        i = 0
        while i < len(data):
            null_idx = data.find(b'\0', i)
            if null_idx == -1:
                break
            mode_name = data[i:null_idx].decode()
            mode, name = mode_name.split(' ', 1)
            obj_hash = data[null_idx + 1: null_idx + 21].hex()
            tree.add_entry(mode, name, obj_hash)
            i = null_idx + 21
        return tree


# ==============================================
# Commit Object
# ==============================================
class Commit(GitObject):
    def __init__(self,
                 tree_hash: str,
                 parent_hash: List[str],
                 author: str,
                 committer: str,
                 message: str,
                 timestamp: int = None):
        self.tree_hash = tree_hash
        self.parent_hash = parent_hash
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())

        # serialize commit content
        content_str = self._serialize_commit()
        content = content_str.encode()
        super().__init__('commit', content)

    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
        for parent in self.parent_hash:
            lines.append(f"parent {parent}")
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("")
        lines.append(self.message)
        return "\n".join(lines)

    @classmethod
    def from_content(cls, data: bytes) -> 'Commit':
        lines = data.decode().split('\n')
        tree_hash = None
        parent_hashes = []
        author = None
        committer = None
        message_start = 0
        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author = line[7:].rsplit(' ', 2)[0]
            elif line.startswith("committer "):
                committer = line[10:].rsplit(' ', 2)[0]
            elif line == "":
                message_start = i + 1
                break
        message = "\n".join(lines[message_start:])
        return cls(tree_hash, parent_hashes, author, committer, message)


# ==============================================
# Repository Class
# ==============================================
class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.gitdir = self.path / ".gitpy"
        self.objects = self.gitdir / "objects"
        self.refs = self.gitdir / "refs"
        self.head = self.gitdir / "HEAD"
        self.index = self.gitdir / "index"
        self.head_dir = self.refs / "heads"

    def init(self):
        if self.gitdir.exists():
            return False
        self.gitdir.mkdir()
        self.objects.mkdir()
        self.refs.mkdir()
        self.head_dir.mkdir()
        self.head.write_text("ref: refs/heads/main\n")
        self.save_index({})
        print("Initialized empty gitpy repository")
        return True

    def load_index(self) -> Dict[str, str]:
        if not self.index.exists():
            return {}
        try:
            return json.loads(self.index.read_text())
        except json.JSONDecodeError:
            return {}

    def save_index(self, index: Dict[str, str]):
        self.index.write_text(json.dumps(index, indent=2))

    def load_object(self, obj_hash: str) -> GitObject:
        obj_dir = self.objects / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        if not obj_file.exists():
            raise Exception(f"Object {obj_hash} does not exist")
        return GitObject.deserialize(obj_file.read_bytes())

    def store_object(self, obj: GitObject) -> str:
        obj_hash = obj.hash()
        obj_path = self.objects / obj_hash[:2]
        obj_file = obj_path / obj_hash[2:]
        if not obj_path.exists():
            obj_path.mkdir(exist_ok=True)
        obj_file.write_bytes(obj.serialize())
        return obj_hash

    def add_file(self, path):
        full_path = self.path / path
        if not full_path.exists():
            raise Exception(f"File {path} does not exist")
        content = full_path.read_bytes()
        blob = Blob(content)
        blob_hash = self.store_object(blob)
        index = self.load_index()
        index[str(path)] = blob_hash
        self.save_index(index)
        print(f"Added {path}")

    def add_directory(self, path):
        fullpath = self.path / path
        if not fullpath.exists():
            raise Exception(f"Directory {path} does not exist")
        if not fullpath.is_dir():
            raise Exception(f"Path {path} is not a directory")

        index = self.load_index()
        count = 0
        for filepath in fullpath.rglob('*'):
            if filepath.is_file():
                if ".gitpy" in filepath.parts:
                    continue
                blob = Blob(filepath.read_bytes())
                blob_hash = self.store_object(blob)
                retpath = filepath.relative_to(self.path)
                index[str(retpath)] = blob_hash
                count += 1
        self.save_index(index)
        print(f"Added {count} files from directory {path}")

    def add_path(self, path):
        fullpath = self.path / path
        if not fullpath.exists():
            raise Exception(f"Path {path} does not exist")
        if fullpath.is_file():
            self.add_file(path)
        elif fullpath.is_dir():
            self.add_directory(path)
        else:
            raise Exception(f"Path {path} is neither file nor directory")

    def create_tree_from_index(self):
        index = self.load_index()
        if not index:
            tree = Tree()
            return self.store_object(tree)

        dirs = {}
        files = {}

        for filepath, blob_hash in index.items():
            parts = filepath.split('/')
            if len(parts) == 1:
                files[parts[0]] = blob_hash
            else:
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}
                current = dirs[dir_name]
                for part in parts[1:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = blob_hash

        def create_tree_recursive(entries_dict: Dict):
            tree = Tree()
            for name, blob_hash in entries_dict.items():
                if isinstance(blob_hash, str):
                    tree.add_entry('100644', name, blob_hash)
                elif isinstance(blob_hash, dict):
                    sub_tree_hash = create_tree_recursive(blob_hash)
                    tree.add_entry('40000', name, sub_tree_hash)
            return self.store_object(tree)

        root_entries = {**files}
        for dir_name, dir_content in dirs.items():
            root_entries[dir_name] = dir_content
        return create_tree_recursive(root_entries)

    def get_current_branch(self) -> str:
        if not self.head.exists():
            return "main"
        head_content = self.head.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        return "HEAD"

    def get_branch_commit(self, branch: str) -> str:
        branch_file = self.head_dir / branch
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None

    def set_branch_commit(self, branch: str, commit_hash: str):
        branch_file = self.head_dir / branch
        branch_file.write_text(commit_hash + "\n")

    def commit(self, message: str, author: str = "Gitpy User"):
        tree_hash = self.create_tree_from_index()
        current_branch = self.get_current_branch()
        parent_commit = self.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else []

        index = self.load_index()
        if not index:
            print("No changes to commit (Up to date)")
            return

        if parent_commit:
            parent_git_commit_obj = self.load_object(parent_commit)
            parent_commit_data = Commit.from_content(parent_git_commit_obj.content)
            if tree_hash == parent_commit_data.tree_hash:
                print("No changes to commit (Up to date)")
                return

        commit_obj = Commit(
            tree_hash=tree_hash,
            parent_hash=parent_hashes,
            author=author,
            committer=author,
            message=message
        )
        commit_hash = self.store_object(commit_obj)
        self.set_branch_commit(current_branch, commit_hash)
        self.save_index({})
        print(f"Committed to {current_branch} with commit {commit_hash}")
        return commit_hash


# ==============================================
# CLI Entry Point
# ==============================================


def main():
    parser = argparse.ArgumentParser(description="gitpy")  
    subparsers = parser.add_subparsers(dest='command')

    # init command
    subparsers.add_parser('init', help='Initialize a new gitpy repository')

    # add command
    add_parser = subparsers.add_parser('add', help='Add files to gitpy repository')
    add_parser.add_argument("paths", nargs='+', help="Files or directories to add")

    # commit command
    commit_parser = subparsers.add_parser('commit', help='Commit changes')
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    repo = Repository()
    try:
        if args.command == "init":
            if not repo.init():
                print("Repository already exists")
        elif args.command == "add":
            if not repo.gitdir.exists():
                print("Not a gitpy repository")
                return
            for path in args.paths:
                repo.add_path(path)
        elif args.command == "commit":
            if not repo.gitdir.exists():
                print("Not a gitpy repository")
                return
            repo.commit(args.message, "Gitpy User")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
