// Create a new file: src/utils/fractionUtils.js

/**
 * Formats a value as a fraction string when appropriate
 * @param {number|string} value - The value to format
 * @returns {string} Formatted fraction or original value
 */
export const formatFraction = (value) => {
    if (value === null || value === undefined || value === '') return '';
    
    // If it's already a fraction string, return it
    if (typeof value === 'string' && (value.includes('/') || value.includes(' '))) {
      return value;
    }
    
    // If it's a whole number, return it as is
    if (Number.isInteger(Number(value))) {
      return String(value);
    }
    
    // Try to convert decimal to fraction
    const decimal = parseFloat(value);
    if (isNaN(decimal)) return String(value);
    
    // Handle common fractions with a small tolerance for floating point errors
    const tolerance = 0.01;
    const commonFractions = [
      { decimal: 0.25, fraction: '1/4' },
      { decimal: 0.33, fraction: '1/3' },
      { decimal: 0.5, fraction: '1/2' },
      { decimal: 0.66, fraction: '2/3' },
      { decimal: 0.75, fraction: '3/4' }
    ];
    
    for (const frac of commonFractions) {
      if (Math.abs(decimal - frac.decimal) < tolerance) {
        return frac.fraction;
      }
    }
    
    // For mixed numbers (greater than 1)
    if (decimal > 1) {
      const wholePart = Math.floor(decimal);
      const fractionalPart = decimal - wholePart;
      
      if (fractionalPart > 0) {
        // Try common fractions for the fractional part
        for (const frac of commonFractions) {
          if (Math.abs(fractionalPart - frac.decimal) < tolerance) {
            return `${wholePart} ${frac.fraction}`;
          }
        }
      } else {
        return String(wholePart);
      }
    }
    
    // If no nice fraction found, return the decimal
    return String(value);
  };
  
  /**
   * Combines multiple quantities, preferring fractions when possible
   * @param {Array} quantities - Array of quantities to combine
   * @returns {string} Combined quantity as a fraction or decimal
   */
  export const combineQuantities = (quantities) => {
    // Implementation would mirror your backend combine_quantities function
    let total = 0;
    
    quantities.forEach(qty => {
      if (typeof qty === 'string' && (qty.includes('/') || qty.includes(' '))) {
        // Parse fraction string
        total += parseFraction(qty);
      } else {
        total += parseFloat(qty) || 0;
      }
    });
    
    return formatFraction(total);
  };
  
  /**
   * Parses a fraction string to a decimal value
   * @param {string} fractionStr - String like "1/2" or "1 1/2"
   * @returns {number} Decimal value
   */
  export const parseFraction = (fractionStr) => {
    if (!fractionStr) return 0;
    
    // Handle mixed numbers like "1 1/2"
    const mixedMatch = /^(\d+)\s+(\d+)\/(\d+)$/.exec(fractionStr);
    if (mixedMatch) {
      const whole = parseInt(mixedMatch[1], 10);
      const numerator = parseInt(mixedMatch[2], 10);
      const denominator = parseInt(mixedMatch[3], 10);
      return whole + (numerator / denominator);
    }
    
    // Handle simple fractions like "1/2"
    const fractionMatch = /^(\d+)\/(\d+)$/.exec(fractionStr);
    if (fractionMatch) {
      const numerator = parseInt(fractionMatch[1], 10);
      const denominator = parseInt(fractionMatch[2], 10);
      return numerator / denominator;
    }
    
    // Handle plain numbers
    return parseFloat(fractionStr) || 0;
  };