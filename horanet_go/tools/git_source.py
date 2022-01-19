import subprocess
import git
from odoo.modules.module import get_module_path


def get_module_git_repository(module_rec):
    """
    Access and return the module git repository IF the module is located in a git repository.

    :param module_rec: A record of ir.module.module model
    :return: A git repository or None if the module isn't under git visioning
    """
    git_folder_path = None
    repo = None
    if subprocess.call(['which', 'git']) == 0:
        horanet_app_path = get_module_path(module_rec.name)
        if horanet_app_path:
            try:
                git_folder_path = subprocess.check_output(
                    'git rev-parse --show-toplevel', shell=True, cwd=horanet_app_path)
                git_folder_path = git_folder_path.strip()
            except subprocess.CalledProcessError:
                git_folder_path = None
    if git_folder_path:
        repo = git.Repo(git_folder_path)

    return repo or None
