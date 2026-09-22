FROM python:3.12-slim

# Create an unprivileged user.
RUN useradd \
    --create-home \
    --uid 10001 \
    sandboxuser

WORKDIR /workspace

# Only install what code inside the sandbox needs.
COPY requirements.txt /tmp/requirements.txt

RUN pip install \
    --no-cache-dir \
    -r /tmp/requirements.txt

# Make sandbox user own its workspace.
RUN mkdir -p /workspace && \
    chown -R sandboxuser:sandboxuser /workspace

USER sandboxuser

WORKDIR /workspace

CMD ["sleep", "infinity"]