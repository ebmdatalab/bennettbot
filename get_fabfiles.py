import json
import os
import requests


with open('fabfiles.json', 'r') as f:
    fabfiles = json.load(f)
    for fabfile in fabfiles:
        proj_path = os.path.join('fabfiles', fabfile['project'])
        os.makedirs(proj_path, exist_ok=True)
        init_path = os.path.join(proj_path, '__init__.py')
        with open(init_path, 'w') as f:
            f.write("")
        fabfile_path = os.path.join(proj_path, 'fabfile.py')
        r = requests.get(fabfile['url'], stream=True)
        if r.status_code == 200:
            with open(fabfile_path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
        for fpath in fabfile['requires']:
            requires_path = os.path.join(proj_path, fpath)
            if not os.path.exists(requires_path):
                print("WARNING: we require a file at {}".format(
                    requires_path))
