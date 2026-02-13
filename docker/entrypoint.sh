#!/bin/sh
set -e
python -c "from dotenv import load_dotenv; load_dotenv(); import sys; sys.path.append('src'); from rqe.engine import run; run()"
