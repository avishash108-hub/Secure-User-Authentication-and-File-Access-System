-- Sample seed data for local development only.
-- All seeded users use: Password123!

INSERT INTO users (
    u_id,
    email,
    password_hash,
    full_name,
    display_name,
    bio,
    created_at,
    role
)
VALUES
(
    'usr_001',
    'alice@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$H/z6qt41PDNQ+4XaoOgnpw$b3o7unzDUB6RwRXGroN+BJeV4+FX+BrTVNFGiv5hXms',
    'Alice Nakamura',
    'alice',
    'Product designer who likes clean UIs.',
    '2025-01-14T09:32:00Z',
    'user'
),
(
    'usr_002',
    'bob@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$lPyA+Rzphf/aHorjLtWx5w$nFOxsZf+i5ZLcoH2iP10eR7Nnv7JQdPQGWtiFIIpi9M
',
    'Bob Alvarez',
    'bob',
    'Backend engineer, coffee enthusiast.',
    '2025-02-02T11:15:00Z',
    'user'
),
(
    'usr_003',
    'carol@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$UGFBJQ3IX8vtNGaapNdFzg$cJa3utHcFa8UqwAalAsJkuOjC5D/EhKQhFz60l4zj+4',
    'Carol Whitfield',
    'carol',
    'QA lead focused on security testing.',
    '2025-03-10T16:48:00Z',
    'user'
)
ON CONFLICT (u_id) DO NOTHING;


INSERT INTO files (
    file_id,
    u_id,
    file_name,
    mime_type,
    size_bytes,
    uploadedAt,
    file_path
)
VALUES
(
    'file_001',
    'usr_001',
    'resume_alice.pdf',
    'application/pdf',
    84213,
    '2025-01-15T10:02:00Z',
    'storage/resume_alice.pdf'
),
(
    'file_002',
    'usr_001',
    'profile_photo.jpg',
    'image/jpeg',
    231044,
    '2025-01-16T14:20:00Z',
    'storage/profile_photo.jpg'
),
(
    'file_003',
    'usr_002',
    'project_notes.txt',
    'text/plain',
    5210,
    '2025-02-03T09:40:00Z',
    'storage/project_notes.txt'
),
(
    'file_004',
    'usr_002',
    'invoice_march.pdf',
    'application/pdf',
    62890,
    '2025-03-01T08:05:00Z',
    'storage/invoice_march.pdf'
),
(
    'file_005',
    'usr_003',
    'test_plan.docx',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    41200,
    '2025-03-11T12:30:00Z',
    'storage/test_plan.docx'
),
(
    'file_006',
    'usr_003',
    'vacation.png',
    'image/png',
    512300,
    '2025-04-02T18:00:00Z',
    'storage/vacation.png'
)
ON CONFLICT (file_id) DO NOTHING;
