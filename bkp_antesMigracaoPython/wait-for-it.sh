#!/bin/bash
# wait-for-it.sh

# Original source: https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh

# Use this script to wait for a service to be available.
#
# Usage:
#   ./wait-for-it.sh host:port [-t timeout] [-- command args]
#
# Examples:
#   ./wait-for-it.sh db:5432 --timeout=30 -- echo "Database is up!"
#   ./wait-for-it.sh localhost:8080 -- /app/start_server.sh
#
# Options:
#   -t, --timeout=TIMEOUT   Timeout in seconds, default is 15.
#   -- COMMAND ARGS        Execute COMMAND with ARGS after the service is available.
#   -q, --quiet             Do not output any status messages.
#   -s, --strict            Ensure that only one of the provided hosts responds to the connection attempts.
#                           If multiple hosts respond, it will be considered a failure.
#   --                   Marks the end of options and the beginning of the command to execute.

cmdname=$(basename "$0")

echo_stderr() {
  if [ -z "$QUIET" ]; then
    printf "%s: %s\n" "$cmdname" "$*" >&2
  fi
}

usage() {
  cat << USAGE >&2
Usage:
  $cmdname host:port [-t timeout] [-- command args]
  -h, --help              Show this help message
  -q, --quiet             Do not output any status messages
  -s, --strict            Ensure that only one of the provided hosts responds to the connection attempts.
  -t, --timeout=TIMEOUT   Timeout in seconds, default is 15
  -- command args         Execute command with args after the service is available
USAGE
  exit 1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local timeout="$3"
  local strict="$4"
  local quiet="$5"

  local start_time=$(date +%s)
  local elapsed_time=0

  if [ -n "$timeout" ]; then
    echo_stderr "Waiting for $host:$port to be available, timeout is $timeout seconds"
  else
    echo_stderr "Waiting for $host:$port to be available"
  fi

  local success_count=0
  while [ "$elapsed_time" -lt "$timeout" ] || [ -z "$timeout" ]; do
    if nc -z "$host" "$port"; then
      echo_stderr "$host:$port is available!"
      success_count=$((success_count + 1))
      if [ -n "$strict" ] && [ "$success_count" -gt 1 ]; then
        echo_stderr "ERROR: Multiple successful connections in strict mode. Exiting."
        return 1
      fi
      return 0
    fi

    if [ -n "$timeout" ]; then
      elapsed_time=$(( $(date +%s) - start_time ))
    fi

    sleep 1
  done

  echo_stderr "Timeout occurred after $timeout seconds waiting for $host:$port"
  return 1
}

# Parse arguments
TIMEOUT=15
QUIET=""
STRICT=""
HOSTPORT=""
CMD=""

while [ $# -gt 0 ]; do
  case "$1" in
    *:*)
      HOSTPORT="$1"
      shift
      ;;
    -q|--quiet)
      QUIET="true"
      shift
      ;;
    -s|--strict)
      STRICT="true"
      shift
      ;;
    -t|--timeout)
      TIMEOUT="$2"
      if [ -z "$TIMEOUT" ]; then usage; fi
      shift 2
      ;;
    --timeout=*)
      TIMEOUT="${1#*=}"
      shift
      ;;
    --)
      shift
      CMD="$@"
      break
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo_stderr "Unknown argument: $1"
      usage
      ;;
  esac
done

if [ -z "$HOSTPORT" ]; then
  echo_stderr "Error: host:port argument is required."
  usage
fi

host=$(echo "$HOSTPORT" | cut -d: -f1)
port=$(echo "$HOSTPORT" | cut -d: -f2)

if [ -z "$host" ] || [ -z "$port" ]; then
  echo_stderr "Error: invalid host:port format. Expected host:port."
  usage
fi

wait_for_port "$host" "$port" "$TIMEOUT" "$STRICT" "$QUIET" || exit 1

if [ -n "$CMD" ]; then
  exec $CMD
else
  exit 0
fi