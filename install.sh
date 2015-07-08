#! /bin/bash
#
# Prepares the environment for the project.
#

ENV_NAME="linux_env"
ACTION="install"
MODULES="BeautifulSoup PyStemmer Whoosh boilerpipe
feedparser guess-language kyotocabinet nltk"

VIRTUAL_ENV_2="virtualenv2"
VIRTUAL_ENV_N="virtualenv"
VIRTUAL_ENV=""

PIP_2="pip2"
PIP_N="pip"
PIP=""

SOURCE="source"
MKDIR="/usr/bin/mkdir"

is_cmd() {
    "$1" --version &> /dev/null && {
        return 0
    } 
    return 1
}

set_cmd(){
    if is_cmd $VIRTUAL_ENV_2; then 
        VIRTUAL_ENV=$VIRTUAL_ENV_2
    else
        if is_cmd $VIRTUAL_ENV_N; then
            VIRTUAL_ENV=$VIRTUAL_ENV_N
        else
            echo "Impossible de trouver virtualenv"
            return 1
        fi
    fi


    if is_cmd $PIP_2; then
        PIP=$PIP_2
    else
        if is_cmd $PIP_N; then
            PIP=$PIP_N
        else
            echo "Impossible de trouver pip"
            return 1
        fi
    fi
}

set_cmd

# Create virtual env
$MKDIR $ENV_NAME
$VIRTUAL_ENV $ENV_NAME --no-site-packages
$SOURCE $ENV_NAME/bin/activate

# Download modules
$PIP $ACTION $MODULES 

