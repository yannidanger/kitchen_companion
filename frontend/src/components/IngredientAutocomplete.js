import React, { useState, useEffect, useRef } from 'react';

/**
 * Ingredient Autocomplete component with USDA database integration
 * 
 * @param {object} props Component props
 * @param {string} props.value Current ingredient value
 * @param {function} props.onChange Callback when selection changes
 * @param {function} props.onSelect Callback when an ingredient is selected
 * @param {string} props.placeholder Placeholder text
 * @param {boolean} props.required Whether the field is required
 */
const IngredientAutocomplete = ({ 
  value = '', 
  onChange, 
  onSelect, 
  placeholder = 'Ingredient Name',
  required = false 
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const resultsRef = useRef(null);
  
  // Debounce timer for search
  const timerRef = useRef(null);

  // Update input value when external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Handle clicks outside the component to close the dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (inputRef.current && !inputRef.current.contains(event.target) &&
          resultsRef.current && !resultsRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Search USDA database for ingredients
  const searchIngredients = async (query) => {
    if (!query || query.length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/usda/search?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data.foods) {
        const formattedResults = data.foods.map(food => ({
          id: food.fdc_id,
          name: food.description,
          category: food.category || 'Unknown',
          isUsda: true
        }));
        
        // Also search local database for custom ingredients
        const localResponse = await fetch(`http://127.0.0.1:5000/api/ingredients?query=${encodeURIComponent(query)}`);
        const localData = await localResponse.json();
        
        // Combine USDA and custom ingredients
        const combinedResults = [
          ...formattedResults,
          ...localData.map(item => ({
            id: item.id,
            name: item.name,
            display_name: item.display_name,
            isCustom: item.is_custom,
            isUsda: !item.is_custom
          }))
        ];
        
        // Remove duplicates by ID
        const uniqueResults = Array.from(
          new Map(combinedResults.map(item => [item.id, item])).values()
        );
        
        setResults(uniqueResults);
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Error searching ingredients:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle input changes with debounce
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Call the parent onChange handler
    if (onChange) {
      onChange(value);
    }
    
    // Clear any existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    // Set a new timer for debounced search
    timerRef.current = setTimeout(() => {
      searchIngredients(value);
    }, 300);
    
    setShowResults(true);
  };

  // Handle selecting an ingredient from results
  const handleSelectIngredient = (ingredient) => {
    setInputValue(ingredient.display_name || ingredient.name);
    setShowResults(false);
    setSelectedIndex(-1);
    
    // Call the parent onSelect handler with the selected ingredient
    if (onSelect) {
      onSelect(ingredient);
    }
  };

  // Handle keyboard navigation in results
  const handleKeyDown = (e) => {
    // Only handle keys if results are showing
    if (!showResults || results.length === 0) return;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelectIngredient(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowResults(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  return (
    <div className="ingredient-autocomplete">
      <div className="autocomplete-input-container">
        <input
          ref={inputRef}
          type="text"
          className="autocomplete-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowResults(true)}
          placeholder={placeholder}
          required={required}
        />
        {loading && <div className="autocomplete-loading"></div>}
      </div>
      
      {showResults && results.length > 0 && (
        <ul 
          ref={resultsRef}
          className="autocomplete-results"
        >
          {results.map((result, index) => (
            <li 
              key={result.id}
              className={`autocomplete-result ${selectedIndex === index ? 'selected' : ''} ${result.isUsda ? 'usda-item' : 'custom-item'}`}
              onClick={() => handleSelectIngredient(result)}
            >
              <div className="result-name">{result.display_name || result.name}</div>
              {result.category && (
                <div className="result-category">{result.category}</div>
              )}
              <div className="result-badge">
                {result.isUsda ? 'USDA' : 'Custom'}
              </div>
            </li>
          ))}
        </ul>
      )}
      
      {showResults && inputValue.length >= 2 && results.length === 0 && !loading && (
        <div className="no-results">
          No ingredients found. Type to add a custom ingredient.
        </div>
      )}
    </div>
  );
};

export default IngredientAutocomplete;