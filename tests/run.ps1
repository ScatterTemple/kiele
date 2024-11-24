$prefix = get-date -Format "MM月dd日 HH時mm分"
poetry run pytest --html="results/$prefix-report.html" -m "sample"
