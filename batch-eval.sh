#!/bin/sh
#SBATCH --exclusive -c28 -N1

if [ -n "$SLACK_NOTIFY_USER" ]; then
    SLACK_TAG="<$SLACK_NOTIFY_USER>, "
fi

if [ -n SLACK_WEBHOOK_CLI_URL ]; then
    slack-hook send -m ":rocket: $SLACK_TAG we are starting job $SLURM_JOB_NAME!"
fi

srun ./run-eval.sh "$@"
ecode="$?"

if [ -n SLACK_WEBHOOK_CLI_URL ]; then
    if [ "$ecode" -eq 0 ]; then
        slack-hook send -m ":tada: $SLACK_TAG job $SLURM_JOB_NAME completed!"
    else
        slack-hook send -m ":skull: $SLACK_TAG job $SLURM_JOB_NAME is not happy"
    fi
fi
exit "$ecode"
