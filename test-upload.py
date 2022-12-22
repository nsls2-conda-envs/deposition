import datetime
import json
import os
import pprint
import subprocess
import sys
import time as ttime
from itertools import count

import requests

# BASE_URL = "https://sandbox.zenodo.org/api"
BASE_URL = "https://zenodo.org/api"


def print_now(*args):
    print(*args, file=sys.stdout, flush=True)


def upload_files(bucket_url, files, token):
    if files is None:
        raise ValueError(
            "Files cannot be None, specify a dict with file names "
            "as keys and access mode as values"
        )

    for file, mode in files.items():
        print_now(f"Uploading {file}...")
        ret = requests.put(
            f"{bucket_url}/{os.path.basename(file)}",
            params={"access_token": token},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/octet-stream",
                "Authorization": f"Bearer {token}",
            },
            data=open(file, mode),
        )
        print_now(ret.status_code, ret.text)


def create_new_version(
    conceptrecid=None, version=None, extra_files=None, token=None
):
    rec = requests.get(
        f"{BASE_URL}/records/{conceptrecid}",
        headers={"Authorization": f"Bearer {token}"},
    )

    ret_newver = requests.post(
        f"{BASE_URL}/deposit/depositions/{rec.json()['id']}/actions/newversion",
        params={"access_token": token},
    )
    print_now(ret_newver.url, ret_newver.status_code, ret_newver.json())

    newver_draft = ret_newver.json()["links"]["latest_draft"]

    notes_urls = [
        # non-tiled
        "https://github.com/nsls2-conda-envs/nsls2-collection/pull/13",
        "https://github.com/nsls2-conda-envs/nsls2-collection/actions/runs/3751019640",
        # need this empty line to enforce line break on Zenodo:
        "",
        # tiled
        "https://github.com/nsls2-conda-envs/nsls2-collection-tiled/pull/10",
        "https://github.com/nsls2-conda-envs/nsls2-collection-tiled/actions/runs/3751025176",
    ]
    notes_urls_strs = "<br>\n".join([f'<a href="{url}">{url}</a>'
                                     if url else ""
                                     for url in notes_urls])

    data = {
        "metadata": {
            "version": version,
            "title": f"NSLS-II collection conda environment {version} with Python 3.9 and Python 3.10",
            "description": "NSLS-II collection environment deployed to the experimental floor.",
            "upload_type": "software",
            "publication_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "prereserve_doi": True,
            "keywords": [
                "conda",
                "NSLS-II",
                "bluesky",
                "data acquisition",
                "conda-forge",
                "conda-pack",
            ],
            "notes": notes_urls_strs,
            "creators": [
                {
                    "name": "Rakitin, Maksim",
                    "affiliation": "NSLS-II, Brookhaven National Laboratory",
                    "orcid": "0000-0003-3685-852X",
                },
                {
                    "name": "Bischof, Garrett",
                    "affiliation": "NSLS-II, Brookhaven National Laboratory",
                    "orcid": "0000-0001-9351-274X",
                },
            ],
        }
    }

    resp_update = requests.put(
        newver_draft,
        params={"access_token": token},
        headers={"Content-Type": "application/json"},
        data=json.dumps(data),
    )
    print_now(newver_draft, resp_update.status_code, resp_update.text)

    for file in resp_update.json()["files"]:
        self_file = file["links"]["self"]
        r = requests.delete(self_file, params={"access_token": token})
        print_now(r.status_code, r.text)

    bucket_url = resp_update.json()["links"]["bucket"]

    all_files = {}
    if extra_files is not None:
        all_files.update(**extra_files)

    upload_files(bucket_url, files=all_files, token=token)

    # ret = requests.post(
    #     resp_update.json()["links"]["publish"], params={"access_token": token}
    # )
    # print_now(ret.status_code, ret.text)
    # return ret.json()


