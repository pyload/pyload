namespace java org.pyload.thrift

typedef i32 FileID
typedef i32 PackageID
typedef i32 ResultID
typedef i32 InteractionID
typedef i32 UserID
typedef i64 UTCDate
typedef i64 ByteCount
typedef list<string> LinkList
typedef string PluginName
typedef string JSONString

// NA - Not Available
enum DownloadStatus {
  NA,
  Offline,
  Online,
  Queued,
  Paused,
  Finished,
  Skipped,
  Failed,
  Starting,
  Waiting,
  Downloading,
  TempOffline,
  Aborted,
  Decrypting,
  Processing,
  Custom,
  Unknown
}

// Download states, combination of several downloadstatuses
// defined in Api
enum DownloadState {
    All,
    Finished,
    Unfinished,
    Failed,
    Unmanaged // internal state
}

enum MediaType {
  All = 0
  Other = 1,
  Audio = 2,
  Image = 4,
  Video = 8,
  Document = 16,
  Archive = 32,
}

enum FileStatus {
  Ok,
  Missing,
  Remote,   // file is available at remote location
}

enum PackageStatus {
  Ok,
  Paused,
  Folder,
  Remote,
}

// types for user interaction
// some may only be place holder currently not supported
// also all input - output combination are not reasonable, see InteractionManager for further info
// Todo: how about: time, ip, s.o.
enum Input {
  NA,
  Text,
  Int,
  File,
  Folder,
  Textbox,
  Password,
  Bool,   // confirm like, yes or no dialog
  Click,  // for positional captchas
  Select,  // select from list
  Multiple,  // multiple choice from list of elements
  List, // arbitary list of elements
  Table  // table like data structure
}
// more can be implemented by need

// this describes the type of the outgoing interaction
// ensure they can be logcial or'ed
enum Output {
  All = 0,
  Notification = 1,
  Captcha = 2,
  Query = 4,
}

enum Permission {
    All = 0,  // requires no permission, but login
    Add = 1,  // can add packages
    Delete = 2, // can delete packages
    Modify = 4, // modify some attribute of downloads
    Download = 8,  // can download from webinterface
    Accounts = 16, // can access accounts
    Interaction = 32, // can interact with plugins
    Plugins = 64 // user can configure plugins and activate addons
}

enum Role {
    Admin = 0,  //admin has all permissions implicit
    User = 1
}

struct DownloadProgress {
    1: FileID fid,
    2: PackageID pid,
    3: ByteCount speed, // per second
    4: DownloadStatus status,
}

struct ProgressInfo {
  1: PluginName plugin,
  2: string name,
  3: string statusmsg,
  4: i32 eta, // in seconds
  5: ByteCount done,
  6: ByteCount total, // arbitary number, size in case of files
  7: optional DownloadProgress download
}

struct ServerStatus {
  1: i16 queuedDownloads,
  2: i16 totalDownloads,
  3: ByteCount speed,
  4: bool pause,
  5: bool download,
  6: bool reconnect
}

// download info for specific file
struct DownloadInfo {
  1: string url,
  2: PluginName plugin,
  3: string hash,
  4: DownloadStatus status,
  5: string statusmsg,
  6: string error,
}

struct FileInfo {
  1: FileID fid,
  2: string name,
  3: PackageID package,
  4: UserID owner,
  5: ByteCount size,
  6: FileStatus status,
  7: MediaType media,
  8: UTCDate added,
  9: i16 fileorder,
  10: optional DownloadInfo download,
}

struct PackageStats {
  1: i16 linkstotal,
  2: i16 linksdone,
  3: ByteCount sizetotal,
  4: ByteCount sizedone,
}

struct PackageInfo {
  1: PackageID pid,
  2: string name,
  3: string folder,
  4: PackageID root,
  5: UserID owner,
  6: string site,
  7: string comment,
  8: string password,
  9: UTCDate added,
  10: list<string> tags,
  11: PackageStatus status,
  12: i16 packageorder,
  13: PackageStats stats,
  14: list<FileID> fids,
  15: list<PackageID> pids,
}

// thrift does not allow recursive datatypes, so all data is accumulated and mapped with id
struct TreeCollection {
  1: PackageInfo root,
  2: map<FileID, FileInfo> files,
  3: map<PackageID, PackageInfo> packages
}

// general info about link, used for collector and online results
struct LinkStatus {
    1: string url,
    2: string name,
    3: PluginName plugin,
    4: ByteCount size,   // size <= 0 : unknown
    5: DownloadStatus status,
    6: string packagename,
}

struct InteractionTask {
  1: InteractionID iid,
  2: Input input,
  3: list<string> data,
  4: Output output,
  5: optional JSONString default_value,
  6: string title,
  7: string description,
  8: PluginName plugin,
}

