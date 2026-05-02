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
    Set OpenDb = OpenCurrentDb
End Function

' ================================================================
' Старт/стоп
' ================================================================
Public Sub SessionStartup(ByVal userID As Long, _
                          Optional ByVal userLogin As String = "", _
                          Optional ByVal roleID As Long = 0)

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
    On Error Resume Next
    Call SessionStopHeartbeat
    g_HeartbeatScheduledAt = Now + TimeSerial(0, HEARTBEAT_INTERVAL_MINUTES, 0)
    Application.OnTime EarliestTime:=g_HeartbeatScheduledAt, _
                       Procedure:=HEARTBEAT_PROC_NAME, _
                       Schedule:=True
    On Error GoTo 0
End Sub
Public Sub SessionStopHeartbeat()
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
    On Error Resume Next
    GetWorkbookHost = Environ("COMPUTERNAME")
    If Len(GetWorkbookHost) = 0 Then GetWorkbookHost = "UNKNOWN"
    On Error GoTo 0
End Function

Private Function SqlText(ByVal s As String) As String
    SqlText = Replace$(s, "'", "''")
End Function

Public Sub SessionCleanupHistory()
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

