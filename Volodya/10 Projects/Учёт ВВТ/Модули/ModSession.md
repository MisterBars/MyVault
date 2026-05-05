---
type: module
status: in-progress
done_date:
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

Private Const SESSION_TIMEOUT_MINUTES       As Long = 30
Private Const HEARTBEAT_INTERVAL_MINUTES    As Long = 5
Private Const HEARTBEAT_PROC_NAME           As String = "SessionHeartBeatTick"

Public g_SessionID      As Long
Public g_SessionToken   As String
Public g_CurrentUserID  As Long
Public g_CurrentLogin   As String
Public g_CurrentRoleID  As Long
Public g_IsAuthorized As Boolean
Public g_HeartbeatScheduledAt As Date

Private Function OpenDb() As DAO.Database
' @desc: Обёртка над OpenCurrentDb для удобства внутри модуля сессий.
' @role: DB
' @todo: При изменении способа открытия БД править только OpenCurrentDb.
    Set OpenDb = OpenCurrentDb
End Function

' ================================================================
' Старт/стоп
' ================================================================
Public Sub SessionStartup(ByVal userID As Long, _
                          Optional ByVal userLogin As String = "", _
                          Optional ByVal roleID As Long = 0)
' @desc: Инициализирует сессию пользователя: чистит хвосты, открывает новую запись UserSessions и запускает heartbeat.
' @role: Session
' @todo: При неуспешном SessionOpen можно добавить явное сообщение пользователю.

    Call SessionResetGlobals
    
    g_CurrentUserID = userID
    g_CurrentLogin = userLogin
    g_CurrentRoleID = roleID
    
    Call SessionCleanupOnStartup(userID)
    Call SessionCleanupHistory
    Call SessionOpen(userID)
    
    If g_SessionID > 0 Then
        g_IsAuthorized = True
        Call SessionStartHeartbeat
    End If
End Sub

Public Sub SessionShutdown()
' @desc: Корректно завершает текущую сессию: останавливает heartbeat, закрывает запись UserSessions и сбрасывает глобалы.
' @role: Session
' @todo: Рассмотреть логирование причин завершения (нормальный выход, ошибка, логаут).
    On Error Resume Next
    Call SessionStopHeartbeat
    Call SessionClose
    Call SessionResetGlobals
    On Error GoTo 0
End Sub

' ================================================================
' Очистка при запуске
' ================================================================
Public Sub SessionCleanupOnStartup(ByVal userID As Long)
' @desc: Помечает старые активные сессии пользователя как Expired/Closed при новом входе.
' @role: Session
' @todo: Добавить ShowError при критической ошибке вместо тихого ExitPoint.
    Dim db As DAO.Database
    Dim sql As String
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "UPDATE UserSessions " & _
          "Set SessionStatus='Expired',LogoutTime=Now() " & _
          "WHERE UserID=" & userID & " " & _
          "AND SessionStatus='Active' " & _
          "AND DateDiff('n', LastPing, Now()) > " & SESSION_TIMEOUT_MINUTES
    db.Execute sql, dbFailOnError
          
    sql = "UPDATE UserSessions " & _
          "Set SessionStatus='Closed',LogoutTime=Now() " & _
          "WHERE UserID=" & userID & " " & _
          "AND SessionStatus='Active'"
    db.Execute sql, dbFailOnError
    
ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub

' ================================================================
' Открытие/закрытие сессии
' ================================================================
Public Function SessionOpen(ByVal userID As Long) As Long
' @desc: Создаёт новую запись в UserSessions для пользователя, обновляет LastLogin и заполняет g_SessionID/g_SessionToken.
' @role: Session
' @todo: При ошибке стоит показывать ShowError, сейчас просто возвращается 0.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim tok As String
    
    On Error GoTo ErrHandler
    
    tok = CreateSessionToken_GUID()
    Set db = OpenDb()
    Set rs = db.OpenRecordset("UserSessions", dbOpenDynaset)
    
    rs.AddNew
    rs!userID = userID
    rs!SessionToken = tok
    rs!LoginTime = Now
    rs!lastPing = Now
    rs!SessionStatus = "Active"
    rs!WorkbookHost = GetWorkbookHost()
    rs.Update
    
    rs.Bookmark = rs.LastModified
    g_SessionID = rs!sessionID
    g_SessionToken = tok
    
    rs.Close
    Set rs = Nothing
    
    sql = "UPDATE Users SET LastLogin=NOW() WHERE UserID=" & userID
    db.Execute sql, dbFailOnError
    
    db.Close
    Set db = Nothing
    
    SessionOpen = g_SessionID
    GoTo CleanExit

ErrHandler:
    SessionOpen = 0

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then
        If rs.EditMode <> 0 Then rs.CancelUpdate
        rs.Close
    End If
    If Not db Is Nothing Then db.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Sub SessionClose()
' @desc: Помечает текущую сессию как Closed и проставляет LogoutTime для активной записи.
' @role: Session
' @todo: В будущем можно различать ручное закрытие и авто-логаут по типу события.
    Dim db As DAO.Database
    Dim sql As String
    
    If g_SessionID <= 0 Then Exit Sub
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "UPDATE UserSessions " & _
          "SET SessionStatus='Closed', LogoutTime=Now() " & _
          "WHERE SessionID=" & g_SessionID & " " & _
          "AND SessionToken='" & SqlText(g_SessionToken) & "' " & _
          "AND SessionStatus='Active'"
    db.Execute sql, dbFailOnError
    
ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub

Public Sub SessionMarkCrashed()
' @desc: Помечает текущую сессию как Crashed, если Excel завершился/отключился некорректно.
' @role: Session
' @todo: Рассмотреть вызов при обработке ошибок верхнего уровня (Application-level error handler).
    Dim db As DAO.Database
    Dim sql As String
    
    If g_SessionID <= 0 Then Exit Sub
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "UPDATE UserSessions " & _
          "SET SessionStatus='Crashed', LogoutTime=Now() " & _
          "WHERE SessionID=" & g_SessionID & " " & _
          "AND SessionToken='" & SqlText(g_SessionToken) & "' " & _
          "AND SessionStatus='Active'"
    db.Execute sql, dbFailOnError
    
ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub

Public Sub SessionExpireCurrent()
' @desc: Помечает текущую активную сессию как Expired и устанавливает LogoutTime.
' @role: Session
' @todo: Сейчас вызывается только из SessionIsValid — можно добавить отдельный сценарий принудительного истечения.
    Dim db As DAO.Database
    Dim sql As String
    
    If g_SessionID <= 0 Then Exit Sub
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "UPDATE UserSessions " & _
          "SET SessionStatus='Expired', LogoutTime=Now() " & _
          "WHERE SessionID=" & g_SessionID & " " & _
          "AND SessionToken='" & SqlText(g_SessionToken) & "' " & _
          "AND SessionStatus='Active'"
    db.Execute sql, dbFailOnError
    
ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub

' ================================================================
' Валидация и проверка сессии
' ================================================================
Public Sub SessionPing()
' @desc: Обновляет LastPing для текущей активной сессии, сигнализируя, что клиент ещё жив.
' @role: Session
' @todo: При регулярных ошибках можно добавить счётчик неудачных пингов для диагностики.
    Dim db As DAO.Database
    Dim sql As String
    
    If g_SessionID <= 0 Then Exit Sub
    If Len(g_SessionToken) = 0 Then Exit Sub
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "UPDATE UserSessions " & _
          "SET LastPing=Now() " & _
          "WHERE SessionID=" & g_SessionID & " " & _
          "AND SessionToken='" & SqlText(g_SessionToken) & "' " & _
          "AND SessionStatus='Active'"
    db.Execute sql, dbFailOnError
    
ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub

Public Function SessionIsValid() As Boolean
' @desc: Проверяет по таблице UserSessions, активна ли текущая сессия и не истёк ли таймаут.
' @role: Session
' @todo: При частых истечениях можно логировать в аудит или показывать пользователю причину разлогина.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim lastPing As Date
    Dim st As String
    
    SessionIsValid = False
    
    If g_SessionID <= 0 Then Exit Function
    If Len(g_SessionToken) = 0 Then Exit Function
    
    On Error GoTo ExitPoint
    
    Set db = OpenDb()
    
    sql = "SELECT SessionStatus, LastPing " & _
          "FROM UserSessions " & _
          "WHERE SessionID=" & g_SessionID & " " & _
          "AND SessionToken='" & SqlText(g_SessionToken) & "'"
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    If rs.EOF Then GoTo ExitPoint
    
    st = NzStr(rs!SessionStatus)
    lastPing = NzDate(rs!lastPing)
    
    If UCase$(st) <> "ACTIVE" Then GoTo ExitPoint
    
    If DateDiff("n", lastPing, Now) > SESSION_TIMEOUT_MINUTES Then
        rs.Close
        Set rs = Nothing
        db.Close
        Set db = Nothing
        
        Call SessionExpireCurrent
        Call SessionStopHeartbeat
        g_IsAuthorized = False
        GoTo ExitPoint
    End If
    
    SessionIsValid = True
    
ExitPoint:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not db Is Nothing Then db.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Sub SessionStartHeartbeat()
' @desc: Планирует периодический вызов SessionHeartBeatTick через Application.OnTime.
' @role: Session
' @todo: Убедиться, что при закрытии книги всегда вызывается SessionStopHeartbeat.
    On Error Resume Next
    Call SessionStopHeartbeat
    g_HeartbeatScheduledAt = Now + TimeSerial(0, HEARTBEAT_INTERVAL_MINUTES, 0)
    Application.OnTime EarliestTime:=g_HeartbeatScheduledAt, _
                       Procedure:=HEARTBEAT_PROC_NAME, _
                       Schedule:=True
    On Error GoTo 0
End Sub

Public Sub SessionStopHeartbeat()
' @desc: Отменяет запланированный таймер heartbeat и сбрасывает время следующего срабатывания.
' @role: Session
' @todo: При отладке удобно логировать отмену heartbeat в Immediate/лог.
    On Error Resume Next
    If g_HeartbeatScheduledAt > 0 Then
        Application.OnTime EarliestTime:=g_HeartbeatScheduledAt, _
                           Procedure:=HEARTBEAT_PROC_NAME, _
                           Schedule:=False
    End If
    g_HeartbeatScheduledAt = CDate(0)
    On Error GoTo 0
End Sub

Public Sub SessionHeartBeatTick()
' @desc: Периодически проверяет валидность сессии и обновляет LastPing либо останавливает heartbeat при истечении.
' @role: Session
' @todo: Добавить вызов UI-логики (например, показать форму логина) при потере авторизации.
    On Error GoTo ExitPoint
    
    If g_IsAuthorized = False Then GoTo ExitPoint
    If g_SessionID <= 0 Then GoTo ExitPoint
    If SessionIsValid() Then
        Call SessionPing
        Call SessionStartHeartbeat
    Else
        Call SessionStopHeartbeat
        g_IsAuthorized = False
    End If
    
ExitPoint:
End Sub

' ================================================================
' Вспомогательные функции
' ================================================================
Public Function SessionTokenIsActive(ByVal token As String) As Boolean
' @desc: Проверяет по БД, существует ли активная сессия с указанным токеном.
' @role: Session
' @todo: Использовать при необходимости межклиентной валидации токена.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String

    SessionTokenIsActive = False
    If Len(Trim$(token)) = 0 Then Exit Function

    On Error GoTo ExitPoint

    Set db = OpenDb()

    sql = "SELECT TOP 1 SessionID " & _
          "FROM UserSessions " & _
          "WHERE SessionToken='" & SqlText(token) & "' " & _
          "AND SessionStatus='Active'"

    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    If Not rs.EOF Then SessionTokenIsActive = True

