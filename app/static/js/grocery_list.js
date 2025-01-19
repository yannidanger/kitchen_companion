document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
    const precisionToggle = document.getElementById('precision-mode-toggle');

    // Fetch grocery list data from the API
    // Fetch grocery list data from the API
    async function fetchGroceryList(weeklyPlanId) {
        try {
            const response = await fetch(`/grocery/api/grocery_list?weekly_plan_id=${weeklyPlanId}`);
            console.log('Received Data:', data);
            if (!Array.isArray(data)) {
                console.error("Invalid grocery list format:", data);
                groceryListContainer.innerHTML = "<p>Unexpected data format received.</p>";
                return;
            }
            if (!data || !Array.isArray(data) || data.length === 0) {
                console.error('Invalid or empty grocery list received:', data); // Add here
                groceryListContainer.innerHTML = '<p>No grocery list data available.</p>';
                return;
            }
            
            if (!response.ok) {
                throw new Error(`Failed to fetch grocery list. Status: ${response.status}`);
            }
            const data = await response.json();
            console.log('API Response:', data); // Log response to debug
            console.log('Fetched data:', data); // <-- Log the fetched data
            renderGroceryList(data); // Render the grocery list dynamically
        } catch (error) {
            console.error('Error fetching grocery list:', error);
            groceryListContainer.innerHTML = '<p>Error loading grocery list. Please try again.</p>';
        }
    }


    // Render the grocery list dynamically
    // Render the grocery list dynamically
    function renderGroceryList(data) {
        const groceryListContainer = document.getElementById('grocery-list-container');
        groceryListContainer.innerHTML = ''; // Clear existing content
    
        data.forEach(section => {
            const sectionDiv = document.createElement('div');
            sectionDiv.classList.add('grocery-section');
    
            const sectionHeader = document.createElement('h2');
            sectionHeader.textContent = section.section;
            sectionDiv.appendChild(sectionHeader);
    
            const itemList = document.createElement('ul');
            section.items.forEach(item => {
                const listItem = document.createElement('li');
                listItem.textContent = `${item.name} (${item.quantity} ${item.unit})`;
                itemList.appendChild(listItem);
                if (!data || data.length === 0) {
                    groceryListContainer.innerHTML = '<p>The grocery list is empty or unavailable.</p>';  // Add here
                    return;
                }
                
            });
    
            sectionDiv.appendChild(itemList);
            console.log(`Section rendered: ${section.section}`, section.items);
            groceryListContainer.appendChild(sectionDiv);
        });
    }
    


    // Toggle precision mode
    precisionToggle.addEventListener('change', () => {
        const groceryItems = document.querySelectorAll('.grocery-item');
        groceryItems.forEach(item => {
            const precisionInfo = item.querySelector('.precision-info');
            if (precisionInfo) {
                precisionInfo.classList.toggle('hidden', !precisionToggle.checked);
            }
        });
    });

    // Initialize
    // Initialize
    const weeklyPlanId = new URLSearchParams(window.location.search).get('weekly_plan_id');
    console.log('window.location.search:', window.location.search); // Log the query string
    console.log('Parsed Weekly Plan ID:', weeklyPlanId);
    
    if (weeklyPlanId) {
        fetchGroceryList(weeklyPlanId);
    } else {
        groceryListContainer.innerHTML = '<p>No weekly plan selected. Please go back and choose one.</p>';
    }
    

});
