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

const reDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;
const reReturnType = /\)\s*As\s+([A-Za-z0-9_\.]+)/i;
const reTag = /^'\s*@([a-zA-Z0-9_]+):\s*(.+)$/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(reDecl);
    if (!m) continue;

    const scopeRaw = m[1];
    const kindRaw = m[2];
    const name = m[3];

    const kindLower = String(kindRaw ?? "").toLowerCase();
    const kind = kindLower === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw ? String(scopeRaw) : "По умолчанию (Public)";

    let j = i;
    while (j < lines.length - 1 && lines[j].trim().endsWith("_")) {
      j++;
    }

    const signatureLines = lines.slice(i, j + 1);
    const signatureText = signatureLines.join(" ");
    const mReturn = signatureText.match(reReturnType);
    const returnType = kind === "Функция" && mReturn ? String(mReturn[1]) : "";

    const tags = {
      desc: "",
      role: "",
      todo: ""
    };

    let k = j + 1;

    while (k < lines.length) {
      const cur = lines[k].trim();

      if (cur === "") {
        k++;
        continue;
      }

      const tagMatch = cur.match(reTag);
      if (!tagMatch) break;

      const tagName = String(tagMatch[1] ?? "").toLowerCase();
      const tagValue = String(tagMatch[2] ?? "").trim();

      if (Object.prototype.hasOwnProperty.call(tags, tagName)) {
        tags[tagName] = tagValue;
      }

      k++;
    }

    rows.push([
      name,
      kind,
      scope,
      returnType,
      tags.desc,
      tags.role,
      tags.todo
    ]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(
    ["Имя", "Тип", "Область", "Возврат", "Описание", "Роль", "TODO"],
    rows
  );
}
```
# Код
```vba
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе**
' @todo: **заметка по процедуре/функции**


Option Explicit

Private mItems As Collection

Public Sub SvcBuf_Init()
    Set mItems = New Collection
End Sub

Public Sub SvcBuf_Clear()
    Set mItems = Nothing
End Sub

Public Function SvcBuf_IsReady() As Boolean
    SvcBuf_IsReady = Not mItems Is Nothing
End Function

Private Function NewUserState( _
    ByVal userID As Long, _
    ByVal login As String, _
    ByVal fullName As String, _
    ByVal rightsByRole As Boolean, _
    ByVal hasDbLink As Boolean, _
    ByVal canEdit As Boolean, _
    ByVal canApprove As Boolean) As Object

    Dim d As Object
    Set d = CreateObject("Scripting.Dictionary")

    d("UserID") = userID
    d("Login") = login
    d("FullName") = fullName
    d("RightsByRole") = rightsByRole
    d("HasDbLink") = hasDbLink
    d("PendingDelete") = False
    d("CanEdit") = canEdit
    d("CanApprove") = canApprove

    Set NewUserState = d
End Function

Private Function SvcBuf_Key(ByVal userID As Long) As String
    SvcBuf_Key = "U" & CStr(userID)
End Function

Public Function SvcBuf_Exists(ByVal userID As Long) As Boolean
    Dim obj As Object
    On Error Resume Next
    Set obj = mItems(SvcBuf_Key(userID))
    SvcBuf_Exists = Not obj Is Nothing
    Set obj = Nothing
    On Error GoTo 0
End Function

Public Function SvcBuf_Get(ByVal userID As Long) As Object
    On Error Resume Next
    Set SvcBuf_Get = mItems(SvcBuf_Key(userID))
    On Error GoTo 0
End Function

Public Sub SvcBuf_AddOrReplace( _
    ByVal userID As Long, _
    ByVal login As String, _
    ByVal fullName As String, _
    ByVal rightsByRole As Boolean, _
    ByVal hasDbLink As Boolean, _
    ByVal canEdit As Boolean, _
    ByVal canApprove As Boolean)

    Dim key As String
    Dim obj As Object

    key = SvcBuf_Key(userID)

    On Error Resume Next
    mItems.Remove key
    On Error GoTo 0

    Set obj = NewUserState(userID, login, fullName, rightsByRole, hasDbLink, canEdit, canApprove)
    mItems.Add obj, key
End Sub

Public Sub SvcBuf_LoadFromServiceRecordset(ByVal rs As DAO.Recordset)
    Dim userID As Long
    Dim login As String
    Dim fullName As String
    Dim rightsByRole As Boolean
    Dim hasDbLink As Boolean
    Dim canEdit As Boolean
    Dim canApprove As Boolean

    Call SvcBuf_Init

    If rs Is Nothing Then Exit Sub
    If rs.EOF Then Exit Sub

    rs.MoveFirst
    Do While Not rs.EOF
        userID = NzLng(rs.Fields("UserID").Value)
        login = NzStr(rs.Fields("Login").Value)
        fullName = NzStr(rs.Fields("FullName").Value)
        rightsByRole = NzBool(rs.Fields("RightsByRole").Value, False)
        hasDbLink = NzBool(rs.Fields("HasUserServiceLink").Value, False)
        canEdit = (NzBool(rs.Fields("RoleCanEditAny").Value, False) Or NzBool(rs.Fields("LinkCanEdit").Value, False))
        canApprove = (NzBool(rs.Fields("RoleCanApproveAny").Value, False) Or NzBool(rs.Fields("LinkCanApprove").Value, False))

        Call SvcBuf_AddOrReplace(userID, login, fullName, rightsByRole, hasDbLink, canEdit, canApprove)
        rs.MoveNext
    Loop
