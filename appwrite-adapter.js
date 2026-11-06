
if (!window.Appwrite) {
    throw new Error("Appwrite SDK failed to load.");
}

const client = new Appwrite.Client();

client
    .setEndpoint(document.getElementById("awEndpoint").value.trim())
    .setProject(document.getElementById("awProjectId").value.trim());

const account = new Appwrite.Account(client);
const tablesDB = new Appwrite.TablesDB(client);
const storage = new Appwrite.Storage(client);

const appwriteConfig = {
    databaseId: document.getElementById("awDatabaseId").value.trim(),
    usersTableId: "users",
    filesTableId: "files",
    bucketId: document.getElementById("awBucketId").value.trim()
};


// Find the profile belonging to the logged-in Appwrite Auth user.
async function getProfile(userId) {
    const result = await tablesDB.listRows({
        databaseId: appwriteConfig.databaseId,
        tableId: appwriteConfig.usersTableId,
        queries: [
            Appwrite.Query.equal("u_Id", userId)
        ]
    });

    return result.rows[0] || null;
}


// Register a new Appwrite Auth user and create their profile row.
async function register(email, password) {
    const user = await account.create({
        userId: Appwrite.ID.unique(),
        email,
        password
    });

    await account.createEmailPasswordSession({
        email,
        password
    });

    const profile = await tablesDB.createRow({
        databaseId: appwriteConfig.databaseId,
        tableId: appwriteConfig.usersTableId,
        rowId: user.$id,
        data: {
            u_Id: user.$id,
            email: user.email,
            full_name: email.split("@")[0],
            display_name: email.split("@")[0],
            bio: "",
            role: "user"
        }
    });

    return { user, profile };
}


// Log in using an Appwrite session. No JWT is generated.
async function login(email, password) {
    await account.createEmailPasswordSession({
        email,
        password
    });

    const user = await account.get();
    const profile = await getProfile(user.$id);

    return { user, profile };
}


// Delete the current Appwrite session.
async function logout() {
    return await account.deleteSession({
        sessionId: "current"
    });
}


// Retrieve the current authenticated user and their profile.
async function getMe() {
    const user = await account.get();
    const profile = await getProfile(user.$id);

    return { user, profile };
}


// List metadata rows belonging to the current user.
async function getFiles() {
    const user = await account.get();

    return await tablesDB.listRows({
        databaseId: appwriteConfig.databaseId,
        tableId: appwriteConfig.filesTableId,
        queries: [
            Appwrite.Query.equal("user_id", user.$id)
        ]
    });
}


// Find metadata using the Storage file ID, not the metadata row's $id.
async function getFileById(id) {
    const user = await account.get();

    const result = await tablesDB.listRows({
        databaseId: appwriteConfig.databaseId,
        tableId: appwriteConfig.filesTableId,
        queries: [
            Appwrite.Query.equal("file_id", id),
            Appwrite.Query.equal("user_id", user.$id)
        ]
    });

    if (!result.rows.length) {
        throw new Error("File not found or you do not own this file.");
    }

    return result.rows[0];
}


// Generate the Appwrite Storage download URL.
function downloadFileById(id) {
    const fileUrl = storage.getFileDownload({
        bucketId: appwriteConfig.bucketId,
        fileId: id
    });

    return fileUrl;
}


// Expose the adapter to index.html.
window.appwriteAdapter = {
    register,
    login,
    logout,
    getMe,
    getFiles,
    getFileById,
    downloadFileById
};

console.log("Appwrite adapter initialized");
