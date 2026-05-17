---
type: class
status: active
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - class
  - skill/python
reward_xp: 60
---

# Класс CodeRunner

## Назначение класса
Безопасный запуск Python-кода в subprocess.
Принимает строку с кодом, запускает его с таймаутом, возвращает `(stdout, stderr)`.
Не знает ничего про LLM — только выполняет код.
В новой архитектуре этот класс рассматривается как execution-tool слой для `WorkerAgent`.
Он не является самостоятельным агентом и не отвечает за планирование.
## Важные решения
- `subprocess.run` с `capture_output=True` — перехватываем stdout и stderr раздельно.
- Таймаут 10 сек — защита от бесконечных циклов.
- Базовая проверка на запрещённые вызовы через regex перед запуском.
- Временный файл вместо `-c` флага — корректно обрабатывает многострочный код с отступами.


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
import sys
import subprocess
import tempfile
import os
import re

# @desc: Класс для безопасного запуска Python-кода в изолированном subprocess
# @role: Execution / Sandbox
# @todo: Добавить запуск в Docker-контейнере для полной изоляции

TIMEOUT_SECONDS = 10

BANNED_PATTERNS = [
    r"os\.system\s*\(",
    r"os\.popen\s*\(",
    r"shutil\.rmtree\s*\(",
    r"subprocess\.(?:call|Popen|run)\s*\(",
    r"open\s*\([^)]*['\"]w['\"]",      # открытие файлов на запись
    r"__import__\s*\(",
]

class CodeRunner:
    def __init__(self, timeout: int = TIMEOUT_SECONDS):
        # @desc: Инициализирует раннер с таймаутом в секундах
        # @role: Init
        # @todo: Принимать список доп. запрещённых паттернов снаружи
        self.timeout = timeout

    def _check_safety(self, code: str) -> tuple[bool, str]:
        # @desc: Проверяет код на запрещённые конструкции через regex
        # @role: Security
        # @todo: Перейти на AST-анализ для более надёжной проверки
        for pattern in BANNED_PATTERNS:
            if re.search(pattern, code):
                return False, f"BLOCKED: запрещённая конструкция: {pattern}"
        return True, ""

    def run(self, code: str) -> tuple[str, str]:
        # @desc: Запускает Python-код, возвращает (stdout, stderr). При блокировке или таймауте — возвращает ("", сообщение_об_ошибке)
        # @role: Execution
        # @todo: Добавить логирование через Logger каждой попытки запуска
        safe, reason = self._check_safety(code)
        if not safe:
            return "", reason

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", f"TimeoutError: код не завершился за {self.timeout} секунд"
        except Exception as e:
            return "", f"RunnerError: {e}"
        finally:
            os.unlink(tmp_path)

# ─── Тест-запуск ───
if __name__ == "__main__":
    runner = CodeRunner()

    # Тест 1: обычный вывод
    out, err = runner.run('print("hello from runner")')
    print("Тест 1 stdout:", repr(out))
    print("Тест 1 stderr:", repr(err))

    # Тест 2: синтаксическая ошибка
    out, err = runner.run('pritn("oops")')
    print("Тест 2 stdout:", repr(out))
    print("Тест 2 stderr:", repr(err))

    # Тест 3: таймаут
    out, err = runner.run('while True: pass')
    print("Тест 3 stdout:", repr(out))
    print("Тест 3 stderr:", repr(err))

    # Тест 4: блокировка
    out, err = runner.run('import os; os.system("echo pwned")')
    print("Тест 4 stdout:", repr(out))
    print("Тест 4 stderr:", repr(err))
```

## Черновые заметки
