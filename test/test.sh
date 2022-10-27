#!/bin/bash

COMMAND="pdm run python smt.py"
TEST_FILES="test/data/*.hsp"
CHECKER_PATH="test/hsp-checker"

WRONG_COLOR='\033[0;31m'
CORRECT_COLOR='\033[0;32m'
NO_COLOR='\033[0m'

OK_STRING="No errors found. Everything seems to be ok!"

CORRECT_COUNT=0
TOTAL_COUNT=0
for fpath in $TEST_FILES; do
  f_dir="$(dirname "${fpath}")"
  f_input="$(basename -- "${fpath}")"
  f_expected="${f_input%.*}.out"
  f_output="${f_input%.*}.output"

  echo -n "Testing ${f_input}... "
  exec_time=$({ TIMEFORMAT=%R; time $COMMAND < "$f_dir/$f_input" > "$f_dir/$f_output"; }  2>&1)
  echo -n "${exec_time}s "

  echo -n "Checking output file..."
  checker_result=$("$CHECKER_PATH" "$f_dir/$f_input" "$f_dir/$f_output")
  output_cost=$(head -n 1 "$f_dir/$f_output")
  expected_cost=$(head -n 1 "$f_dir/$f_expected")

  if [ "$checker_result" != "$OK_STRING" ]; then
    echo -e "${WRONG_COLOR}NOT OK${NO_COLOR}"
    echo "$checker_result"
    echo ""
  elif [ "$output_cost" != "$expected_cost" ]; then
    echo -e "${WRONG_COLOR}NOT OK${NO_COLOR}"
    echo "Solution not optimal. Expected: ${expected_cost}. Got ${output_cost}."
    echo ""
  else
    echo -e "${CORRECT_COLOR}OK${NO_COLOR}"
    (( CORRECT_COUNT++ ))
  fi

  (( TOTAL_COUNT++ ))
done

echo ""
echo -e "${CORRECT_COLOR}${CORRECT_COUNT} OUT OF ${TOTAL_COUNT} TESTS PASSED${NO_COLOR}"