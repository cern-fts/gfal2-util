#!/usr/bin/env bash
set -e

function print_info {
  printf "======================\n"
  printf "%-17s%s\n" "Distribution:" "${DIST}"
  printf "%-17s%s\n" "Dist name:" "${DISTNAME}"
  printf "%-17s%s\n" "Build type:" "${BUILD}"
  printf "%-17s%s\n" "Branch:" "${BRANCH}"
  printf "%-17s%s\n" "Release:" "${RELEASE}"
  printf "%-17s%s\n" "DMC Repository:" "${REPO_FILE}"
  printf "%-17s%s\n" "RPM build flags:" "${RPMBUILD_FLAGS}"
  printf "======================\n"
}

TIMESTAMP=$(git log -1 --format="%at" | xargs -I{} date -d @{} +%y%m%d%H%M)
GITREF=`git rev-parse --short HEAD`
RELEASE=r${TIMESTAMP}git${GITREF}
BUILD="devel"

if [[ -z ${BRANCH} ]]; then
  BRANCH=`git name-rev $GITREF --name-only`
else
  printf "Using environment set variable BRANCH=%s\n" "${BRANCH}"
fi

if [[ $BRANCH =~ ^(tags/)?(v)[.0-9]+(-(rc)?([0-9]+))?$ ]]; then
  RELEASE="${BASH_REMATCH[4]}${BASH_REMATCH[5]}"
  BUILD="rc"
fi

DIST=$(rpm --eval "%{dist}" | cut -d. -f2)
DISTNAME=${DIST}

# Special handling of FC rawhide
[[ "${DISTNAME}" == "fc41" ]] && DISTNAME="fc-rawhide"

# Write repository files to /etc/yum.repos.d/ based on the branch name
REPO_FILE=$(./ci/write-repo-file.sh)
print_info

RPMBUILD=${PWD}/build
SRPMS=${RPMBUILD}/SRPMS

cd packaging/
make srpm RELEASE=${RELEASE} RPMBUILD=${RPMBUILD} SRPMS=${SRPMS} RPMBUILD_SRC_EXTRA_FLAGS="${RPMBUILD_FLAGS}"
dnf builddep -y ${SRPMS}/*

rpmbuild --rebuild --define="_topdir ${RPMBUILD}" ${RPMBUILD_FLAGS} ${SRPMS}/*
