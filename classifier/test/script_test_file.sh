curl -X POST http://127.0.0.1:5000/cic/api/classify \
     -H "X-Request-Source: cli" \
     -F "file=@/absolute/path/to/test_file.json" \
     -F "mode=WS"