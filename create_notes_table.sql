-- Create a table to store work order notes
-- This table allows users to add notes to work orders without modifying the read-only Softbase database
CREATE TABLE IF NOT EXISTS ben002.WorkOrderNotes (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    wo_number NVARCHAR(50) NOT NULL,
    note NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    created_by NVARCHAR(100),
    updated_by NVARCHAR(100),
    
    -- Index for quick lookups by work order number
    INDEX idx_wo_number (wo_number)
);

-- Create a trigger to update the updated_at timestamp
-- Note: Azure SQL doesn't support CREATE OR REPLACE, so we drop first if exists
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'trg_WorkOrderNotes_UpdatedAt')
    DROP TRIGGER ben002.trg_WorkOrderNotes_UpdatedAt;
GO

CREATE TRIGGER ben002.trg_WorkOrderNotes_UpdatedAt
ON ben002.WorkOrderNotes
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE ben002.WorkOrderNotes
    SET updated_at = GETDATE()
    FROM ben002.WorkOrderNotes n
    INNER JOIN inserted i ON n.id = i.id;
END;
GO

-- Sample insert to test (optional)
-- INSERT INTO ben002.WorkOrderNotes (wo_number, note, created_by, updated_by)
-- VALUES ('S123456', 'Waiting for parts from supplier', 'system', 'system');