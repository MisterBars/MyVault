---
type: snippet
lang: python
topic: requests
tags: [snippet, python]
---

# Python: базовый GET-запрос

```python
import requests

resp = requests.get("https://example.com/api", timeout=10)
resp.raise_for_status()
data = resp.json()
```

## Когда использовать
Когда нужно быстро получить JSON с API.
## На что обратить внимание
- добавить обработку ошибок;
- при необходимости вынести в функцию;
- не забыть таймаут.