curl -X POST http://127.0.0.1:5000/cic/api/classify \
     -H "Content-Type: application/json" \
     -H "X-Request-Source: cli" \
     -d @/absolute/path/to/test_payload.json
