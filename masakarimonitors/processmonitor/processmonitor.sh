#!/bin/bash

# Copyright(c) 2016 Nippon Telegraph and Telephone Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Define constants.
BASE_NAME=`basename $0`
TMP_DIR="/var/tmp"
TMP_CRM_MON_FILE="$TMP_DIR/crm_mon.tmp"
STATUS_FILE="$TMP_DIR/node_status.tmp"
TMP_CRMADM_FILE="$TMP_DIR/crmadmin.tmp"
NOTICE_OUTPUT="$TMP_DIR/${BASE_NAME}_resp.out"

SCRIPT_DIR=$(cd $(dirname $0);pwd)
SCRIPT_CHECK_PROCESS="$SCRIPT_DIR/process_status_checker.sh"
SCRIPT_COMMON_SH="$SCRIPT_DIR/common.sh"

DOWN_PROCESS_LIST="$TMP_DIR/badproc.list"

MASAKARI_API_SEND_PROGRAM=curl
MASAKARI_API_SEND_FAIL_FLG="off"

ALREADY_SEND_ID_LIST=()
LOGTAG=`basename $0`
P_HOST=`uname -n`

# Define the default setting.
DEFAULT_PROCESS_CHECK_INTERVAL=5
DEFAULT_PROCESS_REBOOT_RETRY=3
DEFAULT_REBOOT_INTERVAL=10
DEFAULT_MASAKARI_API_SEND_TIMEOUT=10
DEFAULT_MASAKARI_API_SEND_RETRY=12
DEFAULT_MASAKARI_API_SEND_DELAY=10


# This function locks a file
# Argument:
#   $1 : File name
file_lock () {
    exec 9>>$1
    flock -x 9
}

# This function unlocks a file
file_unlock () {
    exec 9>&-
}

