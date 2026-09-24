run_mitgcm_with_hang_check() {
    local nprocs=$1
    local workdir=$2
    local forwadj=$3

    local LOG_FILE="STDOUT.0000"
    local TARGET="dyG"

    local CHECK_INTERVAL=1     # seconds
    local HANG_TIME=30         # seconds stuck on dyG
    local KILL_WAIT=5

    while true; do
        echo "$(date +%Y/%m/%d_%H:%M:%S.%3N) Starting MITgcm run..."

        # Truncate stdout so we only see output from *this* run
        : > "$LOG_FILE"

        mpiexec -n "${nprocs}" "${workdir}/mitgcmuv${forwadj}" &
        local MPI_PID=$!

        local dyG_seen=false
        local stuck_time=0
        local last_line=""

        while kill -0 "$MPI_PID" 2>/dev/null; do
            sleep "$CHECK_INTERVAL"

            current_line=$(tail -n 1 "$LOG_FILE" 2>/dev/null)

            # -------------------------------
            # Phase 1: wait until dyG appears
            # -------------------------------
            if [ "$dyG_seen" = false ]; then

                if echo "$current_line" | grep -q "$TARGET"; then
                    echo "Detected $TARGET. Beginning hang monitoring."
                    dyG_seen=true
                    last_line="$current_line"
                    stuck_time=0
                fi
                continue
            fi

            # ----------------------------------
            # Phase 2: monitor progress past dyG
            # ----------------------------------
            if [ "$current_line" = "$last_line" ]; then
                ((stuck_time+=CHECK_INTERVAL))
                echo "Still on $TARGET (${stuck_time}/${HANG_TIME}s)"
            else
                echo "Progress past $TARGET detected. Monitoring complete."
                wait "$MPI_PID"
                return $?
            fi

            if [ "$stuck_time" -ge "$HANG_TIME" ]; then
                echo "Executable hung on $TARGET. Killing MPI process $MPI_PID..."
                kill "$MPI_PID"
                sleep "$KILL_WAIT"
                pkill -9 "mitgcmuv${forwadj}"
                break   # restart outer while loop
            fi
        done

        echo "Restarting MITgcm after hang detection."
    done
}
