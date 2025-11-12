-- Knowledge Base Table Schema for PostgreSQL
-- Run this to manually create the table and insert sample data

CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    equipment_make VARCHAR(100),
    equipment_model VARCHAR(100),
    issue_category VARCHAR(100) NOT NULL,
    symptoms TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    solution TEXT NOT NULL,
    related_wo_numbers VARCHAR(500),
    image_urls TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    updated_date TIMESTAMP,
    view_count INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(issue_category);
CREATE INDEX IF NOT EXISTS idx_kb_make ON knowledge_base(equipment_make);
CREATE INDEX IF NOT EXISTS idx_kb_created ON knowledge_base(created_date DESC);
CREATE INDEX IF NOT EXISTS idx_kb_views ON knowledge_base(view_count DESC);

-- Sample Article 1: Hydraulic Issue
INSERT INTO knowledge_base (
    title, equipment_make, equipment_model, issue_category, symptoms, root_cause, solution,
    related_wo_numbers, image_urls, created_by, created_date, view_count
) VALUES (
    'Hydraulic Pump Failure - Loss of Pressure',
    'Caterpillar', '320D', 'Hydraulic',
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
    'WO-12345, WO-12389', '', 'Service Manager', CURRENT_TIMESTAMP, 0
);

-- Sample Article 2: Engine Issue
INSERT INTO knowledge_base (
    title, equipment_make, equipment_model, issue_category, symptoms, root_cause, solution,
    related_wo_numbers, image_urls, created_by, created_date, view_count
) VALUES (
    'Engine Won''t Start - Cold Weather',
    'John Deere', '310L', 'Engine',
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
    'WO-12456', '', 'Service Manager', CURRENT_TIMESTAMP, 0
);

-- Sample Article 3: Electrical Issue
INSERT INTO knowledge_base (
    title, equipment_make, equipment_model, issue_category, symptoms, root_cause, solution,
    related_wo_numbers, image_urls, created_by, created_date, view_count
) VALUES (
    'Electrical Short - Intermittent Power Loss',
    'Bobcat', 'S650', 'Electrical',
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
    'WO-12567, WO-12589', '', 'Service Manager', CURRENT_TIMESTAMP, 0
);