# This function reads the configuration file and setting value.
# If the value is omitted, set the default value.
# If invalid value is set, return "1".
# Note) The default value for each item are as follows.
#       PROCESS_CHECK_INTERVAL (defualt : 60)
#       PROCESS_REBOOT_RETRY (default : 10)
#       REBOOT_INTERVAL (default : 3)
#       MASAKARI_API_SEND_TIMEOUT (defualt : 10)
#       MASAKARI_API_SEND_RETRY (default : 3)
#       MASAKARI_API_SEND_DELAY (default : 1)
#
# Return value:
#   0 : Setting completion
#   1 : Reading failure of the configuration or invalid setting value
#   2 : Omission of the required item
set_conf_value () {
    # Initialize setting
    unset PROCESS_CHECK_INTERVAL
    unset PROCESS_REBOOT_RETRY
    unset REBOOT_INTERVAL
    unset MASAKARI_API_SEND_TIMEOUT
    unset MASAKARI_API_SEND_RETRY
    unset MASAKARI_API_SEND_DELAY
    unset DOMAIN
    unset PROJECT
    unset ADMIN_USER
    unset ADMIN_PASS
    unset AUTH_URL
    unset REGION

    # Read configuration file
    source $SCRIPT_CONF_FILE > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        log_info "config file read error. [$SCRIPT_CONF_FILE]"
        return 1
    fi

    # Empty string is permitted. If there is no key itself, consider it as an error.

    # If the PROCESS_CHECK_INTERVAL is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $PROCESS_CHECK_INTERVAL | sed 's/[0-9]//g'`
    if [ "x" = "x${PROCESS_CHECK_INTERVAL}" ]; then
        PROCESS_CHECK_INTERVAL=$DEFAULT_PROCESS_CHECK_INTERVAL
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:PROCESS_CHECK_INTERVAL]"
        return 1
    fi
    log_debug "config file parameter : PROCESS_CHECK_INTERVAL=$PROCESS_CHECK_INTERVAL"

    # If the PROCESS_REBOOT_RETRY is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $PROCESS_REBOOT_RETRY | sed 's/[0-9]//g'`
    if [ "x" = "x${PROCESS_REBOOT_RETRY}" ]; then
        PROCESS_REBOOT_RETRY=$DEFAULT_PROCESS_REBOOT_RETRY
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:PROCESS_REBOOT_RETRY]"
        return 1
    fi
    log_debug "config file parameter : PROCESS_REBOOT_RETRY=$PROCESS_REBOOT_RETRY"

    # If the REBOOT_INTERVAL is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $REBOOT_INTERVAL | sed 's/[0-9]//g'`
    if [ "x" = "x${REBOOT_INTERVAL}" ]; then
        REBOOT_INTERVAL=$DEFAULT_REBOOT_INTERVAL
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:REBOOT_INTERVAL]"
        return 1
    fi
    log_debug "config file parameter : REBOOT_INTERVAL=$REBOOT_INTERVAL"

    # If the MASAKARI_API_SEND_TIMEOUT is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $MASAKARI_API_SEND_TIMEOUT | sed 's/[0-9]//g'`
    if [ "x" = "x${MASAKARI_API_SEND_TIMEOUT}" ]; then
        MASAKARI_API_SEND_TIMEOUT=$DEFAULT_MASAKARI_API_SEND_TIMEOUT
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:MASAKARI_API_SEND_TIMEOUT]"
        return 1
    fi
    log_debug "config file parameter : MASAKARI_API_SEND_TIMEOUT=$MASAKARI_API_SEND_TIMEOUT"

    # If the MASAKARI_API_SEND_RETRY is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $MASAKARI_API_SEND_RETRY | sed 's/[0-9]//g'`
    if [ "x" = "x${MASAKARI_API_SEND_RETRY}" ]; then
        MASAKARI_API_SEND_RETRY=$DEFAULT_MASAKARI_API_SEND_RETRY
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:MASAKARI_API_SEND_RETRY]"
        return 1
    fi
    log_debug "config file parameter : MASAKARI_API_SEND_RETRY=$MASAKARI_API_SEND_RETRY"

    # If the MASAKARI_API_SEND_DELAY is omitted, set the default value.
    # If invalid is set, return 1.
    expect_empty=`echo -n $MASAKARI_API_SEND_DELAY | sed 's/[0-9]//g'`
    if [ "x" = "x${MASAKARI_API_SEND_DELAY}" ]; then
        MASAKARI_API_SEND_DELAY=$DEFAULT_MASAKARI_API_SEND_DELAY
    elif [ "x" != "x${expect_empty}" ]; then
        log_info "config file parameter error. [$SCRIPT_CONF_FILE:MASAKARI_API_SEND_DELAY]"
        return 1
    fi
    log_debug "config file parameter : MASAKARI_API_SEND_DELAY=$MASAKARI_API_SEND_DELAY"

    # If the DOMAIN is omitted, return 1.
    if [ "x" = "x${DOMAIN}" ]; then
        log_info "config file parameter error. [$DOMAIN:DOMAIN]"
        return 1
    else
        log_debug "config file parameter : DOMAIN=$DOMAIN"
    fi

    # If the PROJECT is omitted, return 1.
    if [ "x" = "x${PROJECT}" ]; then
        log_info "config file parameter error. [$PROJECT:PROJECT]"
        return 1
    else
        log_debug "config file parameter : PROJECT=$PROJECT"
    fi

    # If the ADMIN_USER is omitted, return 1.
    if [ "x" = "x${ADMIN_USER}" ]; then
        log_info "config file parameter error. [$ADMIN_USER:ADMIN_USER]"
        return 1
    else
        log_debug "config file parameter : ADMIN_USER=$ADMIN_USER"
    fi

    # If the ADMIN_PASS is omitted, return 1.
    if [ "x" = "x${ADMIN_PASS}" ]; then
        log_info "config file parameter error. [$ADMIN_PASS:ADMIN_PASS]"
        return 1
    else
        log_debug "config file parameter : ADMIN_PASS=$ADMIN_PASS"
    fi

    # If the AUTH_URL is omitted, return 1.
    if [ "x" = "x${AUTH_URL}" ]; then
        log_info "config file parameter error. [$AUTH_URL:AUTH_URL]"
        return 1
    else
        log_debug "config file parameter : AUTH_URL=$AUTH_URL"
    fi

    # If the REGION is omitted, return 1.
    if [ "x" = "x${REGION}" ]; then
        log_info "config file parameter error. [$REGION:REGION]"
        return 1
    else
        log_debug "config file parameter : REGION=$REGION"
    fi

    return 0
}

# Initial startup command execution method:
# This method does not execute same command as startup command that executed once.

