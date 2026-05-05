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
# Назначение
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
const TYPES = ['module', 'form', 'class'];

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

// Диагностика — сохраняем, но не показываем
const debugModulesCount = allPages.length;

async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();

    if (!inBlock && trimmed.toLowerCase().startsWith('```vba')) {
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

const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;
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

// Диагностика — сохраняем, но не показываем
const debugProcNames = Object.keys(procIndex);
const debugProcCount = debugProcNames.length;

const currentBlocks = await getVbaBlocks(current.file.path);

// будем искать вызовы более аккуратно:
// 1) Call Name ...
// 2) Name(...)
// 3) Name <что-то>, но не Name =, не Dim Name, не Set Name =
const reCallPattern = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\b/g;

const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed.startsWith("'")) continue;

    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    // Не считать строки, где имя функции слева от "=":
    //   FuncName = ...
    //   Set obj = ...
    //   Dim FuncName As ...
    // Обработаем это внутри цикла по совпадениям.

    let m;
    while ((m = reCallPattern.exec(line)) !== null) {
      const calledName = m[1];

      // Позиция найденного имени в строке
      const idx = m.index;

      // Левая часть строки до имени
      const before = line.slice(0, idx);
      const after = line.slice(idx + calledName.length);

      const beforeTrim = before.trim();
      const afterTrim = after.trimStart();

      // 1) Если это присваивание результата функции: "FuncName = ..."
      //    — имя стоит в начале строки / после пробелов, а сразу после него "="
      const isAssignmentResult =
        beforeTrim === "" && afterTrim.startsWith("=");

      if (isAssignmentResult) {
        // Это возврат из функции, НЕ вызов
        continue;
      }

      // 2) Если это объявление переменной: "Dim FuncName As ..."
      if (/^\s*Dim\s+$/i.test(before) || /^\s*Dim\s+/i.test(beforeTrim)) {
        continue;
      }

      // 3) Если это левая часть Set: "Set obj = ..."
      //    — нас интересуют вызовы, а не имя слева от Set/=
      if (/^\s*Set\s+$/i.test(before) || /^\s*Set\s+/i.test(beforeTrim)) {
        continue;
      }

      // 4) Если после имени нет "(", нет пробела + аргументов, и нет "Call",
      //    можно попасть в кучу ложных срабатываний. Но:
      //    - уже отсекли очевидные присваивания и Dim/Set.
      //    - оставим это как потенциальный вызов (вызов без скобок: Name arg1, arg2).
      //    При желании можно ещё проверить, что после имени не конец строки и не оператор.

      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // не считаем самовызов внутри того же модуля той же процедуры
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        const key = `${currentProc}||${t.modulePath}`;
        if (!callMap.has(key)) {
          callMap.set(key, {
            fromProc: currentProc,
            toModuleLink: t.moduleLink,
            calledNames: new Set()
          });
        }

        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];