struct AddonService {
  1: string func_name,
  2: string description,
  3: list<string> arguments,
  4: optional i16 media,
}

struct AddonInfo {
  1: string func_name,
  2: string description,
  3: JSONString value,
}

struct ConfigItem {
  1: string name,
  2: string label,
  3: string description,
  4: string type,
  5: JSONString default_value,
  6: JSONString value,
}

struct ConfigHolder {
  1: string name,
  2: string label,
  3: string description,
  4: string long_description,
  5: list<ConfigItem> items,
  6: optional list<AddonInfo> info,
  7: optional list<InteractionTask> handler, // if null plugin is not loaded
}

struct ConfigInfo {
  1: string name
  2: string label,
  3: string description,
  4: bool addon,
  5: bool user_context,
  6: optional bool activated,
}

struct EventInfo {
  1: string eventname,
  2: list<JSONString> event_args,
}

struct UserData {
  1: UserID uid,
  2: string name,
  3: string email,
  4: i16 role,
  5: i16 permission,
  6: string folder,
  7: ByteCount traffic
  8: i16 dllimit
  9: string dlquota,
  10: ByteCount hddquota,
  11: UserID user,
  12: string templateName
}

struct AccountInfo {
  1: PluginName plugin,
  2: string loginname,
  3: UserID owner,
  4: bool valid,
  5: UTCDate validuntil,
  6: ByteCount trafficleft,
  7: ByteCount maxtraffic,
  8: bool premium,
  9: bool activated,
  10: bool shared,
  11: map<string, string> options,
}

struct OnlineCheck {
  1: ResultID rid, // -1 -> nothing more to get
  2: map<string, LinkStatus> data, // url to result
}

// exceptions

exception PackageDoesNotExists {
  1: PackageID pid
}

exception FileDoesNotExists {
  1: FileID fid
}

exception UserDoesNotExists {
  1: string user
}

exception ServiceDoesNotExists {
  1: string plugin
  2: string func
}

exception ServiceException {
  1: string msg
}

exception InvalidConfigSection {
  1: string section
}

exception Unauthorized {
}

exception Forbidden {
}


