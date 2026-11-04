FROM alpine:3.21

# Herramientas instaladas en build, no al arrancar: el laboratorio funciona sin internet.
RUN apk add --no-cache \
      nmap nmap-scripts curl bind-tools netcat-openbsd \
      hydra tcpdump openssh-client busybox-extras \
 && adduser -D -u 1000 student

COPY wordlists /usr/share/wordlists
WORKDIR /home/student
CMD ["tail", "-f", "/dev/null"]