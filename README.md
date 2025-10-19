# 🧩 Mini Git (GitPy)

A simplified version control system written in **Python**, inspired by Git — built to understand how Git works internally.

This project (`gitpy`) implements the fundamental Git features such as **repository initialization**, **staging files**, and **committing changes**, using object-based storage with Blobs, Trees, and Commits.  

---

## 🚀 Features

✅ Initialize a new repository (`init`)  
✅ Stage files or directories (`add`)  
✅ Commit changes with messages (`commit`)  
✅ Internal structure using **objects**, **refs**, **HEAD**, and **index** files — similar to real Git  

---

## 🧠 How It Works

`gitpy` mimics the **core logic of Git** using the following concepts:

| Component | Description |
|------------|--------------|
| **Blob** | Represents the content of individual files. |
| **Tree** | Represents directories (hierarchical structure of blobs and sub-trees). |
| **Commit** | Stores a snapshot of the project along with metadata (author, timestamp, message, and parent commit). |
| **Index file** | Acts as a staging area for files added before committing. |
| **Refs & HEAD** | `refs/heads/main` stores the latest commit hash. `HEAD` points to the active branch. |
| **Objects folder** | Stores all serialized blobs, trees, and commits (compressed with zlib and hashed with SHA-1). |

When you run `gitpy add`, file contents are stored as blob objects, and the file paths are recorded in the `index` file.  
When you `commit`, the tree and commit objects are created, linking blobs together to form a version snapshot.

---

## 🛠️ Technologies Used

- **Language:** Python 3  
- **Modules:** `argparse`, `pathlib`, `json`, `hashlib`, `zlib`, `time`  
- **Core Concepts:** File I/O, SHA-1 hashing, zlib compression, JSON indexing, command-line parsing  

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/gitpy.git
cd gitpy
