document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
    const precisionToggle = document.getElementById('precision-mode-toggle');

    // Fetch grocery list data from the API
    // Fetch the grocery list on form submission
    async function fetchGroceryList(data) {
        try {
            const response = await fetch('/api/generate_grocery_list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error('Failed to generate the grocery list.');
            }

            const result = await response.json();
            if (result.error) {
                alert(result.error);
                return;
            }

            // Render the grocery list
            renderGroceryList(result.grocery_list);
        } catch (error) {
            console.error(error);
            alert('An error occurred while generating the grocery list.');
        }
    }

    // Render the grocery list in the DOM
    function renderGroceryList(groceryList) {
        const listContainer = document.getElementById('grocery-list');
        listContainer.innerHTML = '';

        if (!groceryList.length) {
            listContainer.innerHTML = '<p>No items in the grocery list.</p>';
            return;
        }

        groceryList.forEach(item => {
            const listItem = document.createElement('li');
            listItem.textContent = `${item.item_name} - ${item.quantity || ''} ${item.unit || ''}`;
            listContainer.appendChild(listItem);
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
