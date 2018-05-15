#!/bin/bash

set -e

OUT="/opt/scanning/saasherder_parser/images.txt"

rm -f $OUT

for saasrepo in $(cat repo_list); do
    pushd "${saasrepo}"

    [ -z "$NO_REFRESH" ] && git pull

    for context in `saasherder config get-contexts`; do
        [ -z "$context" ] && echo "Empty context" && exit 1

        if [ -z "$NO_REFRESH" ]; then
            rm -rf "${context}-out"
            saasherder --context "${context}" pull
            saasherder --environment production template --local --output-dir "${context}-out" tag
        fi

        for f in `ls ${context}-out/*`; do
            service=$(basename "$f" .yaml)
            git_hash=$(saasherder --context $context get hash $service)
            git_url=$(saasherder --context $context get url $service)
            images=$(yq -r '.items | .[] | select(.kind=="DeploymentConfig").spec.template.spec.containers | .[] | .image ' $f)

            for i in $images; do
                echo "${git_url};${git_hash};${i}" | tee -a "$OUT"
            done
        done
    done

    popd
done

echo "Output written to $OUT"
