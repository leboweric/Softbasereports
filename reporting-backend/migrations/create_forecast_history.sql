-- Create ForecastHistory table for tracking forecast accuracy
-- This table stores every forecast generated and compares to actual results

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ForecastHistory')
BEGIN
    CREATE TABLE ben002.ForecastHistory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        
        -- When was this forecast made?
        forecast_date DATE NOT NULL,
        forecast_timestamp DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- What period is being forecasted?
        target_year INT NOT NULL,
        target_month INT NOT NULL,
        days_into_month INT NOT NULL,
        
        -- Forecast values
        projected_total DECIMAL(18,2) NOT NULL,
        forecast_low DECIMAL(18,2),
        forecast_high DECIMAL(18,2),
        confidence_level VARCHAR(10),
        
        -- Context at time of forecast
        mtd_sales DECIMAL(18,2),
        mtd_invoices INT,
        month_progress_pct DECIMAL(5,2),
        days_remaining INT,
        pipeline_value DECIMAL(18,2),
        avg_pct_complete DECIMAL(5,2),
        
        -- Actual outcome (filled in after month ends)
        actual_total DECIMAL(18,2) NULL,
        actual_invoices INT NULL,
        accuracy_pct DECIMAL(5,2) NULL,
        absolute_error DECIMAL(18,2) NULL,
        within_range BIT NULL,
        
        -- Metadata
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME NULL,
        
        -- Indexes for performance
        INDEX IX_ForecastHistory_Target (target_year, target_month),
        INDEX IX_ForecastHistory_Date (forecast_date)
    );
    
    PRINT 'ForecastHistory table created successfully';
END
ELSE
BEGIN
    PRINT 'ForecastHistory table already exists';
END
GO

-- Create stored procedure to backfill actual totals after month ends
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'UpdateForecastActuals')
    DROP PROCEDURE ben002.UpdateForecastActuals;
GO

CREATE PROCEDURE ben002.UpdateForecastActuals
    @target_year INT,
    @target_month INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get actual total for the completed month
    DECLARE @actual_total DECIMAL(18,2);
    DECLARE @actual_invoices INT;
    
    SELECT 
        @actual_total = SUM(GrandTotal),
        @actual_invoices = COUNT(*)
    FROM ben002.InvoiceReg
    WHERE YEAR(InvoiceDate) = @target_year
        AND MONTH(InvoiceDate) = @target_month;
    
    -- Update all forecasts for this month with actuals
    UPDATE ben002.ForecastHistory
    SET 
        actual_total = @actual_total,
        actual_invoices = @actual_invoices,
        accuracy_pct = CASE 
            WHEN @actual_total > 0 THEN 
                ABS(projected_total - @actual_total) / @actual_total * 100
            ELSE NULL
        END,
        absolute_error = ABS(projected_total - @actual_total),
        within_range = CASE 
            WHEN @actual_total BETWEEN ISNULL(forecast_low, projected_total) 
                AND ISNULL(forecast_high, projected_total) THEN 1
            ELSE 0
        END,
        updated_at = GETDATE()
    WHERE target_year = @target_year
        AND target_month = @target_month
        AND actual_total IS NULL;
    
    PRINT 'Updated ' + CAST(@@ROWCOUNT AS VARCHAR) + ' forecast records with actuals';
END
GO

PRINT 'Forecast accuracy tracking system created successfully';
