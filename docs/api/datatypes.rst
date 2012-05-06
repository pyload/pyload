.. _api_datatypes:

***********************
API Datatype Definition
***********************

Below you find a copy of :file:`module/remote/thriftbackend/pyload.thrift`, which is used to generate the data structs
for various languages. It is also a good overview of avaible methods and return data.

.. code-block:: c

     .. [[[cog cog.out(open('module/remote/thriftbackend/pyload.thrift', 'rb').read()) ]]]
     namespace java org.pyload.thrift

     typedef i32 FileID
     typedef i32 PackageID
     typedef i32 ResultID
     typedef i32 InteractionID
     typedef i64 UTCDate
     typedef i64 ByteCount
     typedef list<string> LinkList
     // a string that can represent multiple types int, bool, time, etc..
     typedef string ValueString
     typedef string PluginName

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
       Remote,
     }

     // types for user interaction
     // some may only be place holder currently not supported
     // also all input - output combination are not reasonable, see InteractionManager for further info
     enum Input {
       NA,
       Text,
       TextBox,
       Password,
       Bool,   // confirm like, yes or no dialog
       Click,  // for positional captchas
       Choice,  // choice from list
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

     struct ProgressInfo {
       1: FileID fid,
       2: string name,
       3: ByteCount speed,
       4: i32 eta,
       5: string format_eta,
       6: ByteCount bleft,
       7: ByteCount size,
       8: string format_size,
       9: i16 percent,
       10: DownloadStatus status,
       11: string statusmsg,
       12: string format_wait,
       13: UTCDate wait_until,
       14: PackageID packageID,
       15: string packageName,
       16: PluginName plugin,
     }

     struct ServerStatus {
       1: bool pause,
       2: i16 active,
       3: i16 queue,
       4: i16 total,
       5: ByteCount speed,
       6: bool download,
       7: bool reconnect
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
       4: ByteCount size,
       5: FileStatus status,
       6: MediaType media,
       7: UTCDate added,
       8: i16 fileorder,
       9: optional DownloadInfo download,
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
       5: string site,
       6: string comment,
       7: string password,
       8: UTCDate added,
       9: PackageStatus status,
       10: i16 packageorder,
       11: PackageStats stats,
       12: list<FileID> fids,
       13: list<PackageID> pids,
     }

     // thrift does not allow recursive datatypes, so all data is accumulated and mapped with id
     struct PackageView {
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
       5: optional ValueString default_value,
       6: string title,
       7: string description,
       8: PluginName plugin,
     }

     struct AddonInfo {
       1: string func_name,
       2: string description,
       3: ValueString value,
     }

     struct ConfigItem {
       1: string name,
       2: string display_name,
       3: string description,
       4: string type,
       5: ValueString default_value,
       6: ValueString value,
     }

     struct ConfigSection {
       1: string name,
       2: string display_name,
       3: string description,
       4: string long_description,
       5: optional list<ConfigItem> items,
       6: optional list<AddonInfo> info,
       7: optional list<InteractionTask> handler, // if null plugin is not loaded
     }

     struct EventInfo {
       1: string eventname,
       2: list<string> event_args,
     }

     struct UserData {
       1: string name,
       2: string email,
       3: i32 role,
       4: i32 permission,
       5: string templateName
     }

     struct AccountInfo {
       1: PluginName plugin,
       2: string loginname,
       3: bool valid,
       4: UTCDate validuntil,
       5: ByteCount trafficleft,
       6: ByteCount maxtraffic,
       7: bool premium,
       8: bool activated,
       9: map<string, string> options,
     }

     struct AddonService {
       1: string func_name,
       2: string description,
       3: optional i16 media,
       4: optional bool package,
     }

     struct OnlineCheck {
       1: ResultID rid, // -1 -> nothing more to get
       2: map<string, LinkStatus> data, //url to result
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

     service Pyload {

       ///////////////////////
       // Server Status
       ///////////////////////

       string getServerVersion(),
       ServerStatus statusServer(),
       void pauseServer(),
       void unpauseServer(),
       bool togglePause(),
       ByteCount freeSpace(),
       void kill(),
       void restart(),
       list<string> getLog(1: i32 offset),
       bool isTimeDownload(),
       bool isTimeReconnect(),
       bool toggleReconnect(),
       void scanDownloadFolder(),

       // downloads - information
       list<ProgressInfo> getProgressInfo(),

       ///////////////////////
       // Configuration
       ///////////////////////

       string getConfigValue(1: string section, 2: string option),
       void setConfigValue(1: string section, 2: string option, 3: string value),
       map<string, ConfigSection> getConfig(),
       map<PluginName, ConfigSection> getPluginConfig(),
       ConfigSection configureSection(1: string section),
       void setConfigHandler(1: PluginName plugin, 2: InteractionID iid, 3: ValueString value),

       ///////////////////////
       // Download Preparing
       ///////////////////////

       map<PluginName, LinkList> checkURLs(1: LinkList urls),
       map<PluginName, LinkList> parseURLs(1: string html, 2: string url),
       // packagename - urls

       // parses results and generates packages
       OnlineCheck checkOnlineStatus(1: LinkList urls),
       OnlineCheck checkOnlineStatusContainer(1: LinkList urls, 2: string filename, 3: binary data)

       // poll results from previously started online check
       OnlineCheck pollResults(1: ResultID rid),

       map<string, LinkList> generatePackages(1: LinkList links),

       ///////////////////////
       // Adding/Deleting
       ///////////////////////

       list<PackageID> generateAndAddPackages(1: LinkList links, 2: bool paused),
       list<FileID> autoAddLinks(1: LinkList links),

       PackageID createPackage(1: string name, 2: string folder, 3: PackageID root, 4: string password,
                                 5: string site, 6: string comment, 7: bool paused),

       PackageID addPackage(1: string name, 2: LinkList links, 3: string password),
       // same as above with paused attribute
       PackageID addPackageP(1: string name, 2: LinkList links, 3: string password, 4: bool paused),

       // pid -1 is toplevel
       PackageID addPackageChild(1: string name, 2: LinkList links, 3: string password, 4: PackageID root, 5: bool paused),

       PackageID uploadContainer(1: string filename, 2: binary data),

       void addLinks(1: PackageID pid, 2: LinkList links) throws (1: PackageDoesNotExists e),

       // these are real file operations and WILL delete files on disk
       void deleteFiles(1: list<FileID> fids),
       void deletePackages(1: list<PackageID> pids),

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
       // File Information retrival
       ////////////////////////////

       PackageView getAllFiles(),
       PackageView getAllUnfinishedFiles(),

       // pid -1 for root, full=False only delivers first level in tree
       PackageView getFileTree(1: PackageID pid, 2: bool full),
       PackageView getUnfinishedFileTree(1: PackageID pid, 2: bool full),

       // same as above with full=False
       PackageView getPackageContent(1: PackageID pid),

       PackageInfo getPackageInfo(1: PackageID pid) throws (1: PackageDoesNotExists e),
       FileInfo getFileInfo(1: FileID fid) throws (1: FileDoesNotExists e),
       map<FileID, FileInfo> findFiles(1: string pattern),

       ///////////////////////
       // Modify Downloads
       ///////////////////////

       void restartPackage(1: PackageID pid),
       void restartFile(1: FileID fid),
       void recheckPackage(1: PackageID pid),
       void stopDownloads(1: list<FileID> fids),
       void stopAllDownloads(),
       void restartFailed(),

       /////////////////////////
       // Modify Files/Packages
       /////////////////////////

       void setFilePaused(1: FileID fid, 2: bool paused) throws (1: FileDoesNotExists e),

       // moving package while downloading is not possible, so they will return bool to indicate success
       void setPackagePaused(1: PackageID pid, 2: bool paused) throws (1: PackageDoesNotExists e),
       bool setPackageFolder(1: PackageID pid, 2: string path) throws (1: PackageDoesNotExists e),
       void setPackageData(1: PackageID pid, 2: map<string, string> data) throws (1: PackageDoesNotExists e),

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
       void setInteractionResult(1: InteractionID iid, 2: ValueString result),

       // generate a download link, everybody can download the file until timeout reached
       string generateDownloadLink(1: FileID fid, 2: i16 timeout),

       list<InteractionTask> getNotifications(),

       map<PluginName, list<AddonService>> getAddonHandler(),
       void callAddonHandler(1: PluginName plugin, 2: string func, 3: PackageID pid_or_fid),

       ///////////////////////
       // Event Handling
       ///////////////////////

       list<EventInfo> getEvents(1: string uuid),
       
       ///////////////////////
       // Account Methods
       ///////////////////////

       list<AccountInfo> getAccounts(1: bool refresh),
       list<string> getAccountTypes()
       void updateAccount(1: PluginName plugin, 2: string account, 3: string password, 4: map<string, string> options),
       void removeAccount(1: PluginName plugin, 2: string account),
       
       /////////////////////////
       // Auth+User Information
       /////////////////////////

       bool login(1: string username, 2: string password),
       UserData getUserData(1: string username, 2: string password) throws (1: UserDoesNotExists ex),
       map<string, UserData> getAllUserData(),

       ///////////////////////
       // Addon Methods
       ///////////////////////

       map<PluginName, list<AddonService>> getServices(),
       bool hasService(1: PluginName plugin, 2: string func),

       // empty string or json encoded list as args
       string call(1: PluginName plugin, 2: string func, 3: string arguments) throws (1: ServiceDoesNotExists ex, 2: ServiceException e),

       map<PluginName, list<AddonInfo>> getAllInfo(),
       list<AddonInfo> getInfoByPlugin(1: PluginName plugin),

       //scheduler

       // TODO

     }
     .. [[[end]]]

