#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import git
import re
from datetime import datetime
from utils import shellhelper

EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

insertion_pattern = re.compile('(\d+) insertion')
deletion_pattern = re.compile('(\d+) deletion')


def get_project_repository(path: str):
    repository = git.Repo(path)
    assert not repository.bare
    return repository


def reset(git_repo):
    g = git_repo.git
    #g.reset('--hard')
    g.reset()


def checkout_origin_head(git_repo):
    g = git_repo.git
    g.checkout('-f', 'origin/HEAD')


def get_default_branch(path: str):
    output = shellhelper.run("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' | tr -d ' '", cwd=path)
    return output.strip()


def checkout_master_if_exists(path: str):
    """Checkout master branch if existes, otherwise checkout origin/HEAD branch"""
    git_repo = get_project_repository(path)
    g = git_repo.git
    if is_master_exists(path):
        g.checkout('-f', 'master')
    else:
        default_branch = get_default_branch(path)
        print(default_branch)
        g.checkout('-f', default_branch)


def is_master_exists(path: str):
    output = shellhelper.run("git branch -r | grep -E 'origin/master$'", cwd=path)
    output = ''.join(output.split())
    if len(output) > 0:
        return True
    else:
        return False


def is_origin_head_at_master(path: str):
    output = shellhelper.run("git branch -r | grep 'origin/HEAD'", cwd=path)
    output = ''.join(output.split())
    if output == 'origin/HEAD->origin/master':
        return True
    else:
        return False


def checkout_commit(git_repo, commit_id):
    g = git_repo.git
    g.checkout('-f', commit_id)


def get_diff_between_commits(parent_commit, head_commit):
    return parent_commit.diff(head_commit, create_patch=False)


def get_diff_of_initial_commit(git_repo, initial_commit):
    # See https://stackoverflow.com/questions/33916648/get-the-diff-details-of-first-commit-in-gitpython
    return git_repo.tree(EMPTY_TREE_SHA).diff(initial_commit, create_patch=False)


def get_non_merge_commits(path: str):
    git_repo = get_project_repository(path)
    g = git_repo.git
    result = g.log('--no-merges', '--oneline', '--pretty=%H').split('\n')
    return result


def get_all_commits(path: str):
    git_repo = get_project_repository(path)
    g = git_repo.git
    result = g.log('--oneline', '--pretty=%H').split('\n')
    return result


def get_latest_commit(path: str):
    git_repo = get_project_repository(path)
    g = git_repo.git
    return git_repo.head.commit


def get_spec_commit(path:str, commit_hash: str):
    git_repo = get_project_repository(path)
    return git_repo.commit(commit_hash)


def refresh_git_repo(path: str):
    git_repo = get_project_repository(path)
    reset(git_repo)
    checkout_master_if_exists(path)


def refresh_and_pull_git_repo(path: str):
    git_repo = get_project_repository(path)
    reset(git_repo)
    checkout_master_if_exists(path)
    git_repo.git.pull()


def refresh_repo(path: str):
    git_repo = get_project_repository(path)
    git_repo.git.pull()


def get_files_num(path: str):
    output = shellhelper.run("git ls-files | wc -l | tr -d ' '", cwd=path)
    return int(output)


def get_commits_num(path: str):
    output = shellhelper.run("git log --oneline $commit | wc -l | tr -d ' '", cwd=path)
    return int(output)


def get_repo_age_str(path: str):
    output = shellhelper.run("git log --reverse --pretty=oneline --format='%ar' | head -n 1 | LC_ALL=C sed 's/ago//' | tr -d ' '", cwd=path)
    return output


def get_last_commit_date(path: str):
    # 2017-12-07 11:22:05 +0100
    output = shellhelper.run("git log --pretty='format: %ai' | head -n 1", cwd=path)
    datetime_str = output.strip()
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S %z')


def get_first_commit_date(path: str):
    output = shellhelper.run("git log --reverse --pretty='format: %ai' | head -n 1", cwd=path)
    datetime_str = output.strip()
    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S %z')


def get_authors_num(path: str):
    output = shellhelper.run("git log --format='%aN' | sort -u | wc -l | tr -d ' '", cwd=path)
    return int(output)


def get_code_churn_between_commits(path: str, old_commit, new_commit):
    output = shellhelper.run("git diff --shortstat {} {} -- '*.java' | head -n 1".format(old_commit, new_commit), cwd=path)
    added_count = 0
    deleted_count = 0
    added_match = insertion_pattern.search(output)
    if added_match:
        added_count = int(added_match.group(1))
    deleted_match = deletion_pattern.search(output)
    if deleted_match:
        deleted_count = int(deleted_match.group(1))

    return added_count + deleted_count


def get_modified_line_counts(old_file, new_file):
    output = shellhelper.run("git diff --shortstat {} {}".format(old_file, new_file))
    added = 0
    deleted = 0
    modified = 0
    added_count = 0
    deleted_count = 0

    added_match = insertion_pattern.search(output)
    if added_match:
        added_count = int(added_match.group(1))
    deleted_match = deletion_pattern.search(output)
    if deleted_match:
        deleted_count = int(deleted_match.group(1))

    if added_count == deleted_count:
        modified = added_count
    elif added_count < deleted_count:
        modified = added_count
        deleted = deleted_count - added_count
    else:
        modified = deleted_count
        added = added_count - deleted_count

    return added, deleted, modified

