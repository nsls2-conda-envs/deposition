import datetime
import json
import os
import pprint
import subprocess
import time as ttime
from itertools import count

import requests

# BASE_URL = "https://sandbox.zenodo.org/api"
BASE_URL = "https://zenodo.org/api"

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
    print(ret_newver.url, ret_newver.status_code, ret_newver.json())

    newver_draft = ret_newver.json()["links"]["latest_draft"]

    data = {
        "metadata": {
            "version": version,
            "title": f"NSLS-II collection conda environment 2022-2.2 with Python 3.8 and 3.9",
            "description": "NSLS-II collection environment deployed to the experimental floor.",
            "upload_type": "software",
            "publication_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "prereserve_doi": True,
            "creators": [
                {
                    "name": "Rakitin, Maksim",
                    "affiliation": "NSLS-II, BNL",
                    "orcid": "0000-0003-3685-852X",
                }
            ],
        }
    }

    resp_update = requests.put(
        newver_draft,
        params={"access_token": token},
        headers={"Content-Type": "application/json"},
        data=json.dumps(data),
    )
    print(newver_draft, resp_update.status_code, resp_update.text)

    for file in resp_update.json()["files"]:
        self_file = file["links"]["self"]
        r = requests.delete(self_file, params={"access_token": token})
        print(r.status_code, r.text)

    all_files = {}
    if extra_files is not None:
        all_files.update(**extra_files)
    bucket_url = resp_update.json()["links"]["bucket"]
    for file, mode in all_files.items():
        ret = requests.put(
            f"{bucket_url}/{os.path.basename(file)}",
            params={"access_token": token},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/octet-stream",
            },
            data=open(file, mode),
        )
        print(ret.status_code, ret.text)

    # ret = requests.post(
    #     resp_update.json()["links"]["publish"], params={"access_token": token}
    # )
    # print(ret.status_code, ret.text)
    # return ret.json()


if __name__ == "__main__":
    counter = count(1)
    token = os.environ["ZENODO_TOKEN"]
    resp = create_new_version(
        conceptrecid="4057062", version="2022-2.2", token=token,
        extra_files={
            "2022-2.2-py39-tiled-md5sum.txt": "r",
            "2022-2.2-py39-tiled-sha256sum.txt": "r",
            "2022-2.2-py39-tiled.tar.gz": "rb",
            "2022-2.2-py39-tiled.yml": "r",
        }
    )
    pprint.pprint(resp)
