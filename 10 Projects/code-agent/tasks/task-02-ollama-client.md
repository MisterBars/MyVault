---
type: task
task_type: dev
status: backlog
project: "[[code-agent]]"
deadline: 2026-05-28
reward_xp: 50
tags:
  - task
  - skill/python
  - skill/ai
---

# Задача: Реализовать OllamaClient

## Что нужно сделать
- [ ] Реализовать `ask(prompt, model, system) -> str` через `requests.post`
- [ ] Реализовать `extract_python_code(text) -> str` через regex
- [ ] Реализовать `list_models() -> list[str]`
- [ ] Проверить что `ask()` бросает `RuntimeError` если Ollama не запущен
- [ ] Запустить тест-запуск в конце файла [[10 Projects/code-agent/Модули/OllamaClient]]

## Критерий выполнения
`ask("напиши fizzbuzz")` возвращает строку с Python-кодом. `extract_python_code` корректно вырезает блок.

## Заметки