End Sub

Public Sub SvcBuf_LoadForNewService(ByVal rsAllUsers As DAO.Recordset)
    Dim userID As Long
    Dim login As String
    Dim fullName As String
    Dim rightsByRole As Boolean
    Dim canEdit As Boolean
    Dim canApprove As Boolean

    Call SvcBuf_Init

    If rsAllUsers Is Nothing Then Exit Sub
    If rsAllUsers.EOF Then Exit Sub

    rsAllUsers.MoveFirst
    Do While Not rsAllUsers.EOF
        userID = NzLng(rsAllUsers.Fields("UserID").Value)
        login = NzStr(rsAllUsers.Fields("Login").Value)
        fullName = NzStr(rsAllUsers.Fields("FullName").Value)
        canEdit = NzBool(rsAllUsers.Fields("RoleCanEditAny").Value, False)
        canApprove = NzBool(rsAllUsers.Fields("RoleCanApproveAny").Value, False)
        rightsByRole = (canEdit Or canApprove)

        If rightsByRole Then
            Call SvcBuf_AddOrReplace(userID, login, fullName, True, False, canEdit, canApprove)
        End If

        rsAllUsers.MoveNext
    Loop
End Sub

Public Function SvcBuf_CountVisibleAssigned() As Long
    Dim i As Long
    Dim obj As Object
    If mItems Is Nothing Then Exit Function

    For i = 1 To mItems.Count
        Set obj = mItems(i)
        If NzBool(obj("PendingDelete"), False) = False Then
            SvcBuf_CountVisibleAssigned = SvcBuf_CountVisibleAssigned + 1
        End If
    Next i
End Function

Public Function SvcBuf_CanAppearInLeftList(ByVal userID As Long) As Boolean
    Dim obj As Object

    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then
        SvcBuf_CanAppearInLeftList = True
        Exit Function
    End If

    If NzBool(obj("RightsByRole"), False) = True Then
        SvcBuf_CanAppearInLeftList = False
    ElseIf NzBool(obj("PendingDelete"), False) = True Then
        SvcBuf_CanAppearInLeftList = True
    Else
        SvcBuf_CanAppearInLeftList = False
    End If
End Function

Public Function SvcBuf_AddLink( _
    ByVal userID As Long, _
    ByVal login As String, _
    ByVal fullName As String) As Boolean

    Dim obj As Object

    Set obj = SvcBuf_Get(userID)

    If obj Is Nothing Then
        Call SvcBuf_AddOrReplace(userID, login, fullName, False, False, False, False)
        SvcBuf_AddLink = True
        Exit Function
    End If

    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    obj("PendingDelete") = False
    SvcBuf_AddLink = True
End Function

Public Function SvcBuf_RemoveLink(ByVal userID As Long) As Boolean
    Dim obj As Object
    Dim key As String

    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then Exit Function
    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    If NzBool(obj("HasDbLink"), False) = True Then
        obj("PendingDelete") = True
    Else
        key = SvcBuf_Key(userID)
        On Error Resume Next
        mItems.Remove key
        On Error GoTo 0
    End If

    SvcBuf_RemoveLink = True
End Function

Public Function SvcBuf_ToggleEdit(ByVal userID As Long) As Boolean
    Dim obj As Object
    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then Exit Function
    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    obj("CanEdit") = Not NzBool(obj("CanEdit"), False)
    SvcBuf_ToggleEdit = True
End Function

Public Function SvcBuf_ToggleApprove(ByVal userID As Long) As Boolean
    Dim obj As Object
    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then Exit Function
    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    obj("CanApprove") = Not NzBool(obj("CanApprove"), False)
    SvcBuf_ToggleApprove = True
End Function

Public Function SvcBuf_Items() As Collection
    Set SvcBuf_Items = mItems
End Function

Public Sub NormalizeServiceUsersBufferAfterSave()
    Dim items As Collection
    Dim obj As Object
    Dim toRemove As Collection
    Dim key As Variant

    Set items = SvcBuf_Items
    If items Is Nothing Then Exit Sub

    Set toRemove = New Collection

    For Each obj In items
        If NzBool(obj("RightsByRole"), False) = False Then
            If NzBool(obj("PendingDelete"), False) = True Then
                toRemove.Add "U" & CStr(NzLng(obj("UserID")))
            Else
                obj("HasDbLink") = True
                obj("PendingDelete") = False
            End If
        End If
    Next obj

    For Each key In toRemove
        On Error Resume Next
        items.Remove CStr(key)
        On Error GoTo 0
    Next key
End Sub
```

## Черновые заметки

