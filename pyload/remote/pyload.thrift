namespace java org.pyload.thrift

typedef i32 FileID
typedef i32 PackageID
typedef i32 ResultID
typedef i32 InteractionID
typedef i32 UserID
typedef i32 AccountID
typedef i64 UTCDate
typedef i64 ByteCount
typedef list<string> LinkList
typedef string PluginName
typedef string JSONString

enum DownloadStatus {
  NA, // No downloads status set
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
  NotPossible,
  Missing,
  FileMismatch,
  Occupied,
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
  Executable = 64
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
enum InputType {
  NA,
  Text,
  Int,
  File,
  Folder,
  Textbox,
  Password,
  Time,
  TimeSpan,
  ByteSize, // size in bytes
  Bool,   // confirm like, yes or no dialog
  Click,  // for positional captchas
  Select,  // select from list
  Multiple,  // multiple choice from list of elements
  List, // arbitary list of elements
  PluginList, // a list plugins from pyload
  Table  // table like data structure
}
// more can be implemented by need

// this describes the type of the outgoing interaction
// ensure they can be logcial or'ed
enum Interaction {
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

enum ProgressType {
    All = 0,
    Other = 1,
    Download = 2,
    Decrypting = 4,
    LinkCheck = 8,
    Addon = 16,
    FileOperation = 32,
}

enum Connection {
    All = 0,
    Resumable = 1,
    Secure = 2,
}

struct Input {
    1: InputType type,
    2: optional JSONString default_value,
    3: optional JSONString data,
}

struct DownloadProgress {
    1: FileID fid,
    2: PackageID pid,
    3: ByteCount speed, // per second
    4: Connection conn,
    5: DownloadStatus status,
}

struct ProgressInfo {
  1: PluginName plugin,
  2: string name,
  3: string statusmsg,
  4: i32 eta, // in seconds
  5: ByteCount done,
  6: ByteCount total, // arbitary number, size in case of files,
  7: UserID owner,
  8: ProgressType type,
  9: optional DownloadProgress download //only given when progress type download
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
  12: bool shared,
  13: i16 packageorder,
  14: PackageStats stats,
  15: list<FileID> fids,
  16: list<PackageID> pids,
}

// thrift does not allow recursive datatypes, so all data is accumulated and mapped with id
struct TreeCollection {
  1: PackageInfo root,
  2: map<FileID, FileInfo> files,
  3: map<PackageID, PackageInfo> packages
}

// general info about link, used for online results
struct LinkStatus {
    1: string url,
    2: string name,
    3: ByteCount size,   // size <= 0 : unknown
    4: DownloadStatus status,
    5: optional PluginName plugin,
    6: optional string hash
}

struct StatusInfo {
  1: ByteCount speed,
  2: i16 linkstotal,
  3: i16 linksqueue,
  4: ByteCount sizetotal,
  5: ByteCount sizequeue,
  6: bool notifications,
  7: bool paused,
  8: bool download,
  9: bool reconnect,
  10: ByteCount quota
}

struct InteractionTask {
  1: InteractionID iid,
  2: Interaction type,
  3: Input input,
  4: string title,
  5: string description,
  6: PluginName plugin,
}

struct AddonService {
  1: string func_name,
  2: string label,
  3: string description,
  4: list<string> arguments,
  5: bool pack,
  6: i16 media,
}

struct AddonInfo {
  1: string name,
  2: string description,
  3: JSONString value,
}

struct ConfigItem {
  1: string name,
  2: string label,
  3: string description,
  4: Input input,
  5: JSONString value,
}

struct ConfigHolder {
  1: string name, // for plugin this is the PluginName
  2: string label,
  3: string description,
  4: string explanation,
  5: list<ConfigItem> items,
  6: optional list<AddonInfo> info,
}

struct ConfigInfo {
  1: string name
  2: string label,
  3: string description,
  4: string category,
  5: bool user_context,
  6: optional bool activated,
}

struct EventInfo {
  1: string eventname,
  2: list<JSONString> event_args, //will contain json objects
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
  1: AccountID aid,
  2: PluginName plugin,
  3: string loginname,
  4: UserID owner,
  5: bool valid,
  6: UTCDate validuntil,
  7: ByteCount trafficleft,
  8: ByteCount maxtraffic,
  9: bool premium,
  10: bool activated,
  11: bool shared,
  12: list <ConfigItem> config,
}

struct OnlineCheck {
  1: ResultID rid, // -1 -> nothing more to get
  2: map<string, LinkStatus> data, // package name to result
}

// exceptions

exception PackageDoesNotExist {
  1: PackageID pid
}

exception FileDoesNotExist {
  1: FileID fid
}

exception UserDoesNotExist {
  1: string user
}

exception ServiceDoesNotExist {
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

exception Conflict {
}


service Pyload {

  ///////////////////////
  // Core Status
  ///////////////////////

  string get_server_version(),
  string get_ws_address(),
  StatusInfo get_status_info(),
  list<ProgressInfo> get_progress_info(),

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

  map<string, ConfigHolder> get_config(),
  string getConfigValue(1: string section, 2: string option),

  // two methods with ambigous classification, could be configuration or addon/plugin related
  list<ConfigInfo> getCoreConfig(),
  list<ConfigInfo> getPluginConfig(),
  list<ConfigInfo> getAvailablePlugins(),

  ConfigHolder loadConfig(1: string name),

  void setConfigValue(1: string section, 2: string option, 3: string value),
  void saveConfig(1: ConfigHolder config),
  void deleteConfig(1: PluginName plugin),

  ///////////////////////
  // Download Preparing
  ///////////////////////

  map<PluginName, LinkList> parseLinks(1: LinkList links),

  // parses results and generates packages
  OnlineCheck checkLinks(1: LinkList links),
  OnlineCheck checkContainer(1: string filename, 2: binary data),
  OnlineCheck check_html(1: string html, 2: string url),

  // poll results from previously started online check
  OnlineCheck pollResults(1: ResultID rid),

  // packagename -> urls
  map<string, LinkList> generatePackages(1: LinkList links),

  ///////////////////////
  // Download
  ///////////////////////

  PackageID createPackage(1: string name, 2: string folder, 3: PackageID root, 4: string password,
                            5: string site, 6: string comment, 7: bool paused),

  PackageID addPackage(1: string name, 2: LinkList links, 3: string password),
  // same as above with paused attribute
  PackageID addPackageP(1: string name, 2: LinkList links, 3: string password, 4: bool paused),

  // pid -1 is toplevel
  PackageID addPackageChild(1: string name, 2: LinkList links, 3: string password, 4: PackageID root, 5: bool paused),

  PackageID uploadContainer(1: string filename, 2: binary data),

  void addLinks(1: PackageID pid, 2: LinkList links) throws (1: PackageDoesNotExist e),
  void addLocalFile(1: PackageID pid, 2: string name, 3: string path) throws (1: PackageDoesNotExist e)

  // removes the links with out actually deleting the files
  void removeFiles(1: list<FileID> fids),
  void removePackages(1: list<PackageID> pids), // remove the whole folder recursive

  // Modify Downloads

  void restartPackage(1: PackageID pid),
  void restartFile(1: FileID fid),
  void recheckPackage(1: PackageID pid),
  void restartFailed()
  void stopDownloads(1: list<FileID> fids),
  void stopAllDownloads(),

  ///////////////////////////////
  // File Information retrieval
  ///////////////////////////////

  TreeCollection getAllFiles(),
  TreeCollection getFilteredFiles(1: DownloadState state),

  // pid -1 for root, full=False only delivers first level in tree
  TreeCollection getFileTree(1: PackageID pid, 2: bool full),
  TreeCollection getFilteredFileTree(1: PackageID pid, 2: bool full, 3: DownloadState state),

  // same as above with full=False
  TreeCollection getPackageContent(1: PackageID pid),

  PackageInfo getPackageInfo(1: PackageID pid) throws (1: PackageDoesNotExist e),
  FileInfo getFileInfo(1: FileID fid) throws (1: FileDoesNotExist e),

  TreeCollection findFiles(1: string pattern),
  TreeCollection findPackages(1: list<string> tags),
  list<string> searchSuggestions(1: string pattern),

  // Modify Files/Packages

  // moving package while downloading is not possible, so they will return bool to indicate success
  PackageInfo updatePackage(1: PackageInfo pack) throws (1: PackageDoesNotExist e),
  PackageStatus setPackagePaused(1: PackageID pid, 2: bool paused) throws (1: PackageDoesNotExist e),

  // as above, this will move files on disk
  bool movePackage(1: PackageID pid, 2: PackageID root) throws (1: PackageDoesNotExist e),
  bool moveFiles(1: list<FileID> fids, 2: PackageID pid) throws (1: PackageDoesNotExist e),

  bool deletePackages(1: list<PackageID> pids), // remove the whole folder recursive
  bool deleteFiles(1: list<FileID> fids),

  void orderPackage(1: list<PackageID> pids, 2: i16 position),
  void orderFiles(1: list<FileID> fids, 2: PackageID pid, 3: i16 position),

  ///////////////////////
  // User Interaction
  ///////////////////////

  // mode = interaction types binary ORed
  bool isInteractionWaiting(1: i16 mode),
  list<InteractionTask> getInteractionTasks(1: i16 mode),
  void setInteractionResult(1: InteractionID iid, 2: JSONString result),

  // generate a download link, everybody can download the file until timeout reached
  string generateDownloadLink(1: FileID fid, 2: i16 timeout),

  ///////////////////////
  // Account Methods
  ///////////////////////

  list<string> getAccountTypes(),

  list<AccountInfo> getAccounts(),
  AccountInfo getAccountInfo(1: AccountID aid, 2: PluginName plugin, 3: bool refresh),

  AccountInfo create_account(1: PluginName plugin, 2: string loginname, 3: string password),
  AccountInfo update_account(1:AccountID aid, 2: PluginName plugin, 3: string loginname, 4: string password),
  void updateAccountInfo(1: AccountInfo account),
  void remove_account(1: AccountInfo account),

  /////////////////////////
  // Auth+User Information
  /////////////////////////

  bool login(1: string username, 2: string password),
  // returns own user data
  UserData getUserData(),

  // works contextual, admin can change every password
  bool setPassword(1: string username, 2: string old_password, 3: string new_password),

  // all user, for admins only
  map<UserID, UserData> getAllUserData(),

  UserData add_user(1: string username, 2:string password),

  // normal user can only update their own userdata and not all attributes
  void updateUserData(1: UserData data),
  void removeUser(1: UserID uid),

  ///////////////////////
  // Addon Methods
  ///////////////////////

  map<PluginName, list<AddonInfo>> get_all_info(),
  list<AddonInfo> getInfoByPlugin(1: PluginName plugin),

  map<PluginName, list<AddonService>> getAddonHandler(),

  JSONString invokeAddon(1: PluginName plugin, 2: string func, 3: list<JSONString> func_args)
        throws (1: ServiceDoesNotExist e, 2: ServiceException ex),

  // special variant of callAddon that works on the media types, acccepting integer
  JSONString invokeAddonHandler(1: PluginName plugin, 2: string func, 3: PackageID pid_or_fid)
        throws (1: ServiceDoesNotExist e, 2: ServiceException ex),


  ///////////////////////
  // Statistics Api
  ///////////////////////

  ByteCount getQuota(),



  ///////////////////////
  // Media finder
  ///////////////////////


  //scheduler

  // TODO

}
