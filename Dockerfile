FROM python:3.10.0a4-slim-buster

RUN apt-get -y update && apt-get install -y git gpg && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /public-keys /repo /checker
WORKDIR "/repo"
COPY checker.py /checker/

ENTRYPOINT ["/checker/checker.py"]
CMD ["--git-dir", "/repo", "-l", "INFO", "--public-keys", "/public-keys"]
