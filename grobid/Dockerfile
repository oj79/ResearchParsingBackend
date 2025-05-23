FROM grobid/grobid:0.8.2
EXPOSE 8070

# (Optional) only if you need to override the default config:
# COPY config.yml /opt/grobid/grobid-home/config/grobid.yaml
# └─ this replaces the built-in YAML under grobid-home/config :contentReference[oaicite:2]{index=2}

CMD ["./grobid-service/bin/grobid-service"]
