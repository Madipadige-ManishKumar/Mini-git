This document outlines the execution flow within `main.py` for each of the primary `gitpy` commands.
It details which parts of the code are utilized when a specific command is run.

---
### `python main.py init`
This command initializes a new `gitpy` repository in the current directory.
1.  **`main()` function (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   The `argparse` module processes the `init` command.
   *   An instance of `Repository` is created: `repo = Repository()`.
   *   The condition `args.command == "init"` evaluates to `True`.
   *   `repo.init()` is called.
2.  **`Repository.init()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   It first checks if the `.gitpy` directory (`self.gitdir`) already exists.
   *   If it does not exist:
       *   `self.gitdir.mkdir()` creates the `.gitpy` directory.
       *   `self.objects.mkdir()` creates the `.gitpy/objects` directory.
       *   `self.refs.mkdir()` creates the `.gitpy/refs` directory.
       *   `self.head_dir.mkdir()` creates the `.gitpy/refs/heads` directory.
       *   `self.head.write_text("ref: refs/heads/main\n")` writes the initial HEAD reference.
       *   `self.save_index({})` is called to create an empty index file.
       *   A success message is printed: `"Initialized empty gitpy repository"`.
   *   If `.gitpy` already exists, it prints: `"Repository already exists"`.
3.  **`Repository.save_index()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.init()` to write an empty JSON object `{}` to `.gitpy/index`.
---
### `python main.py add <path>`
This command adds files or directories to the `gitpy` staging area (index).
1.  **`main()` function (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   The `argparse` module processes the `add` command and captures the `<path>` arguments.
   *   An instance of `Repository` is created: `repo = Repository()`.
   *   The condition `args.command == "add"` evaluates to `True`.
   *   It checks if the `.gitpy` directory (`repo.gitdir`) exists. If not, it prints `"Not a gitpy repository"`.
   *   It iterates through each `path` provided in `args.paths`.
   *   For each `path`, `repo.add_path(path)` is called.
2.  **`Repository.add_path(path)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Determines if the given `path` is a file or a directory.
   *   If `path` is a file (`fullpath.is_file()`):
       *   `self.add_file(path)` is called.
   *   If `path` is a directory (`fullpath.is_dir()`):
       *   `self.add_directory(path)` is called.
   *   If the path does not exist or is neither a file nor a directory, an exception is raised.
3.  **`Repository.add_file(path)` method (if adding a file) (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Reads the content of the file.
   *   Creates a `Blob` object with the file content: `blob = Blob(content)`.
   *   `blob_hash = self.store_object(blob)` is called to store the blob.
   *   `index = self.load_index()` is called to retrieve the current index.
   *   The `blob_hash` is added to the `index` dictionary, mapped to the file's path.
   *   `self.save_index(index)` is called to update the index file.
   *   A message is printed: `"Added <path>"`.
4.  **`Repository.add_directory(path)` method (if adding a directory) (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   `index = self.load_index()` is called to retrieve the current index.
   *   It recursively iterates through all files within the specified directory (excluding `.gitpy` files).
   *   For each file:
       *   A `Blob` object is created with the file's content.
       *   `blob_hash = self.store_object(blob)` is called to store the blob.
       *   The `blob_hash` is added to the `index` dictionary, mapped to the file's relative path.
   *   `self.save_index(index)` is called to update the index file.
   *   A message is printed indicating the number of files added from the directory.
5.  **`Repository.store_object(obj)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `add_file` and `add_directory`.
   *   `obj.hash()` is called (from `GitObject.hash()`) to compute the SHA-1 hash of the object.
   *   It creates the appropriate subdirectory under `.gitpy/objects` if it doesn't exist.
   *   `obj_file.write_bytes(obj.serialize())` is called to write the zlib-compressed object data to a file.
   *   Returns the computed `obj_hash`.
6.  **`GitObject.hash()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.store_object`.
   *   Constructs the Git object header (`type` and `content` length).
   *   Computes and returns the SHA-1 hexadecimal hash of the header + content.
7.  **`GitObject.serialize()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.store_object`.
   *   Constructs the Git object header.
   *   Compresses the header + content using `zlib.compress()` and returns the compressed bytes.
8.  **`Repository.load_index()` and `Repository.save_index()` methods (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   `load_index` reads the `.gitpy/index` file and parses its JSON content.
   *   `save_index` writes the updated index dictionary back to `.gitpy/index` as pretty JSON.
---
### `python main.py commit -m "Your commit message"`
This command creates a new commit object from the current index.
1.  **`main()` function (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   The `argparse` module processes the `commit` command and captures the message.
   *   An instance of `Repository` is created: `repo = Repository()`.
   *   The condition `args.command == "commit"` evaluates to `True`.
   *   It checks if the `.gitpy` directory (`repo.gitdir`) exists. If not, it prints `"Not a gitpy repository"`.
   *   `repo.commit(args.message, "Gitpy User")` is called.
2.  **`Repository.commit(message, author)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   `tree_hash = self.create_tree_from_index()` is called to build the tree object(s) from the current index and get the root tree hash.
   *   `current_branch = self.get_current_branch()` is called to determine the active branch.
   *   `parent_commit = self.get_branch_commit(current_branch)` is called to get the hash of the previous commit on the current branch (if any).
   *   `index = self.load_index()` is called. If the index is empty, it prints `"No changes to commit (Up to date)"` and returns.
   *   If a `parent_commit` exists:
       *   `parent_git_commit_obj = self.load_object(parent_commit)` is called to load the parent commit object.
       *   `parent_commit_data = Commit.from_content(parent_git_commit_obj.content)` is called to deserialize the parent commit.
       *   It compares the newly created `tree_hash` with `parent_commit_data.tree_hash`. If they are identical, it means no changes have occurred, and it prints `"No changes to commit (Up to date)"` and returns.
   *   A `Commit` object is instantiated with the `tree_hash`, `parent_hashes`, `author`, `committer`, and `message`.
   *   `commit_hash = self.store_object(commit_obj)` is called to store the new commit object.
   *   `self.set_branch_commit(current_branch, commit_hash)` is called to update the branch reference to point to the new commit.
   *   `self.save_index({})` is called to clear the index after a successful commit.
   *   A success message is printed: `"Committed to <branch> with commit <hash>"`.
   *   The `commit_hash` is returned.
3.  **`Repository.create_tree_from_index()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()`.
   *   `index = self.load_index()` is called to get the current staged files.
   *   It organizes the flat index into a nested dictionary structure representing the file system hierarchy.
   *   A recursive helper function `create_tree_recursive` is used to:
       *   Create `Tree` objects for directories and add `Blob` references for files.
       *   `self.store_object(tree)` is called for each `Tree` object created.
   *   Returns the hash of the root `Tree` object.
4.  **`Repository.get_current_branch()` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()`.
   *   Reads the content of the `.gitpy/HEAD` file to determine the current branch name.
5.  **`Repository.get_branch_commit(branch)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()`.
   *   Reads the commit hash from the branch file (e.g., `.gitpy/refs/heads/main`).
6.  **`Repository.load_object(obj_hash)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()` to load the parent commit object.
   *   Locates the object file based on the `obj_hash`.
   *   Reads the compressed bytes and passes them to `GitObject.deserialize()`.
   *   Returns the deserialized `GitObject`.
7.  **`Commit.__init__()` and `Commit._serialize_commit()` methods (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   `Commit.__init__()` constructs the commit object.
   *   It calls `self._serialize_commit()` to format the commit data (tree hash, parent hashes, author, committer, message, timestamp) into a byte string.
   *   It then calls `super().__init__('commit', content)` to initialize the `GitObject` base with type 'commit' and the serialized content.
8.  **`Commit.from_content(data)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()` to parse the content of a parent commit object.
   *   Decodes the byte data and parses the lines to extract the tree hash, parent hashes, author, committer, and message.
   *   Returns a new `Commit` instance populated with these details.
9.  **`Repository.store_object(obj)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()` to store the newly created commit object. (See description under `add` command).
10. **`Repository.set_branch_commit(branch, commit_hash)` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()`.
   *   Updates the branch reference file (e.g., `.gitpy/refs/heads/main`) to point to the new `commit_hash`.
11. **`Repository.save_index({})` method (c:\Users\M.Manish kumar\OneDrive\Desktop\Mini git\main.py)**:
   *   Called by `Repository.commit()` to clear the index after the commit.
