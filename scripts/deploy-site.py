import os, sys
import shutil
from subprocess import call
import git
import argparse
from distutils.dir_util import copy_tree

def log(message):
    print(f"[deploy] {message}")

def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        raise ValueError("file {} is not a file or dir.".format(path))

parser = argparse.ArgumentParser()
parser.add_argument('--push', action='store_true')
args = parser.parse_args()

script_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.join(script_dir,'..')
thumbnail_dir = os.path.join(root_dir, 'images/photography/thumbnails')
site_dir = os.path.join(root_dir,'_site')
setup_photos_script = os.path.join(root_dir, 'scripts/setup-photos.py')
config_files = ['_config.yml']
private_config = os.path.join(root_dir, '_config_private.yml')
if os.path.isfile(private_config):
    config_files.append('_config_private.yml')
config_arg = ','.join(config_files)


log(f"Switching to repo root: {root_dir}")
os.chdir(root_dir)
log(f"Cleaning thumbnails directory: {thumbnail_dir}")
shutil.rmtree(thumbnail_dir, ignore_errors=True)
log("Running setup-photos script")
with open(setup_photos_script, 'r') as f:
    exec(f.read())

if args.push:
    log("Starting Jekyll build")
    if sys.platform != "win32":
        build_ret = call(['bundle','exec','jekyll', 'build', '--config', config_arg, '--destination','_site'])
    else:
        build_ret = os.system(f'bundle exec jekyll build --config {config_arg} --destination _site')
    log(f"Jekyll build exited with code {build_ret}")
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    log(f"Using commit {sha} for deploy")
    os.chdir(site_dir)

    log("Committing built site in _site repo")
    git_commit_ret = call(['git','commit', '-am', 'deploying from '+sha])
    if git_commit_ret == 0:
        log("Committed _site changes")
        web_dir = os.path.join(root_dir,'../website')
        log(f"Syncing to website repo located at: {web_dir}")
        os.chdir(web_dir)
        old_content = os.listdir(web_dir)
        log(f"Cleaning {web_dir}, preserving .git ({len(old_content)} entries)")
        for clean_up in old_content:
            if not clean_up.endswith('.git'):    
                remove(clean_up)
        log("Copying files from _site to website repo")
        copy_tree(site_dir, web_dir)
        log("Committing website repo")
        website_commit = call(['git','commit', '-am', 'deploying from '+sha])
        log(f"Website commit exit code: {website_commit}")
        if website_commit == 0:
            log("Website repo ready to push")
        else:
            log("Website repo commit failed")
    else:
        log('Deployment failed, could not commit _site')
else:
    log('Deployment not requested')