def update_deposition_with_files(conceptrecid=None, files=None, token=None):
    headers = {"Authorization": f"Bearer {token}"}

    rec = requests.get(
        f"{BASE_URL}/records/{conceptrecid}",
        headers=headers,
    )
    latest_published_id = rec.json()["id"]

    deposition = requests.get(
        f"{BASE_URL}/deposit/depositions/{latest_published_id}",
        headers=headers,
    )

    latest_draft_url = deposition.json()["links"]["latest_draft"]
    latest_draft = requests.get(
        latest_draft_url,
        headers=headers,
    )

    bucket_url = latest_draft.json()["links"]["bucket"]

    upload_files(bucket_url, files=files, token=token)


if __name__ == "__main__":

    conceptrecid = "4057062"
    version = "2023-1.0"
    token = os.environ["ZENODO_TOKEN"]

    resp = create_new_version(
        conceptrecid=conceptrecid,
        # version=f"{version}-tiled",
        version=f"{version}",
        token=token,
        extra_files={
            # # Python 3.8 (non-tiled)
            # f"{version}-py38-md5sum.txt": "r",
            # f"{version}-py38-sha256sum.txt": "r",
            # f"{version}-py38.yml": "r",
            # f"Dockerfile-{version}-py38": "r",
            # f"runner-{version}-py38.sh": "r",
            # f"{version}-py38.tar.gz": "rb",

            # Python 3.9 (non-tiled)
            f"{version}-py39-md5sum.txt": "r",
            f"{version}-py39-sha256sum.txt": "r",
            f"{version}-py39.yml": "r",
            f"Dockerfile-{version}-py39": "r",
            f"runner-{version}-py39.sh": "r",
            f"{version}-py39.tar.gz": "rb",

            # Python 3.10 (non-tiled)
            f"{version}-py310-md5sum.txt": "r",
            f"{version}-py310-sha256sum.txt": "r",
            f"{version}-py310.yml": "r",
            f"Dockerfile-{version}-py310": "r",
            f"runner-{version}-py310.sh": "r",
            f"{version}-py310.tar.gz": "rb",

            # # Python 3.8 (tiled)
            # f"{version}-py38-tiled-md5sum.txt": "r",
            # f"{version}-py38-tiled-sha256sum.txt": "r",
            # f"{version}-py38-tiled.yml": "r",
            # f"Dockerfile-{version}-py38-tiled": "r",
            # f"runner-{version}-py38-tiled.sh": "r",
            # f"{version}-py38-tiled.tar.gz": "rb",

            # Python 3.9 (tiled)
            f"{version}-py39-tiled-md5sum.txt": "r",
            f"{version}-py39-tiled-sha256sum.txt": "r",
            f"{version}-py39-tiled.yml": "r",
            f"Dockerfile-{version}-py39-tiled": "r",
            f"runner-{version}-py39-tiled.sh": "r",
            f"{version}-py39-tiled.tar.gz": "rb",

            # Python 3.10 (tiled)
            f"{version}-py310-tiled-md5sum.txt": "r",
            f"{version}-py310-tiled-sha256sum.txt": "r",
            f"{version}-py310-tiled.yml": "r",
            f"Dockerfile-{version}-py310-tiled": "r",
            f"runner-{version}-py310-tiled.sh": "r",
            f"{version}-py310-tiled.tar.gz": "rb",
        },
    )
    pprint.pprint(resp)

    # files = {
    #     # Python 3.8
    #     "2022-2.2-py38-md5sum.txt": "r",
    #     "2022-2.2-py38-sha256sum.txt": "r",
    #     "2022-2.2-py38.yml": "r",
    #     "Dockerfile-2022-2.2-py38": "r",
    #     "runner-2022-2.2-py38.sh": "r",
    #     "2022-2.2-py38.tar.gz": "rb",
    #     # Python 3.9
    #     "2022-2.2-py39-md5sum.txt": "r",
    #     "2022-2.2-py39-sha256sum.txt": "r",
    #     "2022-2.2-py39.yml": "r",
    #     "Dockerfile-2022-2.2-py39": "r",
    #     "runner-2022-2.2-py39.sh": "r",
    #     "2022-2.2-py39.tar.gz": "rb",
    # }

    # update_deposition_with_files(
    #     conceptrecid=conceptrecid, files=files, token=token
    # )
