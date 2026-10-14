# Test runner: Python, Playwright browsers and the test suite in one image.
# The tag must match the playwright version in requirements.txt.
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble

WORKDIR /tests

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY pyproject.toml .
COPY tests ./tests

CMD ["pytest", "-n", "4", "--html=reports/report.html", "--self-contained-html"]
