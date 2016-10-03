#!/bin/sh -e

kvm-xfstests \
    --kernel /src-mirror/bzImage \
    -c $CFG_NAME -g auto

cp -r  /usr/local/lib/kvm-xfstests/logs $AVOCADO_TEST_OUTPUTDIR/


