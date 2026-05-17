---
type: class
status: planned
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - class
  - skill/python
  - skill/ai
reward_xp: 80
---

# Класс FixLoop

## Назначение класса
Механизм автоисправления ошибок для execution-сценариев worker-ветки.

В первой версии проекта `FixLoop` был одной из центральных сущностей: он получал задачу, просил LLM написать код, запускал код и при ошибке отправлял traceback обратно в модель.

В новой архитектуре `FixLoop` больше не является центральной логикой всего проекта.
Теперь это потенциальный вспомогательный механизм внутри `WorkerAgent`, если конкретная подзадача требует генерации и итеративного исправления Python-кода.

## Важные решения
- Разделение ответственности: `FixLoop` не знает про HTTP, `CodeRunner` не знает про LLM.
- Промпт для исправления ошибки - отдельный метод `_build_fix_prompt()`, чтобы легко менять.
- Логирование каждой попытки через `Logger`.


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
from dataclasses import dataclass

# @desc: Результат выполнения петли исправления
# @role: Data
# @todo: Добавить поле attempts_history для полного аудита всех попыток
@dataclass
class FixResult:
    success: bool
    stdout: str
    stderr: str
    attempts: int
    final_code: str

SYSTEM_PROMPT = (
    "Ты - Python-программист. Получаешь задачу на русском языке.\n"
    "Отвечаешь ТОЛЬКО кодом Python в блоке ```python```.\n"
    "Никаких пояснений. Только рабочий код."
)

FIX_PROMPT_TEMPLATE = (
    "Код упал с ошибкой:\n\n{error}\n\n"
    "Исходный код:\n```python\n{code}\n```\n\n"
    "Исправь код. Ответь ТОЛЬКО исправленным кодом Python в блоке ```python```."
)

class FixLoop:
    def __init__(self, ollama_client, code_runner, logger, max_retries: int = 3):
        # @desc: Инициализирует петлю с зависимостями (dependency injection)
        # @role: Init
        # @todo: Принимать конфиг вместо отдельных параметров
        self.client = ollama_client
        self.runner = code_runner
        self.logger = logger
        self.max_retries = max_retries

    def _build_task_prompt(self, task: str) -> str:
        # @desc: Строит первичный промпт для решения задачи
        # @role: Prompt
        # @todo: Добавить few-shot примеры для улучшения качества
        return f"Задача: {task}"

    def _build_fix_prompt(self, code: str, error: str) -> str:
        # @desc: Строит промпт для исправления кода с учётом ошибки
        # @role: Prompt
        # @todo: Добавить последние N строк stdout в контекст если они есть
        return FIX_PROMPT_TEMPLATE.format(code=code, error=error.strip())

    def solve(self, task: str) -> FixResult:
        # @desc: Решает задачу с авто-исправлением ошибок. Возвращает FixResult с финальным кодом и результатом
        # @role: Orchestration
        # @todo: Сохранять историю попыток в FixResult.attempts_history
        self.logger.separator(f"Решение задачи")
        self.logger.info(f"Задача: {task}")

        prompt = self._build_task_prompt(task)
        code = ""

        for attempt in range(1, self.max_retries + 1):
            self.logger.separator(f"Попытка {attempt}/{self.max_retries}")

            raw_response = self.client.ask(prompt, system=SYSTEM_PROMPT)
            code = self.client.extract_python_code(raw_response)
            self.logger.info(f"Код от LLM:\n{code}")

            stdout, stderr = self.runner.run(code)

            if stderr:
                self.logger.warn(f"Ошибка:\n{stderr}")
                if attempt < self.max_retries:
                    prompt = self._build_fix_prompt(code, stderr)
                    self.logger.info("Отправляем ошибку в LLM для исправления...")
                else:
                    self.logger.error("Исчерпаны все попытки.")
                    return FixResult(
                        success=False, stdout=stdout, stderr=stderr,
                        attempts=attempt, final_code=code,
                    )
            else:
                self.logger.info(f"Успех! Вывод:\n{stdout}")
                return FixResult(
                    success=True, stdout=stdout, stderr="",
                    attempts=attempt, final_code=code,
                )

        return FixResult(success=False, stdout="", stderr="Unknown error",
                         attempts=self.max_retries, final_code=code)

# --- Тест-запуск (мок-объекты, без реального Ollama) ---
if __name__ == "__main__":
    import re

    class MockLogger:
        def info(self, m): print(f"[INFO] {m}")
        def warn(self, m): print(f"[WARN] {m}")
        def error(self, m): print(f"[ERROR] {m}")
        def separator(self, l=""): print("=" * 40, l)

    class MockRunner:
        def __init__(self, fail_times=0):
            self.call_count = 0
            self.fail_times = fail_times
        def run(self, code):
            self.call_count += 1
            if self.call_count <= self.fail_times:
                return "", f"NameError: name 'wrong' is not defined (попытка {self.call_count})"
            return "42\n", ""

    class MockClient:
        def ask(self, prompt, system=""):
            return "```python\nprint(42)\n```"
        def extract_python_code(self, text):
            m = re.search(r'```python\s*([\s\S]*?)```', text)
            return m.group(1).strip() if m else text.strip()

    loop = FixLoop(MockClient(), MockRunner(fail_times=1), MockLogger(), max_retries=3)
    result = loop.solve("напиши print(42)")
    print("\n=== Результат ===")
    print("Успех:", result.success, "| Попыток:", result.attempts)
    print("Stdout:", repr(result.stdout))
```

## Черновые заметки
