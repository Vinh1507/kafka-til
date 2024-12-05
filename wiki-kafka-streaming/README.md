Consumer:

```bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic stream-topic --formatter kafka.tools.DefaultMessageFormatter --property print.timestamp=true --property print.key=true --property print.value=true --property print.partition=true --from-beginning --group my-first-application
```