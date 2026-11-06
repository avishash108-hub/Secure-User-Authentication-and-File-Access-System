Project ID: 6a8a957c0004aebcd79d
Database ID: 6a8b2cc5001d47736dfb
Users table: users
Files table: files
Storage bucket: 6a8b2ea70010dfac74ba

Auth:
- Email/password enabled
- Alice, Bob, Carol seeded

### Database schema

The Appwrite database uses the same table structure and column names as the PostgreSQL implementation.

Users table:
- u_id
- email
- password_hash
- full_name
- display_name
- bio
- created_at
- role

Files table:
- file_id
- u_id
- file_name
- mime_type
- size_bytes
- uploadedAt
- file_path

The same three seeded users and six file records are used for consistency between the two implementations.

Note: Appwrite Authentication manages user passwords separately, so `password_hash` is not used for authentication in the Appwrite implementation.

Storage:
- File-level permissions enabled
- Each user's files readable by that user only
