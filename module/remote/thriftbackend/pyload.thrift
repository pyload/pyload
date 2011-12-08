namespace java org.pyload.thrift

typedef i32 FileID
typedef i32 PackageID
typedef i32 TaskID
typedef i32 ResultID
typedef i32 InteractionID
typedef list<string> LinkList
typedef string PluginName
typedef byte Progress
typedef byte Priority


enum DownloadStatus {
  Finished
  Offline,
  Online,
  Queued,
  Skipped,
  Waiting,
  TempOffline,
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
  Collector,
  Queue
}

enum ElementType {
  Package,
  File
}

// types for user interaction
// some may only be place holder currently not supported
// also all input - output combination are not reasonable, see InteractionManager for further info
enum Input {
  NONE,
  TEXT,
  TEXTBOX,
  PASSWORD,
  BOOL,   // confirm like, yes or no dialog
  CLICK,  // for positional captchas
  CHOICE,  // choice from list
  MULTIPLE,  // multiple choice from list of elements
  LIST, // arbitary list of elements
  TABLE  // table like data structure
}
// more can be implemented by need

// this describes the type of the outgoing interaction
// ensure they can be logcial or'ed
enum Output {
  CAPTCHA = 1,
  QUESTION = 2,
  NOTIFICATION = 4,
}

struct DownloadInfo {
  1: FileID fid,
  2: string name,
  3: i64 speed,
  4: i32 eta,
  5: string format_eta,
  6: i64 bleft,
  7: i64 size,
  8: string format_size,
  9: Progress percent,
  10: DownloadStatus status,
  11: string statusmsg,
  12: string format_wait,
  13: i64 wait_until,
  14: PackageID packageID,
  15: string packageName,
  16: PluginName plugin,
}

struct ServerStatus {
  1: bool pause,
  2: i16 active,
  3: i16 queue,
  4: i16 total,
  5: i64 speed,
  6: bool download,
  7: bool reconnect
}

struct ConfigItem {
  1: string name,
  2: string description,
  3: string value,
  4: string type,
}

struct ConfigSection {
  1: string name,
  2: string description,
  3: list<ConfigItem> items,
  4: optional string outline
}

struct FileData {
  1: FileID fid,
  2: string url,
  3: string name,
  4: PluginName plugin,
  5: i64 size,
  6: string format_size,
  7: DownloadStatus status,
  8: string statusmsg,
  9: PackageID packageID,
  10: string error,
  11: i16 order
}

struct PackageData {
  1: PackageID pid,
  2: string name,
  3: string folder,
  4: string site,
  5: string password,
  6: Destination dest,
  7: i16 order,
  8: optional i16 linksdone,
  9: optional i64 sizedone,
  10: optional i64 sizetotal,
  11: optional i16 linkstotal,
  12: optional list<FileData> links,
  13: optional list<FileID> fids
}

struct InteractionTask {
  1: InteractionID iid,
  2: Input input,
  3: list<string> structure,
  4: list<string> preset,
  5: Output output,
  6: list<string> data,
  7: string title,
  8: string description,
  9: string plugin,
}

struct CaptchaTask {
  1: i16 tid,
  2: binary data,
  3: string type,
  4: string resultType
}

struct EventInfo {
  1: string eventname,
  2: optional i32 id,
  3: optional ElementType type,
  4: optional Destination destination
}

struct UserData {
  1: string name,
  2: string email,
  3: i32 role,
  4: i32 permission,
  5: string templateName
}

struct AccountInfo {
  1: i64 validuntil,
  2: string login,
  3: map<string, list<string>> options,
  4: bool valid,
  5: i64 trafficleft,
  6: i64 maxtraffic,
  7: bool premium,
  8: string type,
}

struct ServiceCall {
    1: PluginName plugin,
    2: string func,
    3: optional list<string> arguments,
    4: optional bool parseArguments,  //default False
}

struct OnlineStatus {
    1: string name,
    2: PluginName plugin,
    3: string packagename,
    4: DownloadStatus status,
    5: i64 size,   // size <= 0 : unknown
}

struct OnlineCheck {
    1: ResultID rid, // -1 -> nothing more to get
    2: map<string, OnlineStatus> data, //url to result
}


// exceptions

exception PackageDoesNotExists{
  1: PackageID pid
}

exception FileDoesNotExists{
  1: FileID fid
}

exception ServiceDoesNotExists{
  1: string plugin
  2: string func
}

