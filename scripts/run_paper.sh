#!/usr/bin/env bash
set -e
export MODE=paper
python -c "from dotenv import load_dotenv; load_dotenv(); import sys; sys.path.append('src'); from rqe.engine import run; run()"
