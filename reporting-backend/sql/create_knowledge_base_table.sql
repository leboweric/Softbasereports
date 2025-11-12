-- Knowledge Base Table Schema
-- This table stores technical troubleshooting articles for field technicians

CREATE TABLE ben002.KnowledgeBase (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(255) NOT NULL,
    EquipmentMake NVARCHAR(100),
    EquipmentModel NVARCHAR(100),
    IssueCategory NVARCHAR(100) NOT NULL,
    Symptoms NVARCHAR(MAX) NOT NULL,
    RootCause NVARCHAR(MAX) NOT NULL,
    Solution NVARCHAR(MAX) NOT NULL,
    RelatedWONumbers NVARCHAR(500),
    ImageUrls NVARCHAR(MAX),
    CreatedBy NVARCHAR(100) NOT NULL,
    CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
    UpdatedBy NVARCHAR(100),
    UpdatedDate DATETIME,
    ViewCount INT DEFAULT 0,
    INDEX IX_KnowledgeBase_Category (IssueCategory),
    INDEX IX_KnowledgeBase_Make (EquipmentMake),
    INDEX IX_KnowledgeBase_CreatedDate (CreatedDate DESC),
    INDEX IX_KnowledgeBase_ViewCount (ViewCount DESC)
);

-- Add full-text search capability (optional, for better search performance)
-- CREATE FULLTEXT CATALOG KnowledgeBaseCatalog AS DEFAULT;
-- CREATE FULLTEXT INDEX ON ben002.KnowledgeBase(Title, Symptoms, RootCause, Solution)
--     KEY INDEX PK__KnowledgeBase;

-- Sample data for testing
INSERT INTO ben002.KnowledgeBase (
    Title,
    EquipmentMake,
    EquipmentModel,
    IssueCategory,
    Symptoms,
    RootCause,
    Solution,
    RelatedWONumbers,
    ImageUrls,
    CreatedBy,
    CreatedDate,
    ViewCount
) VALUES (
    'Hydraulic Pump Failure - Loss of Pressure',
    'Caterpillar',
    '320D',
    'Hydraulic',
    'Equipment experiencing sudden loss of hydraulic pressure. Boom and bucket movements are slow or non-responsive. Hydraulic oil temperature is elevated.',
    'Hydraulic pump internal seal failure due to contaminated hydraulic fluid. Metal particles found in filter indicate pump wear.',
    '1. Shut down equipment immediately
2. Drain hydraulic system completely
3. Replace hydraulic pump (Part #: 123-4567)
4. Replace all hydraulic filters
5. Flush hydraulic lines
6. Refill with fresh hydraulic oil (ISO 46)
7. Bleed air from system
8. Test all hydraulic functions under load
9. Check for leaks
10. Document oil analysis results',
    'WO-12345, WO-12389',
    '',
    'Service Manager',
    GETDATE(),
    0
);

INSERT INTO ben002.KnowledgeBase (
    Title,
    EquipmentMake,
    EquipmentModel,
    IssueCategory,
    Symptoms,
    RootCause,
    Solution,
    RelatedWONumbers,
    ImageUrls,
    CreatedBy,
    CreatedDate,
    ViewCount
) VALUES (
    'Engine Won''t Start - Cold Weather',
    'John Deere',
    '310L',
    'Engine',
    'Engine cranks but won''t start in cold weather (below 20°F). Glow plug light stays on longer than normal. White smoke from exhaust during cranking.',
    'Glow plug relay failure preventing proper pre-heating of combustion chambers. Common issue in cold climates when glow plugs have over 3000 hours.',
    '1. Test glow plug resistance (should be 0.5-2.0 ohms)
2. Replace failed glow plugs
3. Test glow plug relay with multimeter
4. Replace relay if faulty (Part #: RE-506205)
5. Check battery voltage (must be above 12.4V)
6. Use block heater in extreme cold
7. Consider winter-grade diesel fuel
8. Add anti-gel additive to fuel tank',
    'WO-12456',
    '',
    'Service Manager',
    GETDATE(),
    0
);

INSERT INTO ben002.KnowledgeBase (
    Title,
    EquipmentMake,
    EquipmentModel,
    IssueCategory,
    Symptoms,
    RootCause,
    Solution,
    RelatedWONumbers,
    ImageUrls,
    CreatedBy,
    CreatedDate,
    ViewCount
) VALUES (
    'Electrical Short - Intermittent Power Loss',
    'Bobcat',
    'S650',
    'Electrical',
    'Intermittent loss of all electrical power. Dashboard lights flicker. Equipment shuts down randomly during operation. Battery drains overnight.',
    'Corroded main ground cable connection at frame. Water intrusion in main harness connector near battery box.',
    '1. Disconnect battery (negative first)
2. Inspect all ground connections
3. Clean corroded ground points with wire brush
4. Apply dielectric grease to connections
5. Check main harness connector for water/corrosion
6. Seal connector with electrical tape or heat shrink
7. Test voltage drop across ground connections (should be <0.1V)
8. Reconnect battery (positive first)
9. Monitor for 24 hours to confirm fix',
    'WO-12567, WO-12589',
    '',
    'Service Manager',
    GETDATE(),
    0
);