exception ServiceException{
  1: string msg
}

service Pyload {

  //config
  string getConfigValue(1: string category, 2: string option, 3: string section),
  void setConfigValue(1: string category, 2: string option, 3: string value, 4: string section),
  map<string, ConfigSection> getConfig(),
  map<string, ConfigSection> getPluginConfig(),

  // server status
  void pauseServer(),
  void unpauseServer(),
  bool togglePause(),
  ServerStatus statusServer(),
  i64 freeSpace(),
  string getServerVersion(),
  void kill(),
  void restart(),
  list<string> getLog(1: i32 offset),
  bool isTimeDownload(),
  bool isTimeReconnect(),
  bool toggleReconnect(),

  // download preparing

  // packagename - urls
  map<string, LinkList> generatePackages(1: LinkList links),
  map<PluginName, LinkList> checkURLs(1: LinkList urls),
  map<PluginName, LinkList> parseURLs(1: string html, 2: string url),

  // parses results and generates packages
  OnlineCheck checkOnlineStatus(1: LinkList urls),
  OnlineCheck checkOnlineStatusContainer(1: LinkList urls, 2: string filename, 3: binary data)

  // poll results from previosly started online check
  OnlineCheck pollResults(1: ResultID rid),

  // downloads - information
  list<DownloadInfo> statusDownloads(),
  PackageData getPackageData(1: PackageID pid) throws (1: PackageDoesNotExists e),
  PackageData getPackageInfo(1: PackageID pid) throws (1: PackageDoesNotExists e),
  FileData getFileData(1: FileID fid) throws (1: FileDoesNotExists e),
  list<PackageData> getQueue(),
  list<PackageData> getCollector(),
  list<PackageData> getQueueData(),
  list<PackageData> getCollectorData(),
  map<i16, PackageID> getPackageOrder(1: Destination destination),
  map<i16, FileID> getFileOrder(1: PackageID pid)

  // downloads - adding/deleting
  list<PackageID> generateAndAddPackages(1: LinkList links, 2: Destination dest),
  PackageID addPackage(1: string name, 2: LinkList links, 3: Destination dest),
  void addFiles(1: PackageID pid, 2: LinkList links),
  void uploadContainer(1: string filename, 2: binary data),
  void deleteFiles(1: list<FileID> fids),
  void deletePackages(1: list<PackageID> pids),

  // downloads - modifying
  void pushToQueue(1: PackageID pid),
  void pullFromQueue(1: PackageID pid),
  void restartPackage(1: PackageID pid),
  void restartFile(1: FileID fid),
  void recheckPackage(1: PackageID pid),
  void stopAllDownloads(),
  void stopDownloads(1: list<FileID> fids),
  void setPackageName(1: PackageID pid, 2: string name),
  void movePackage(1: Destination destination, 2: PackageID pid),
  void moveFiles(1: list<FileID> fids, 2: PackageID pid),
  void orderPackage(1: PackageID pid, 2: i16 position),
  void orderFile(1: FileID fid, 2: i16 position),
  void setPackageData(1: PackageID pid, 2: map<string, string> data) throws (1: PackageDoesNotExists e),
  list<PackageID> deleteFinished(),
  void restartFailed(),

  //events
  list<EventInfo> getEvents(1: string uuid)
  
  //accounts
  list<AccountInfo> getAccounts(1: bool refresh),
  list<string> getAccountTypes()
  void updateAccount(1: PluginName plugin, 2: string account, 3: string password, 4: map<string, string> options),
  void removeAccount(1: PluginName plugin, 2: string account),
  
  //auth
  bool login(1: string username, 2: string password),
  UserData getUserData(1: string username, 2:string password),
  map<string, UserData> getAllUserData(),

  //services

  // servicename : description
  map<PluginName, map<string, string>> getServices(),
  bool hasService(1: PluginName plugin, 2: string func),
  string call(1: ServiceCall info) throws (1: ServiceDoesNotExists ex, 2: ServiceException e),


  //info
  // {plugin: {name: value}}
  map<PluginName, map<string,string>> getAllInfo(),
  map<string, string> getInfoByPlugin(1: PluginName plugin),

  //scheduler

  // TODO


  // User interaction

  //captcha
  bool isCaptchaWaiting(),
  CaptchaTask getCaptchaTask(1: bool exclusive),
  string getCaptchaTaskStatus(1: TaskID tid),
  void setCaptchaResult(1: TaskID tid, 2: string result),
}
