#!/bin/bash

# export JAVA_HOME="$HOME/opt/java8"
NODE=$(hostname)
echo "Running on $NODE"
echo "Using Java at $JAVA_HOME"
"$JAVA_HOME/bin/java" -Xmx64m -version
echo "PATH=$PATH"

# export PATH="$HOME/miniconda2/bin:$PATH"
export GRADLE_OPTS="-Xmx128m -XX:+UseParallelGC"
GRADLE_HOME="/scratch/$USER/gradle-homes/$NODE"

ulimit -v unlimited
ulimit -u 512
ulimit -s 65536
ulimit -a
./gradlew -g "$GRADLE_HOME" --project-cache-dir ".gradle-$HOSTNAME" --no-daemon "$@"
