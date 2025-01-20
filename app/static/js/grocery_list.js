console.log('grocery_list.js is loaded and executing.');
alert('grocery_list.js is loaded!');


document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('ingredients-list');
    groceryListContainer.style.display = 'block'; // Ensure it's visible


    async function fetchAndRenderGroceryList(weeklyPlanId) {
        try {
            const response = await fetch(`/api/generate_grocery_list`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weekly_plan_id: weeklyPlanId }),
            });

            if (!response.ok) throw new Error('Failed to fetch grocery list.');

            const data = await response.json();
            console.log('Fetched grocery list:', data);

            if (!data.grocery_list || !Array.isArray(data.grocery_list)) {
                throw new Error('Invalid grocery list structure received.');
            }

            renderGroceryList(data.grocery_list);
        } catch (error) {
            console.error('Error fetching grocery list:', error);
            groceryListContainer.innerHTML = '<p>Error loading grocery list.</p>';
        }
    }

    function renderGroceryList(groceryList) {
        console.log('Rendering grocery list:', groceryList);
        groceryListContainer.innerHTML = '';

        if (!groceryList.length) {
            groceryListContainer.innerHTML = '<p>No items in the grocery list.</p>';
            return;
        }

        const ul = document.createElement('ul');
        groceryList.forEach((item) => {
            const li = document.createElement('li');
            li.textContent = `${item.item_name} - ${item.quantity || ''} ${item.unit || ''}`.trim();
            ul.appendChild(li);
        });

        groceryListContainer.appendChild(ul);
        console.log('Rendered HTML:', groceryListContainer.innerHTML);
    }

    const weeklyPlanId = new URLSearchParams(window.location.search).get('weekly_plan_id');
    if (weeklyPlanId) {
        fetchAndRenderGroceryList(weeklyPlanId);
    } else {
        groceryListContainer.innerHTML = '<p>No weekly plan selected. Please go back and choose one.</p>';
    }
});
