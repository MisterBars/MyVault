---
type: class
status: active
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - class
  - skill/python
  - skill/ai
reward_xp: 100
---

# Класс CodeAgent

## Назначение класса
Основной фасад проекта. Собирает OllamaClient, CodeRunner и FixLoop воедино.
Снаружи виден только один метод: `solve(task)`.
Вся оркестрация внутри - пользователю не нужно знать про детали реализации.

## Важные решения
- Dependency Injection: все зависимости передаются в конструктор, не создаются внутри.
- `solve()` возвращает `FixResult` - так caller сам решает что делать с результатом.
- Конфиг модели и таймаутов через dataclass `AgentConfig` - легко менять без правки кода.


## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task"
  AND project = this.project
  AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
const TYPES = ['module', 'class'];
const current = dv.current();
const currentProject = current.project;
if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject))
  .array();

async function getPyBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];
  const blocks = [];
  const re = /```python([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text)) !== null) blocks.push(m[1]);
  return blocks;
}

const reDef = /^\s*(?:async\s+)?def\s+(\w+)/m;
const reDefG = /^\s*(?:async\s+)?def\s+(\w+)/gm;

const procIndex = {};
for (const page of allPages) {
  const blocks = await getPyBlocks(page.file.path);
  for (const block of blocks) {
    let m;
    while ((m = reDefG.exec(block)) !== null) {
      const name = m[1];
      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({ modulePath: page.file.path, moduleLink: page.file.link });
    }
  }
}

const currentBlocks = await getPyBlocks(current.file.path);
const reCall = /\b(\w+)\s*\(/g;
const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentFunc = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('#')) continue;
    const defMatch = /^\s*(?:async\s+)?def\s+(\w+)/.exec(line);
    if (defMatch) { currentFunc = defMatch[1]; continue; }
    if (!currentFunc) continue;
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;
      for (const t of targets) {
        if (t.modulePath === current.file.path) continue;
        const key = `${currentFunc}||${t.modulePath}`;
        if (!callMap.has(key)) callMap.set(key, { fromFunc: currentFunc, toModuleLink: t.moduleLink, calledNames: new Set() });
        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];
for (const entry of callMap.values()) {
  rows.push([entry.fromFunc, entry.toModuleLink, Array.from(entry.calledNames).sort().join(', ')]);
}
if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/классов в рамках этого проекта не найдено.');
} else {
  dv.table(['Функция', 'Куда (модуль)', 'Что вызывает'], rows);
}
```

## Функции и методы

```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);
const blocks = [];
const re = /```python([\s\S]*?)```/g;
let m;
while ((m = re.exec(text)) !== null) blocks.push(m[1]);

const reDef = /^\s*(?:(async)\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([\w\[\], |None]+))?/;
const reTag = /^\s*#\s*@(\w+):\s*(.+)$/;

const rows = [];
for (const block of blocks) {
  const lines = block.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const dm = reDef.exec(lines[i]);
    if (!dm) continue;
    const isAsync = dm[1] ? 'async ' : '';
    const name = dm[2];
    const params = dm[3] ? dm[3].trim() : '';
    const returnType = dm[4] ? dm[4].trim() : '';
    const tags = { desc: '', role: '', todo: '' };
    let k = i + 1;
    while (k < lines.length) {
      const cur = lines[k].trim();
      if (cur === '') { k++; continue; }
      const tm = reTag.exec(lines[k]);
      if (!tm) break;
      const tn = tm[1].toLowerCase();
      if (Object.prototype.hasOwnProperty.call(tags, tn)) tags[tn] = tm[2].trim();
      k++;
    }
    rows.push([isAsync + name, params, returnType, tags.desc, tags.role, tags.todo]);
  }
}
if (rows.length === 0) {
  dv.paragraph('Функции и методы в коде не найдены.');
} else {
  dv.table(['Имя', 'Параметры', 'Возврат', 'Описание', 'Роль', 'TODO'], rows);
}
```

## Код

```python
from dataclasses import dataclass, field

# @desc: Конфигурация агента - модель, таймауты, количество попыток
# @role: Config
# @todo: Загружать из config.yaml или .env файла
@dataclass
class AgentConfig:
    model: str = "qwen2.5-coder:7b"
    runner_timeout: int = 10
    max_retries: int = 3
    ollama_url: str = "http://localhost:11434/api/generate"

class CodeAgent:
    def __init__(self, config: AgentConfig = None):
        # @desc: Инициализирует агента: создаёт клиент, раннер, петлю исправления и логгер
        # @role: Init
        # @todo: Принимать готовые зависимости снаружи для тестирования (full DI)
        import OllamaClient
        import Logger
        from CodeRunner import CodeRunner
        from FixLoop import FixLoop

        self.config = config or AgentConfig()
        self.logger = Logger
        self.client = OllamaClient
        self.runner = CodeRunner(timeout=self.config.runner_timeout)
        self.loop = FixLoop(
            ollama_client=self.client,
            code_runner=self.runner,
            logger=self.logger,
            max_retries=self.config.max_retries,
        )
        self.logger.info(f"CodeAgent готов. Модель: {self.config.model}")

    def solve(self, task: str):
        # @desc: Принимает задачу на русском языке, возвращает FixResult с кодом и результатом выполнения
        # @role: Public API
        # @todo: Добавить историю сессии - список всех выполненных задач
        return self.loop.solve(task)

    def interactive(self):
        # @desc: Интерактивный REPL-режим: читает задачи из stdin до ввода 'выход'
        # @role: CLI
        # @todo: Добавить сохранение истории сессии в файл
        self.logger.info("Интерактивный режим. Введи 'выход' для остановки.")
        while True:
            try:
                task = input("
Задача > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if task.lower() in ("выход", "exit", "quit", "q"):
                break
            if not task:
                continue
            result = self.solve(task)
            print("
--- Результат ---")
            if result.success:
                print(result.stdout)
            else:
                print(f"Не удалось решить за {result.attempts} попытки.")
                print("Последняя ошибка:", result.stderr)
        self.logger.close()

# --- Точка входа ---
if __name__ == "__main__":
    agent = CodeAgent()
    agent.interactive()
```

## Черновые заметки
