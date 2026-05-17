---
type: task
task_type: dev
status: backlog
project: "[[code-agent]]"
deadline: 2026-06-08
reward_xp: 80
tags:
  - task
  - skill/python
  - skill/ai
---

# Задача: Реализовать FixLoop

## Что нужно сделать
- [ ] Реализовать `_build_task_prompt`, `_build_fix_prompt`, `solve` в [[10 Projects/code-agent/Классы/FixLoop]]
- [ ] Запустить тест-запуск с Mock-объектами (без реального Ollama)
- [ ] Убедиться что при `fail_times=1` агент делает 2 попытки и успешно завершает
- [ ] Убедиться что при `fail_times=3` возвращается `FixResult(success=False)`

## Критерий выполнения
Тест-запуск с моком проходит. Петля корректно обрабатывает ошибки и повторяет запросы.

## Заметки
