document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
    const precisionToggle = document.getElementById('precision-mode-toggle');

    // Fetch and render the grocery list
    async function fetchAndRenderGroceryList(weeklyPlanId) {
        try {
            const response = await fetch(`/api/generate_grocery_list`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ weekly_plan_id: weeklyPlanId }),
            });
    
            if (!response.ok) throw new Error('Failed to fetch grocery list.');
    
            const data = await response.json();
            console.log('Fetched grocery list:', data); // Add this
            renderGroceryList(data.grocery_list);
        } catch (error) {
            console.error(error);
            groceryListContainer.innerHTML = '<p>Error loading grocery list.</p>';
        }
    }
    

    // Render the grocery list in the DOM
    function renderGroceryList(groceryList) {
        console.log('Grocery List:', groceryList);
        console.log('Rendering grocery list:', groceryList);

        const listContainer = document.getElementById('grocery-list-container');
        listContainer.innerHTML = ''; // Clear existing content
    
        if (!groceryList.length) {
            listContainer.innerHTML = '<p>No items in the grocery list.</p>';
            return;
        }
    
        const ul = document.createElement('ul');
        groceryList.forEach(item => {
            const li = document.createElement('li');
            li.textContent = `${item.item_name} - ${item.quantity || ''} ${item.unit || ''}`.trim();
            ul.appendChild(li);
        });
    
        listContainer.appendChild(ul);
    }
    

    // Initialize: Fetch the list for the selected weekly plan
    const weeklyPlanId = new URLSearchParams(window.location.search).get('weekly_plan_id');
    if (weeklyPlanId) {
        fetchAndRenderGroceryList(weeklyPlanId);
    } else {
        groceryListContainer.innerHTML = '<p>No weekly plan selected. Please go back and choose one.</p>';
    }

    // Precision mode toggle
    precisionToggle?.addEventListener('change', () => {
        groceryListContainer.classList.toggle('precision-mode', precisionToggle.checked);
    });
});
