import json
import logging
import os

import boto3
from git import Repo

CONFIG_DIRECTORY = os.getenv("CONFIG_DIRECTORY", "JSONFromTalend")
DEFAULT_WORKSPACE = os.getenv("DEFAULT_WORKSPACE", "./workspace")
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")
SECRET_ID = os.getenv("SECRET_ID", "Okta-BackupTool/Lyvoc-dev")
REGION = os.getenv("REGION", "eu-west-3")


class Backupta:
    def __init__(self, github_org, github_repo, workspace=DEFAULT_WORKSPACE, branch=DEFAULT_BRANCH):
        """
        class
        :param github_org: the GitHub organization that the repo is in
        :param github_repo: the GitHub repo name
        :param workspace: a folder that will be used to store the cloned repo default value is "./workspace"
        """
        self.github_org = github_org
        self.github_repo = github_repo
        self.username, self.token = self.get_credentials()
        self.repo_url = self.build_repo_url()
        self.workspace = workspace
        self.current_branch = branch
        self.repo = None
        self.is_git_author_set = False

    def build_repo_url(self):
        """
        get the repo url from the GitHub org and repo name and the users credentials
        :return:
        """
        return f"https://{self.username}:{self.token}@github.com/{self.github_org}/{self.github_repo}.git"

    def get_credentials(self):
        """
        get the credentials from Amazon Secrets Manager
        :return:
        """
        return os.getenv("USERNAME"), os.getenv("PASSWORD")
        client = boto3.client("secretsmanager", region_name=REGION)
        response = client.get_secret_value(SecretId=SECRET_ID)
        secret_string = json.loads(response["SecretString"])
        return secret_string.get("LAMBDA_GITHUB_USERNAME"), secret_string.get("LAMBDA_GITHUB_PASSWORD")

    def clone_repo(self, branch=None):
        """
        Clone the repo in the local folder. if the repo already exists it will be deleted and cloned again
        :return:
        """
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        if os.path.exists(self.workspace):
            os.system(f"rm -rf {self.workspace}")
            logging.info(f"Deleted {self.workspace} because it already exists")
        Repo.clone_from(self.repo_url, self.workspace)
        logging.info(f"Cloned {self.github_repo} to {self.workspace}")
        # get current branch
        repo = Repo(self.workspace)
        self.current_branch = repo.active_branch.name
        if branch:
            self.checkout_branch(branch)
        self.repo = repo

    def set_git_author(self, name, email):
        """
        get the lambda config from the config file
        :return:
        """
        self.repo.config_writer().set_value("user", "name", name).release()
        self.repo.config_writer().set_value("user", "email", email).release()
        self.is_git_author_set = True

    def checkout_branch(self, branch_name: str):
        """
        checkout a branch in the local repo
        :param branch_name:
        :return:
        """
        repo = self.repo
        repo.git.checkout(branch_name)
        self.current_branch = branch_name
        logging.info(f"Checked out {branch_name}")

    def get_config(self, config_file: str):
        """
        get the config from the config file
        :param config_file: filename of the config file
        :return:
        """
        with open(f"{self.workspace}/{CONFIG_DIRECTORY}/{config_file}", "r") as f:
            return json.load(f)

    def commit(self, message="Committed by Bakupta"):
        """
        commit the changes to the local repo
        :param message: commit message default value is "Committed by Bakupta"
        :return:
        """
        if not self.is_git_author_set:
            raise Exception("Git author is not set")
        repo = self.repo
        repo.git.add(A=True)
        repo.git.commit('-m', message)
        logging.info(f"Changes committed: {message}")

    def push(self):
        """
        push the changes to the remote repo
        :return:
        """
        repo = self.repo
        repo.git.push()
        logging.info("Changes pushed")

    def save(self, commit_message="Saved by Bakupta"):
        """
        save the changes to the local repo and push to the remote repo
        :param commit_message: commit message default value is "Saved by Bakupta"
        :return:
        """
        self.commit(commit_message)
        self.push()

    def write_report(self, report_name: str, report_data, filename: str):
        """
        write the report to a file. The reports will be saved in a folder called "reports" in the local repo. then in a
        sub folder called "report_name"
        :param report_name: name of the report
        :param report_data:
        :param filename: do not forget to add the extension
        :return:
        """
        my_report_folder = f"{self.workspace}/reports/{report_name}"
        report_path = f"{my_report_folder}/{filename}"
        os.path.exists(my_report_folder) or os.makedirs(my_report_folder)  # create the folder if it doesn't exist
        with open(report_path, "w") as f:
            if isinstance(report_data, dict):
                f.write(json.dumps(report_data, indent=4))
            else:
                f.write(report_data)
        logging.info(f"Wrote report to {report_path}")

    def clean_workspace(self):
        """
        delete the local repo
        :return:
        """
        if os.path.exists(self.workspace):
            os.system(f"rm -rf {self.workspace}")
            logging.info(f"Deleted {self.workspace}")
