if [ -z "${VIRTUAL_ENV}" ]; then
    echo "Must be inside some venv. Aborting"
    exit
fi

RESULTS_DIR="results_$(date '+%Y-%m-%d_%H-%M-%S')"
mkdir -p "${RESULTS_DIR}"

python3 -m pip install -e ./environments/neuralinvariants/
python3 ./environments/neuralinvariants/run_experiment.py "$1" ./data "${RESULTS_DIR}"

rm -rf ./generated