service Pyload {

  ///////////////////////
  // Core Status
  ///////////////////////

  string getServerVersion(),
  string getWSAddress(),
  ServerStatus getServerStatus(),
  list<ProgressInfo> getProgressInfo(),

  list<string> getLog(1: i32 offset),
  ByteCount freeSpace(),

  void pauseServer(),
  void unpauseServer(),
  bool togglePause(),
  bool toggleReconnect(),

  void quit(),
  void restart(),

  ///////////////////////
  // Configuration
  ///////////////////////

  map<string, ConfigHolder> getConfig(),
  string getConfigValue(1: string section, 2: string option),

  // two methods with ambigous classification, could be configuration or addon related
  list<ConfigInfo> getCoreConfig(),
  list<ConfigInfo> getPluginConfig(),
  list<ConfigInfo> getAvailablePlugins(),

  ConfigHolder configurePlugin(1: PluginName plugin),

  void setConfigValue(1: string section, 2: string option, 3: string value),
  void saveConfig(1: ConfigHolder config),
  void deleteConfig(1: PluginName plugin),
  void setConfigHandler(1: PluginName plugin, 2: InteractionID iid, 3: JSONString value),

  ///////////////////////
  // Download Preparing
  ///////////////////////

  map<PluginName, LinkList> checkURLs(1: LinkList urls),
  map<PluginName, LinkList> parseURLs(1: string html, 2: string url),

  // parses results and generates packages
  OnlineCheck checkOnlineStatus(1: LinkList urls),
  OnlineCheck checkOnlineStatusContainer(1: LinkList urls, 2: string filename, 3: binary data)

  // poll results from previously started online check
  OnlineCheck pollResults(1: ResultID rid),

  // packagename -> urls
  map<string, LinkList> generatePackages(1: LinkList links),

  ///////////////////////
  // Download
  ///////////////////////

  list<PackageID> generateAndAddPackages(1: LinkList links, 2: bool paused),

  PackageID createPackage(1: string name, 2: string folder, 3: PackageID root, 4: string password,
                            5: string site, 6: string comment, 7: bool paused),

  PackageID addPackage(1: string name, 2: LinkList links, 3: string password),
  // same as above with paused attribute
  PackageID addPackageP(1: string name, 2: LinkList links, 3: string password, 4: bool paused),

  // pid -1 is toplevel
  PackageID addPackageChild(1: string name, 2: LinkList links, 3: string password, 4: PackageID root, 5: bool paused),

  PackageID uploadContainer(1: string filename, 2: binary data),

  void addLinks(1: PackageID pid, 2: LinkList links) throws (1: PackageDoesNotExists e),
  void addLocalFile(1: PackageID pid, 2: string name, 3: string path) throws (1: PackageDoesNotExists e)

  // these are real file operations and WILL delete files on disk
  void deleteFiles(1: list<FileID> fids),
  void deletePackages(1: list<PackageID> pids), // delete the whole folder recursive

  // Modify Downloads

  void restartPackage(1: PackageID pid),
  void restartFile(1: FileID fid),
  void recheckPackage(1: PackageID pid),
  void restartFailed(),
  void stopDownloads(1: list<FileID> fids),
  void stopAllDownloads(),

  ///////////////////////
  // Collector
  ///////////////////////

  list<LinkStatus> getCollector(),

  void addToCollector(1: LinkList links),
  PackageID addFromCollector(1: string name, 2: bool paused),
  void renameCollPack(1: string name, 2: string new_name),
  void deleteCollPack(1: string name),
  void deleteCollLink(1: string url),

  ////////////////////////////
  // File Information retrieval
  ////////////////////////////

  TreeCollection getAllFiles(),
  TreeCollection getFilteredFiles(1: DownloadState state),

  // pid -1 for root, full=False only delivers first level in tree
  TreeCollection getFileTree(1: PackageID pid, 2: bool full),
  TreeCollection getFilteredFileTree(1: PackageID pid, 2: bool full, 3: DownloadState state),

  // same as above with full=False
  TreeCollection getPackageContent(1: PackageID pid),

  PackageInfo getPackageInfo(1: PackageID pid) throws (1: PackageDoesNotExists e),
  FileInfo getFileInfo(1: FileID fid) throws (1: FileDoesNotExists e),

  TreeCollection findFiles(1: string pattern),
  TreeCollection findPackages(1: list<string> tags),

  // Modify Files/Packages

  // moving package while downloading is not possible, so they will return bool to indicate success
  void updatePackage(1: PackageInfo pack) throws (1: PackageDoesNotExists e),
  bool setPackageFolder(1: PackageID pid, 2: string path) throws (1: PackageDoesNotExists e),

  // as above, this will move files on disk
  bool movePackage(1: PackageID pid, 2: PackageID root) throws (1: PackageDoesNotExists e),
  bool moveFiles(1: list<FileID> fids, 2: PackageID pid) throws (1: PackageDoesNotExists e),

  void orderPackage(1: list<PackageID> pids, 2: i16 position),
  void orderFiles(1: list<FileID> fids, 2: PackageID pid, 3: i16 position),

  ///////////////////////
  // User Interaction
  ///////////////////////

  // mode = Output types binary ORed
  bool isInteractionWaiting(1: i16 mode),
  InteractionTask getInteractionTask(1: i16 mode),
  void setInteractionResult(1: InteractionID iid, 2: JSONString result),

  // generate a download link, everybody can download the file until timeout reached
  string generateDownloadLink(1: FileID fid, 2: i16 timeout),

  list<InteractionTask> getNotifications(),

  ///////////////////////
  // Event Handling
  ///////////////////////

  list<EventInfo> getEvents(1: string uuid),
  
  ///////////////////////
  // Account Methods
  ///////////////////////

  list<AccountInfo> getAccounts(1: bool refresh),
  list<string> getAccountTypes(),
  void updateAccount(1: PluginName plugin, 2: string account, 3: string password),
  void updateAccountInfo(1: AccountInfo account),
  void removeAccount(1: PluginName plugin, 2: string account),
  
  /////////////////////////
  // Auth+User Information
  /////////////////////////

  bool login(1: string username, 2: string password),
  // returns own user data
  UserData getUserData(),

  // all user, for admins only
  map<UserID, UserData> getAllUserData(),

  UserData addUser(1: string username, 2:string password),

  // normal user can only update their own userdata and not all attributes
  void updateUserData(1: UserData data),
  void removeUser(1: UserID uid),

  // works contextual, admin can change every password
  bool setPassword(1: string username, 2: string old_password, 3: string new_password),

  ///////////////////////
  // Addon Methods
  ///////////////////////

  //map<PluginName, list<AddonInfo>> getAllInfo(),
  //list<AddonInfo> getInfoByPlugin(1: PluginName plugin),

  map<PluginName, list<AddonService>> getAddonHandler(),
  bool hasAddonHandler(1: PluginName plugin, 2: string func),

  void callAddon(1: PluginName plugin, 2: string func, 3: list<JSONString> arguments)
        throws (1: ServiceDoesNotExists e, 2: ServiceException ex),

  // special variant of callAddon that works on the media types, acccepting integer
  void callAddonHandler(1: PluginName plugin, 2: string func, 3: PackageID pid_or_fid)
        throws (1: ServiceDoesNotExists e, 2: ServiceException ex),


  //scheduler

  // TODO

}
