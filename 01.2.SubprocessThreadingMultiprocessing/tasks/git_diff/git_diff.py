import subprocess
from pathlib import Path


def get_changed_dirs(git_path: Path, from_commit_hash: str, to_commit_hash: str) -> set[Path]:
    """
    Get directories which content was changed between two specified commits
    :param git_path: path to git repo directory
    :param from_commit_hash: hash of commit to do diff from
    :param to_commit_hash: hash of commit to do diff to
    :return: sequence of changed directories between specified commits
    """
    result = subprocess.run(['git', 'diff', '--name-only', from_commit_hash, to_commit_hash],
                             cwd = git_path, text = True, check = True, capture_output=True)
    res = set()
    for directory in result.stdout.strip().split('\n'):
        res.add(Path(str(git_path) + '/' + str(Path(directory).parent)))
    return res
