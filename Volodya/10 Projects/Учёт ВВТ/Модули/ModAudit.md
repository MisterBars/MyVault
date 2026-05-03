---
type: module
status: done
done_date: 2026-05-02
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль
## Назначение

Кратко, за что отвечает модуль, какие задачи решает.

## Важные решения

- Почему выбрана такая архитектура.
- Комментарии по производительности/ограничениям.

## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
// Какие типы считаем VBA-кодом
const TYPES = ['module', 'form', 'class'];

// Проект текущего модуля (ссылка)
const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

// Фильтруем только те страницы, у которых такой же project
// p.project может быть ссылкой или массивом ссылок, поэтому используем dv.func.contains
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject));

// === Функция: вытащить все VBA-блоки ```vba из файла ===
async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!inBlock && trimmed.startsWith('```vba')) {
      inBlock = true;
      currentBlock = [];
      continue;
    }
    if (inBlock && trimmed.startsWith('```')) {
      inBlock = false;
      blocks.push(currentBlock.join('\n'));
      currentBlock = [];
      continue;
    }
    if (inBlock) currentBlock.push(line);
  }
  return blocks;
}

// Регэксп объявления процедур / функций (как в твоём шаблоне)
const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

// Индекс: имя процедуры → список мест, где она объявлена
const procIndex = {};

for (const page of allPages) {
  const vbaBlocks = await getVbaBlocks(page.file.path);

  for (const block of vbaBlocks) {
    const lines = block.split('\n');
    for (const line of lines) {
      const m = line.match(reProcDecl);
      if (!m) continue;

      const name = m[3];

      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({
        modulePath: page.file.path,
        moduleLink: page.file.link,
        moduleType: page.type
      });
    }
  }
}

// === Анализируем текущий модуль: кто кого вызывает ===

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const rows = [];

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // пропускаем комментарии
    if (trimmed.startsWith("'")) continue;

    // новая процедура / функция
    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    // ищем вызовы
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // если не хочешь самовызовы — можно фильтрануть
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        rows.push([
          current.file.link,   // Откуда (модуль)
          currentProc,         // Какая процедура
          t.moduleLink,        // Куда (модуль)
          calledName           // Что вызывает
        ]);
      }
    }
  }
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Откуда (модуль)', 'Процедура', 'Куда (модуль)', 'Что вызывает'],
    rows
  );
}
```
# Функции и процедуры
```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);

const vbaBlocks = [];
let inBlock = false;
let current = [];

for (const line of text.split("\n")) {
  if (line.trim().startsWith("```vba")) {
    inBlock = true;
    current = [];
    continue;
  }
  if (inBlock && line.trim().startsWith("```")) {
    inBlock = false;
    vbaBlocks.push(current.join("\n"));
    current = [];
    continue;
  }
  if (inBlock) current.push(line);
}

const re = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(re);
    if (!m) continue;

    const scopeRaw = m[1];               // Public / Private / undefined
    const kindRaw = m[2];                // Sub / Function
    const name = m[3];

    const kind = kindRaw.toLowerCase() === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw
      ? scopeRaw                       // "Public" или "Private"
      : "По умолчанию (Public)";       // ничего не указано → Public[web:369][web:375]

    let desc = "";
    if (i + 1 < lines.length) {
      const next = lines[i + 1].trim();
      const mDesc = next.match(/^'\s*@desc:\s*(.+)$/i);
      if (mDesc) desc = mDesc[1];
    }

    rows.push([name, kind, scope, desc]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(["Имя", "Тип", "Область", "Описание"], rows);
}
```
# Код
```vba
Option Explicit

' =========================
' Аудит
' =========================

Public Sub WriteAuditEvent( _
    ByVal db As DAO.Database, _
    ByVal tableName As String, _
    ByVal RecordID As Long, _
    ByVal fieldName As Variant, _
    ByVal oldValue As Variant, _
    ByVal newValue As Variant, _
    ByVal actionType As String, _
    ByVal businessEventType As String, _
    ByVal changedByUserId As Long, _
    Optional ByVal changeRequestId As Variant)
	' @desc: Функция записи логов в БД
    Dim rs As DAO.Recordset

    Set rs = db.OpenRecordset("AuditLog", dbOpenDynaset, dbAppendOnly)
    rs.AddNew

    rs.Fields("TableName").Value = Left$(NzStr(tableName), 100)
    rs.Fields("RecordID").Value = RecordID

    If Not IsMissingOrNull(fieldName) Then
        rs.Fields("FieldName").Value = Left$(NzStr(fieldName), 100)
    End If

    If Not IsMissingOrNull(oldValue) Then
        rs.Fields("OldValue").Value = NzStr(oldValue)
    End If

    If Not IsMissingOrNull(newValue) Then
        rs.Fields("NewValue").Value = NzStr(newValue)
    End If

    rs.Fields("ActionType").Value = Left$(NzStr(actionType), 10)
    rs.Fields("BusinessEventType").Value = Left$(NzStr(businessEventType), 50)

    If changedByUserId > 0 Then
        rs.Fields("ChangedByUserID").Value = changedByUserId
    End If

    If Not IsMissingOrNull(changeRequestId) Then
        rs.Fields("ChangeRequestID").Value = CLng(changeRequestId)
    End If
    
    On Error Resume Next
    rs.Fields("WorkstationName").Value = Left$(Environ$("COMPUTERNAME"), 100)
    On Error GoTo 0

    rs.Update
    rs.Close
    Set rs = Nothing
End Sub

Private Function IsMissingOrNull(ByVal v As Variant) As Boolean
    If IsObject(v) Then
        IsMissingOrNull = (v Is Nothing)
    ElseIf IsNull(v) Then
        IsMissingOrNull = True
    ElseIf IsEmpty(v) Then
        IsMissingOrNull = True
    ElseIf VarType(v) = vbString Then
        IsMissingOrNull = (Trim$(CStr(v)) = vbNullString)
    Else
        IsMissingOrNull = False
    End If
End Function

```

## Черновые заметки

