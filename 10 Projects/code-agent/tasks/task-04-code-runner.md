---
type: task
task_type: dev
status: backlog
project: "[[code-agent]]"
deadline: 2026-06-01
reward_xp: 60
tags:
  - task
  - skill/python
---

# Задача: Реализовать CodeRunner

## Что нужно сделать
- [ ] Реализовать `_check_safety(code)` с BANNED_PATTERNS
- [ ] Реализовать `run(code) -> (stdout, stderr)` через subprocess + tempfile
- [ ] Тест 1: `print("hello")` -> `("hello\n", "")`
- [ ] Тест 2: `pritn("oops")` -> `("", "NameError: ...")`
- [ ] Тест 3: `while True: pass` -> `("", "TimeoutError: ...")`
- [ ] Тест 4: `os.system(...)` -> `("", "BLOCKED: ...")`
- [ ] Запустить все 4 теста в конце файла [[10 Projects/code-agent/Классы/CodeRunner]]

## Критерий выполнения
Все 4 теста проходят как ожидается.

## Заметки