for (const entry of callMap.values()) {
  const calledList = Array.from(entry.calledNames).sort().join(", ");
  rows.push([
    entry.fromProc,
    entry.toModuleLink,
    calledList
  ]);
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Процедура', 'Куда (модуль)', 'Что вызывает'],
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

' --- ИНИЦИАЛИЗАЦИЯ И СОСТОЯНИЕ ---

Public Sub SvcBuf_Init()
' @desc: Создаёт новый пустой экземпляр коллекции mItems. Сбрасывает любое предыдущее состояние буфера. 
' @role: Точка входа перед любой загрузкой данных в буфер. Вызывается из SvcBufLoadFromServiceRecordset и SvcBufLoadForNewService. 
' @todo: Нет. Вызов корректен, Collection не требует явного размера.
    Set mItems = New Collection
End Sub

Public Sub SvcBuf_Clear()
' @desc: Уничтожает коллекцию mItems (Set mItems = Nothing). Буфер после этого недоступен до следующего SvcBufInit. 
' @role: Явная очистка при закрытии формы или отмене операции. 
' @todo: Рекомендуется вызывать в UserForm_Terminate / BtnCanselClick чтобы не держать Scripting.Dictionary объекты в памяти.
    Set mItems = Nothing
End Sub

Public Function SvcBuf_IsReady() As Boolean
' @desc: Возвращает True, если буфер инициализирован (mItems не Nothing). 
' @role: Guard-проверка перед любым обращением к буферу. Позволяет избежать ошибки при вызове методов на неинициализированном буфере. 
' @todo: Использовать как первую проверку в процедурах, работающих с буфером.
    SvcBuf_IsReady = Not mItems Is Nothing
End Function

' --- ВНУТРЕННИЕ ХЕЛПЕРЫ ---

Private Function NewUserState( _
    ByVal userID As Long, _
    ByVal login As String, _
    ByVal fullName As String, _
    ByVal rightsByRole As Boolean, _
    ByVal hasDbLink As Boolean, _
    ByVal canEdit As Boolean, _
    ByVal canApprove As Boolean) As Object
    ' @desc: Создаёт и возвращает Scripting.Dictionary с полями одной записи пользователя: UserID, Login, FullName, RightsByRole, HasDbLink, PendingDelete (всегда False при создании), CanEdit, CanApprove. 
    ' @role: Фабричная функция-конструктор для элемента коллекции mItems. Единственное место, где задаётся структура "строки" буфера. 
    ' @todo: Если в будущем появятся новые поля состояния — добавлять только здесь. Рассмотреть замену Dictionary на Class-модуль для строгой типизации.

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
' @desc: Формирует строковый ключ для коллекции в формате "U<userID>". Например: userID=5 → "U5". 
' @role: Единое место формирования ключа; исключает разночтение формата при добавлении, поиске и удалении из коллекции. 
' @todo: Нет. Формат простой и достаточный.
    SvcBuf_Key = "U" & CStr(userID)
End Function

' --- ДОСТУП К ЭЛЕМЕНТАМ ---

Public Function SvcBuf_Exists(ByVal userID As Long) As Boolean
' @desc: Проверяет наличие пользователя с указанным userID в буфере. Использует On Error Resume Next для безопасного обращения к коллекции. 
' @role: Используется перед SvcBufGet и SvcBufAddOrReplace для условных проверок. 
' @todo: Нет. Паттерн с On Error Resume Next — стандартный для VBA Collection lookup.
    Dim obj As Object
    On Error Resume Next
    Set obj = mItems(SvcBuf_Key(userID))
    SvcBuf_Exists = Not obj Is Nothing
    Set obj = Nothing
    On Error GoTo 0
End Function

Public Function SvcBuf_Get(ByVal userID As Long) As Object
' @desc: Проверяет наличие пользователя с указанным userID в буфере. Использует On Error Resume Next для безопасного обращения к коллекции. 
' @role: Используется перед SvcBufGet и SvcBufAddOrReplace для условных проверок. 
' @todo: Нет. Паттерн с On Error Resume Next — стандартный для VBA Collection lookup.
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
    ' @desc: Добавляет нового пользователя в буфер или заменяет существующего. При замене сначала удаляет старый элемент коллекции, затем добавляет новый. 
    ' @role: Единственный публичный способ записи/перезаписи элемента в буфер. Вызывается из SvcBufLoadFromServiceRecordset и SvcBufLoadForNewService, а также из SvcBufAddLink при добавлении нового пользователя вручную. 
    ' @todo: Нет. Паттерн Remove + Add на Collection — стандартный способ upsert.

    Dim key As String
    Dim obj As Object

    key = SvcBuf_Key(userID)

    On Error Resume Next
    mItems.Remove key
    On Error GoTo 0

    Set obj = NewUserState(userID, login, fullName, rightsByRole, hasDbLink, canEdit, canApprove)
    mItems.Add obj, key
End Sub

' --- ЗАГРУЗКА ДАННЫХ ---

Public Sub SvcBuf_LoadFromServiceRecordset(ByVal rs As DAO.Recordset)
' @desc: Заполняет буфер из Recordset существующей службы. Ожидает поля: UserID, Login, FullName, RightsByRole, HasUserServiceLink, RoleCanEditAny, LinkCanEdit, RoleCanApproveAny, LinkCanApprove. CanEdit и CanApprove вычисляются как OR роли и явной ссылки. 
' @role: Используется при открытии формы редактирования существующей службы (ActionBut = Change). Recordset приходит из GetUsersByService(serviceID). 
' @todo: Проверить, что GetUsersByService возвращает все нужные поля с точными именами. При изменении запроса — синхронизировать имена полей здесь.
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
' @desc: Заполняет буфер для новой службы (ещё не сохранённой в БД). Загружает только пользователей, у которых есть права по роли (CanEditAny или CanApproveAny = True). HasDbLink = False для всех. 
' @role: Используется при открытии формы создания новой службы (ActionBut = Add). Recordset приходит из GetUsersForNewService. 
' @todo: Нет. Логика фильтрации по rightsByRole корректна.
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

' --- ПОДСЧЁТ И ВИДИМОСТЬ ---

Public Function SvcBuf_CountVisibleAssigned() As Long
' @desc: Считает количество пользователей в буфере, у которых PendingDelete = False. Те, кто помечен на удаление, в счёт не входят. 
' @role: Используется в RefreshUsersByServiceList для корректного выделения памяти под массив dataArr. 
' @todo: Нет. Логика простая и понятная.
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
' @desc: Определяет, должен ли пользователь отображаться в левом списке (LBUserWOService — "пользователи без службы"). Правила: - пользователь не в буфере → True (показать) - RightsByRole = True → False (скрыть, права по роли — всегда в правом) - PendingDelete = True → True (показать, ссылка помечена к удалению) - иначе → False (пользователь уже назначен) 
' @role: Фильтр отображения в RefreshUsersWithoutServiceList. ' Определяет, кого можно добавить к службе вручную. 
' @todo: Нет. Логика корректна и покрывает все случаи.
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

' --- ИЗМЕНЕНИЕ СОСТОЯНИЯ ---

Public Function SvcBuf_AddLink( _
    ByVal userID As Long, _
    ByVal login As String, _
    ByVal fullName As String) As Boolean
    ' @desc: Добавляет явную ссылку пользователя на службу в буфере. Если пользователь отсутствует — создаёт новый элемент (hasDbLink=False, права False). Если уже есть и RightsByRole = True — ничего не делает (нельзя добавить вручную). Если есть и PendingDelete = True — снимает флаг удаления (восстанавливает). Возвращает True при успехе, False если операция не применима. 
    ' @role: Вызывается из BtnAddUSClick при клике "добавить пользователя к службе". 
    ' @todo: Нет. Логика трёх случаев корректна.

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
' @desc: Помечает ссылку пользователя к удалению или физически удаляет из буфера. Если пользователь не найден — ничего не делает. Если RightsByRole = True — ничего не делает (нельзя снять права роли вручную). Если HasDbLink = True — ставит PendingDelete = True (отложенное удаление в БД). Если HasDbLink = False — физически удаляет из коллекции (ещё не сохранён в БД). Возвращает True при успехе. 
' @role: Вызывается из BtnDelUSClick при клике "убрать пользователя из службы". 
' @todo: Нет. Разделение на мягкое/физическое удаление — правильное решение.
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
' @desc: Переключает флаг CanEdit у пользователя в буфере (True → False → True). Если пользователь не найден или RightsByRole = True — ничего не делает. Возвращает True при успехе. 
' @role: Вызывается из BtnUSCanEditClick при клике на кнопку редактирования прав. 
' @todo: Нет. Toggle-паттерн корректен.
    Dim obj As Object
    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then Exit Function
    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    obj("CanEdit") = Not NzBool(obj("CanEdit"), False)
    SvcBuf_ToggleEdit = True
End Function

Public Function SvcBuf_ToggleApprove(ByVal userID As Long) As Boolean
' @desc: Переключает флаг CanApprove у пользователя в буфере (True → False → True). Если пользователь не найден или RightsByRole = True — ничего не делает. Возвращает True при успехе. 
' @role: Вызывается из BtnUSCanApproveClick при клике на кнопку прав согласования. 
' @todo: Нет. Toggle-паттерн корректен.
    Dim obj As Object
    Set obj = SvcBuf_Get(userID)
    If obj Is Nothing Then Exit Function
    If NzBool(obj("RightsByRole"), False) = True Then Exit Function

    obj("CanApprove") = Not NzBool(obj("CanApprove"), False)
    SvcBuf_ToggleApprove = True
End Function

' --- ДОСТУП К КОЛЛЕКЦИИ И СИНХРОНИЗАЦИЯ ---

Public Function SvcBuf_Items() As Collection
' @desc: Возвращает ссылку на внутреннюю коллекцию mItems. Позволяет внешнему коду итерироваться по буферу без прямого доступа к mItems. 
' @role: Используется в SaveServiceUsersLinks, RefreshUsersByServiceList и NormalizeServiceUsersBufferAfterSave для перебора всех элементов. 
' @todo: Возвращает именно ссылку, не копию — внешний код теоретически может изменить коллекцию. Если станет проблемой — рассмотреть возврат копии.
    Set SvcBuf_Items = mItems
End Function

Public Sub NormalizeServiceUsersBufferAfterSave()
' @desc: Приводит буфер к актуальному состоянию после успешного сохранения в БД. Логика: - пользователи с RightsByRole = False пропускаются - если RightsByRole = True и PendingDelete = True → удаляет из коллекции - если RightsByRole = True и PendingDelete = False → ставит HasDbLink = True, PendingDelete = False (подтверждает сохранение) 
' @role: Вызывается сразу после SaveServiceUsersLinks чтобы синхронизировать буфер с новым состоянием БД без повторного запроса к Access. 
' @todo: Проверить: нужно ли также сбрасывать PendingDelete у RightsByRole=False записей. Сейчас эта ветка полностью игнорируется — возможно намеренно.
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

