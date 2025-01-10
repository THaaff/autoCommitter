import os
import subprocess
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# this is a test commit

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set in the environment variables.")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
if not GITHUB_USERNAME:
    raise ValueError("GITHUB_USERNAME is not set in the environment variables.")

class GitHandler(FileSystemEventHandler):
    def __init__(self, repo_name=None):
        self.repo_name = repo_name

    def is_git_repo(self):
        return os.path.isdir(".git")

    def initialize_git_repo(self):
        print("Initializing Git repository...")
        subprocess.run(["git", "init"], check=True)
        # Create an initial commit to enable branch renaming
        print("Creating an initial commit...")
        with open(".gitkeep", "w") as f:
            f.write("Temporary file to enable branch renaming.")  # Create a placeholder file
        subprocess.run(["git", "add", ".gitkeep"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        # Rename the branch to 'main'
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        print("Git repository initialized with an initial commit and branch renamed to 'main'.")


    def create_github_repo(self):
        if not self.repo_name:
            self.repo_name = os.path.basename(os.getcwd())
        print(f"Creating GitHub repository: {self.repo_name}")
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {"name": self.repo_name, "private": False}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"GitHub repository '{self.repo_name}' created successfully.")
            return response.json()["html_url"]
        else:
            print(f"Error creating GitHub repository: {response.status_code} - {response.text}")
            return None

    def set_git_remote(self, repo_url):
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        print(f"Remote set to {repo_url}")

    def commit_and_push(self):
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Automated commit: {time.ctime()}"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
            print(f"Changes committed and pushed to GitHub at {time.ctime()}")
        except subprocess.CalledProcessError as e:
            print(f"Error during Git operation: {e}")

    def on_any_event(self, event):
        if not self.is_git_repo():
            self.initialize_git_repo()
            repo_url = self.create_github_repo()
            if repo_url:
                self.set_git_remote(repo_url)
                subprocess.run(["git", "branch", "-M", "main"], check=True)
        self.commit_and_push()

if __name__ == "__main__":
    path = "."  # Directory to watch
    repo_name = None  # Optionally specify the repo name
    event_handler = GitHandler(repo_name=repo_name)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Watching for changes in {path}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
