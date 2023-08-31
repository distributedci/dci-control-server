FROM registry.access.redhat.com/ubi8/ubi-minimal

COPY . /usr/src/dci-control-server

COPY entrypoint.sh /usr/local/sbin/

WORKDIR /usr/src/dci-control-server

RUN microdnf update && \
    microdnf -y install python3-pip python3-wheel && \
    microdnf -y install python3-devel gcc postgresql-devel && \
    pip3 --no-cache-dir install -r requirements.txt && \
    pip3 --no-cache-dir install gunicorn && \
    pip3 --no-cache-dir install . && \
    microdnf -y remove python3-devel gcc postgresql-devel && \
    microdnf -y clean all

EXPOSE 5000

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:5000", "dci.app:create_app()"]
