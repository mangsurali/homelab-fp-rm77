Baseline: constant 25 RPS - 300 (validasi pipeline)

cd ../cloud-dynamics-experiments
cp scenarios/constant.env scenarios/constant-300.env
sed -i 's/^DURATION=.*/DURATION=300/' scenarios/constant-300.env
TARGET_URL=http://cpu-bound.127.0.0.1.sslip.io/ REPLICATE=1 sh scripts/run-experiment.sh scenarios/constant-300.env