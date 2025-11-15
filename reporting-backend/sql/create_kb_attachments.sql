-- Knowledge Base Attachments Table Schema for PostgreSQL
-- Stores file attachments as binary data (bytea) in PostgreSQL

CREATE TABLE IF NOT EXISTS kb_attachments (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_data BYTEA NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_article FOREIGN KEY (article_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_attachments_article ON kb_attachments(article_id);
CREATE INDEX IF NOT EXISTS idx_kb_attachments_uploaded ON kb_attachments(uploaded_date DESC);

-- Add comment
COMMENT ON TABLE kb_attachments IS 'Stores file attachments for knowledge base articles as binary data';
COMMENT ON COLUMN kb_attachments.file_data IS 'Binary file data stored as bytea';
COMMENT ON COLUMN kb_attachments.file_size IS 'File size in bytes';
COMMENT ON COLUMN kb_attachments.mime_type IS 'MIME type (e.g., application/pdf, image/jpeg)';