init_boot() {
    log_debug "init_boot start"
    CMD_LIST=()
    for line in "${proc_list[@]}"
    do
        ALREADY_FLG="off"
        CMD=`echo ${line} | cut -d"," -f 3`
        SPECIAL_BEFORE=`echo $line | cut -d"," -f 5`
        SPECIAL_AFTER=`echo $line | cut -d"," -f 6`

        # If there is no startup command, can proceed to the next command.
        if [ -z "$CMD" ]; then
            continue
        fi

        # Check whether already is executed.
        for CHECK_CMD in "${CMD_LIST[@]}"
        do
            if [ "$CHECK_CMD" = "$CMD" ]; then
                ALREADY_FLG="on"
                break
            fi
        done

        # Execute special processing before the initial startup.
        if [ ! -z "$SPECIAL_BEFORE" ]; then
            $SPECIAL_BEFORE
        fi

        # If not be executed, execute start command.
        if [ "$ALREADY_FLG" = "off" ]; then
            OLD_IFS=$IFS
            IFS=';'
            set -- $CMD
            CMD_SPLIT_LIST=("$@")
            IFS=$OLD_IFS
            for SPLIT_CMD in "${CMD_SPLIT_LIST[@]}"
            do
                $SPLIT_CMD > /dev/null 2>&1
            done

            CMD_LIST=("$CMD_LIST" "$CMD")
        fi

        # Execute special processing after the initial startup.
        if [ ! -z "$SPECIAL_AFTER" ]; then
            $SPECIAL_AFTER
        fi
    done
    log_debug "init_boot end"
}

# This function creates data that is notified to the masakari api.
# It is called from the child process.
#
make_notice_data () {
    TIME=`date -u +'%Y-%m-%d %H:%M:%S'`

    PAYLOAD="{\"event\": \"STOPPED\", \"process_name\": \"${PROCESS_NAME}\"}"

}



# This function notifies to the masakari api.
# It is called masakari_cli post_event method.
send_notification () {
    TYPE="PROCESS"
    TARGET="post_event"
    AUTH_INFO="--os-domain-name ${DOMAIN} --os-project-name ${PROJECT} --os-region-name ${REGION} --os-auth-url ${AUTH_URL} --os-username ${ADMIN_USER} --os-password ${ADMIN_PASS}"

    log_info "info : Send a notification."
    log_info "info : openstack ${AUTH_INFO} notification create ${TYPE} ${P_HOST} \"${TIME}\" \"${PAYLOAD}\""

    RESP=`openstack ${AUTH_INFO} notification create ${TYPE} ${P_HOST} "${TIME}" "${PAYLOAD}"`
    result=$?

    if [ $result -eq 0 ]; then
        log_info "info : Succeeded in sending a notification."
        log_info "info : $RESP"
    else
        log_info "info : Failed to send a notification. [exit-code: $result]"
        log_info "info : $RESP"
        MASAKARI_API_SEND_FAIL_FLG="on"
    fi

    return

}

# Attempt to restart the failer process.
# If failure to number of retries, notify to the masakari api.

