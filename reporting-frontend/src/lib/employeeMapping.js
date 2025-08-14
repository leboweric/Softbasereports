// Employee ID to Name Mapping
// ===================================
// TO UPDATE: Replace 'Employee XXXX' with actual names
// Example: '2316': 'John Smith',
// ===================================

export const employeeMapping = {
  // Parts Department Employees
  // Based on invoice creation data from August 2025
  
  '2316': 'Employee 2316', // TODO: Replace with actual name - Top performer (1400 invoices)
  '2295': 'Employee 2295', // TODO: Replace with actual name - (1381 invoices) 
  '2293': 'Employee 2293', // TODO: Replace with actual name - (1016 invoices)
  '2318': 'Employee 2318', // TODO: Replace with actual name - (813 invoices)
  '2334': 'Employee 2334', // TODO: Replace with actual name - (613 invoices)
  '2317': 'Employee 2317', // TODO: Replace with actual name - (130 invoices)
  '2336': 'Employee 2336', // TODO: Replace with actual name - (43 invoices)
  '2338': 'Employee 2338', // TODO: Replace with actual name - (36 invoices)
  '2315': 'Employee 2315', // TODO: Replace with actual name - (13 invoices)
  '2275': 'Employee 2275', // TODO: Replace with actual name - (5 invoices)
  '2332': 'Employee 2332', // TODO: Replace with actual name - (2 invoices)
  
  // Add any missing employee IDs here:
  // 'XXXX': 'First Last',
};

// Helper function to get employee name
export const getEmployeeName = (employeeId) => {
  if (!employeeId) return 'Unknown';
  
  // Convert to string and trim
  const id = String(employeeId).trim();
  
  // Look up in mapping
  return employeeMapping[id] || `Employee ${id}`;
};

// Helper function to get employee first/last name
export const getEmployeeDetails = (employeeId) => {
  const fullName = getEmployeeName(employeeId);
  
  if (fullName.startsWith('Employee ')) {
    return {
      firstName: '',
      lastName: '',
      fullName: fullName
    };
  }
  
  const parts = fullName.split(' ');
  return {
    firstName: parts[0] || '',
    lastName: parts.slice(1).join(' ') || '',
    fullName: fullName
  };
};