ExitPoint:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not db Is Nothing Then db.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function SessionGetToken(ByVal sessionID As Long) As String
' @desc: Возвращает токен сессии по её ID из таблицы UserSessions.
' @role: Session
' @todo: Нужна только для отладочных сценариев; в боевом коде лучше работать через g_SessionToken.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String

    SessionGetToken = ""

    On Error GoTo ExitPoint

    Set db = OpenDb()

    sql = "SELECT TOP 1 SessionToken FROM UserSessions WHERE SessionID=" & sessionID
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)

    If Not rs.EOF Then
        SessionGetToken = NzStr(rs!SessionToken)
    End If

ExitPoint:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    If Not db Is Nothing Then db.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Sub SessionResetGlobals()
' @desc: Сбрасывает все глобальные переменные сессии и авторизации в исходное состояние.
' @role: Session
' @todo: Важно вызывать при любом фатальном сбое авторизации.
    g_SessionID = 0
    g_SessionToken = vbNullString
    g_CurrentUserID = 0
    g_CurrentLogin = vbNullString
    g_CurrentRoleID = 0
    g_IsAuthorized = False
    g_HeartbeatScheduledAt = CDate(0)
End Sub

' ================================================================
' Токен сессии
' ================================================================
Public Function CreateSessionToken_GUID() As String
' @desc: Генерирует GUID-подобный строковый токен из Scriptlet.TypeLib и очищает его от разделителей.
' @role: Session
' @todo: При отсутствии Scriptlet.TypeLib рассмотреть альтернативу (Rnd+Time, крипто-библиотека).
    Dim s As String
    Dim i As Long
    Dim ch As String
    Dim r As String

    s = CreateObject("Scriptlet.TypeLib").GUID
    s = Replace$(s, "{", "")
    s = Replace$(s, "}", "")
    s = Replace$(s, "-", "")

    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If (ch >= "0" And ch <= "9") Or _
           (ch >= "A" And ch <= "F") Or _
           (ch >= "a" And ch <= "f") Then
            r = r & ch
        Else
            Exit For
        End If
    Next i

    CreateSessionToken_GUID = LCase$(r)
End Function


' ================================================================
' Дополнительные функции
' ================================================================
Private Function GetWorkbookHost() As String
' @desc: Возвращает имя компьютера-хоста (COMPUTERNAME) для записи в UserSessions.WorkbookHost.
' @role: Session
' @todo: При необходимости расширить до доменного имени/пользователя Windows.
    On Error Resume Next
    GetWorkbookHost = Environ("COMPUTERNAME")
    If Len(GetWorkbookHost) = 0 Then GetWorkbookHost = "UNKNOWN"
    On Error GoTo 0
End Function

Private Function SqlText(ByVal s As String) As String
' @desc: Экранирует одинарные кавычки в строке для безопасной подстановки в SQL.
' @role: SQL
' @todo: Можно заменить на общий хелпер (Q/QuoteSql) для единообразия.
    SqlText = Replace$(s, "'", "''")
End Function

Public Sub SessionCleanupHistory()
' @desc: Удаляет из истории старые завершённые/истёкшие/упавшие сессии старше суток.
' @role: Session
' @todo: Параметризовать период хранения истории через настройки, а не жёстко 1 день.
    Dim db As DAO.Database
    Dim sql As String

    On Error GoTo ExitPoint
    Set db = OpenDb()

    sql = "DELETE FROM UserSessions " & _
          "WHERE " & _
          " (SessionStatus='Closed' AND LogoutTime < DateAdd('d', -1, Now()))" & _
          " OR (SessionStatus='Expired' AND LogoutTime < DateAdd('d', -1, Now()))" & _
          " OR (SessionStatus='Crashed' AND LogoutTime < DateAdd('d', -1, Now()))"
    db.Execute sql, dbFailOnError

ExitPoint:
    On Error Resume Next
    If Not db Is Nothing Then db.Close
    Set db = Nothing
End Sub
```

## Черновые заметки

