typedef i32 FileID
typedef i32 PackageID
typedef i32 TaskID
typedef list<string> LinkList
typedef byte Progress
typedef byte Priority

enum DownloadStatus {
  Finished
  Offline,
  Online,
  Queued,
  Checking,
  Waiting,
  Reconnected,
  Starting,
  Failed,
  Aborted,
  Decrypting,
  Custom,
  Downloading,
  Processing,
  Unknown
}

enum Destination {
  Queue,
  Collector
}

enum CaptchaStatus {
  Init,
  Waiting,
  User,
  SharedUser,
  Done
}

enum ConfigItemType {
  String,
  Password,
  Choice,
  Bool,
  Integer,
  IP,
  File,
  Folder,
  Time
}

enum ElementType {
  Package,
  File
}

enum EventType {
  ReloadAll,
  ReloadAccounts,
  ReloadConfig,
  ReloadOrder,
  Update,
  Remove,
  Insert
}

struct DownloadStatus {
  1: FileID id,
  2: string name,
  3: i32 speed,
  4: i32 eta,
  5: string format_eta,
  6: i64 kbleft,
  7: i64 bleft,
  8: i64 size,
  9: string format_size,
  10: Progress percent,
  11: DownloadStatus status,
  12: string statusmsg,
  13: string format_wait,
  14: i64 wait_until,
  15: PackageID packageID,
}

struct ServerStatus {
  1: bool pause,
  2: i16 active,
  3: i16 queue,
  4: i16 total,
  5: i32 speed,
  6: bool download,
  7: bool reconnect
}

struct ConfigItem {
  1: string name,
  2: string description,
  3: string value,
  4: ConfigItemType type,
  5: optional set<string> choice
}

struct ConfigSection {
  1: string name,
  2: string description,
  3: list<ConfigItem> items
}

struct FileData {
  1: FileID fid,
  2: string url,
  3: string name,
  4: string plugin,
  5: i64 size,
  6: string format_size,
  7: DownloadStatus status,
  8: string statusmsg,
  9: PackageID package,
  10: string error,
  11: i16 order,
  12: Progress progress
}

struct PackageData {
  1: PackageID pid,
  2: string name,
  3: string folder,
  4: string site,
  5: string password,
  6: Destination destination,
  7: i16 order,
  8: Priority priority,
  9: optional list<FileID> fileids
}

struct CaptchaTask {
  1: TaskID tid,
  2: binary data,
  3: string type
}

struct Event {
  1: EventType event,
  2: optional i32 id,
  3: optional ElementType type,
  4: optional Destination destination
}

struct UserData {
  1: string name,
  2: string email,
  3: i32 role,
  4: i32 permission,
  5: string template
}

struct AccountInfo {
  1: i64 validuntil,
  2: string login,
  3: map<string, string> options,
  4: bool valid,
  5: i64 trafficleft,
  6: i64 maxtraffic,
  7: bool premium,
  8: string type,
}

struct AccountData {
  1: string type,
  2: string login,
  3: optional string password,
  4: optional map<string, string> options
}

service Pyload {
  //general
  string getConfigValue(1: string category, 2: string option, 3: string section),
  void setConfigValue(1: string category, 2: string option, 3: string value, 4: string section),
  list<ConfigSection> getConfig(),
  list<ConfigSection> getPluginConfig(),
  void pauseServer(),
  void unpauseServer(),
  bool togglePause(),
  ServerStatus statusServer(),
  i64 freeSpace(),
  string getServerVersion(),
  void kill(),
  void restart(),
  list<string> getLog(1: i32 offset),
  map<string, string> checkURL(1: LinkList urls),
  bool isTimeDownload(),
  bool isTimeReconnect(),
  
  //downloads
  list<DownloadStatus> statusDownloads(),
  PackageID addPackage(1: string name, 2: LinkList links, 3: Destination dest),
  PackageData getPackageData(1: PackageID pid),
  FileData getFileData(1: FileID fid),
  void deleteFiles(1: list<FileID> fids),
  void deletePackages(1: list<PackageID> pids),
  list<PackageData> getQueue(),
  list<PackageData> getCollector(),
  void addFiles(1: PackageID pid, 2: LinkList links),
  void pushToQueue(1: PackageID pid),
  void pullFromQueue(1: PackageID pid),
  void restartPackage(1: PackageID pid),
  void restartFile(1: FileID fid),
  void recheckPackage(1: PackageID pid),
  void stopAllDownloads(),
  void stopDownloads(1: list<FileID> fids),
  void setPackageName(1: PackageID pid, 2: string name),
  void movePackage(1: Destination destination, 2: PackageID pid),
  void uploadContainer(1: string filename, 2: binary data),
  void setPriority(1: PackageID pid, 2: Priority priority)
  void orderPackage(1: PackageID pid, 2: i16 position),
  void orderFile(1: FileID fid, 2: i16 position),
  void setPackageData(1: PackageID pid, 2: PackageData data),
  void deleteFinished(),
  void restartFailed(),
  map<i16, PackageID> getPackageOrder(1: Destination destination),
  map<i16, FileID> getFileOrder(1: PackageID pid)
  
  //captcha
  bool isCaptchaWaiting(),
  CaptchaTask getCaptchaTask(1: bool exclusive),
  CaptchaStatus getCaptchaTaskStatus(1: TaskID tid),
  void setCaptchaResult(1: TaskID tid, 2: string result),
  
  //events
  list<Event> getEvents()
  
  //accounts
  list<AccountInfo> getAccounts(),
  void updateAccounts(1: AccountData data),
  void removeAccount(1: string plugin, 2: string account)
  
  //auth
  bool login(1: string username, 2: string password),
  UserData getUserData()
}