down_process_reboot(){
    ALREADY_REBOOT_CMD_LIST=()
    while read line
    do
        ALREADY_FLG="off"
        # No processing is executed about process id included in the send list.
        for already_id in "${ALREADY_SEND_ID_LIST[@]}"
        do
            if [ "$line" = "$already_id" ]; then
                ALREADY_FLG="on"
                break
            fi
        done

        if [ "$ALREADY_FLG" = "on" ]; then
            continue
        fi

        for proc in "${proc_list[@]}"
        do
            PROC_ID=`echo $proc | cut -d"," -f 1`
            if [ "$line" = "$PROC_ID" ] ; then
                CMD=`echo $proc | cut -d"," -f 4`
                PROCESS_NAME=`echo $proc | cut -d"," -f 2`
                SPECIAL_BEFORE=`echo $proc | cut -d"," -f 7`
                SPECIAL_AFTER=`echo $proc | cut -d"," -f 8`
                break
            fi
        done

        if [ ! -z "$SPECIAL_BEFORE" ]; then
            $SPECIAL_BEFORE
        fi

        # If there is not restart command, can proceed to the next command.
        if [ -z "$CMD" ]; then
            continue
        fi

        RESULT_FLG=1
        # Decomposes multiple processing be joined by ";" and execute them. (restart execution part)
        OLD_IFS=$IFS
        IFS=';'
        set -- $CMD
        CMD_SPLIT_LIST=("$@")
        IFS=$OLD_IFS
        for SPLIT_CMD in "${CMD_SPLIT_LIST[@]}"
        do
            ALREADY_FLG="off"
            # Check whether already is executed.
            for CHECK_CMD in "${ALREADY_REBOOT_CMD_LIST[@]}"
            do
                if [ "$CHECK_CMD" = "$SPLIT_CMD" ]; then
                    ALREADY_FLG="on"
                    break
                fi
            done
            # If is already executed, skip.
            if [ "$ALREADY_FLG" = "on" ]; then
                continue
            fi

            log_debug "reboot cmd:$SPLIT_CMD"
            $SPLIT_CMD > /dev/null 2>&1
            if [ $? -ne 0 ]; then
                RESULT_FLG=0
                break
            else
                ALREADY_REBOOT_CMD_LIST=("$ALREADY_REBOOT_CMD_LIST" "$SPLIT_CMD")
            fi
        done

        # If fail to restart, executes retry restart.
        if [ $RESULT_FLG -ne 1 ]; then
            result=0
            for retry in `seq $PROCESS_REBOOT_RETRY`
            do
                sleep $REBOOT_INTERVAL
                # Retry the restart processing.
                RESULT_FLG=1
                for SPLIT_CMD in "${CMD_SPLIT_LIST[@]}"
                do
                    ALREADY_FLG="off"
                    # Check whether already is executed.
                    for CHECK_CMD in "${ALREADY_REBOOT_CMD_LIST[@]}"
                    do
                        if [ "$CHECK_CMD" = "$SPLIT_CMD" ]; then
                            ALREADY_FLG="on"
                            break
                        fi
                    done
                    # If is already executed, skip.
                    if [ "$ALREADY_FLG" = "on" ]; then
                        continue
                    fi
                    log_debug "reboot cmd:$SPLIT_CMD"
                    $SPLIT_CMD > /dev/null 2>&1
                    if [ $? -ne 0 ]; then
                        RESULT_FLG=0
                        break
                    else
                        ALREADY_REBOOT_CMD_LIST=("$ALREADY_REBOOT_CMD_LIST" "$SPLIT_CMD")
                    fi
                done
                if [ $RESULT_FLG -eq 1 ]; then
                    break
                elif [ $retry -eq $PROCESS_REBOOT_RETRY ]; then
                    # If number of retries is exceeded, notify to the masakari api.
                    make_notice_data
                    if [ $result -eq 0 ]&&
                       [ "$MASAKARI_API_SEND_FAIL_FLG" = "off" ]; then
                        send_notification
                    fi
                    # Add the sent list.
                    ALREADY_SEND_ID_LIST=("${ALREADY_SEND_ID_LIST[@]}" "${line}")
                fi
            done
        fi

        # Special processes after restart.
        if [ ! -z "$SPECIAL_AFTER" ]; then
            $SPECIAL_AFTER
        fi


    done < $DOWN_PROCESS_LIST
}


# Argument check
if [ $# -ne 2 ]; then
    echo "Usage: $0 <configuration file path> <proc.list file path>"
    exit 1
else
    SCRIPT_CONF_FILE=$1
    PROC_LIST=$2
fi

# Initial processing (check proc.list and read conf file)
. $SCRIPT_COMMON_SH

# Output warning message.
log_info "WARNING : $0 is deprecated as of the Ocata release and will be removed in the Queens release. Use masakari-processmonitor implemented in python instead of $0."

log_debug "processmonitor start!!"
check_proc_file_common
set_conf_value
if [ $? -ne 0 ]; then
    exit 1
fi

if [ -e $NOTICE_OUTPUT ]; then
    sudo rm -rf $NOTICE_OUTPUT
fi

# Initial startup
init_boot

while true
do
    # Recheck and reload of the proc.list.
    check_proc_file_common
    # If invalid value is set to configuration file, set default value.
    set_conf_value

    if [ $? -ne 0 ]; then
       exit 1
    fi

    # Execute process check processing.
    ${SCRIPT_CHECK_PROCESS} ${PROC_LIST}
    RESULT_CODE=$?

    # If the return code is 2, because can't continue functionally, stop.
    if [ $RESULT_CODE -eq 2 ]; then
        log_debug "process_status_checker down!"
        exit 1
    fi

    # If the failing process is detected by shell check, retry restart.
    if [ $RESULT_CODE -ne 0 ]; then
        down_process_reboot
    fi

    sleep ${PROCESS_CHECK_INTERVAL}
done
