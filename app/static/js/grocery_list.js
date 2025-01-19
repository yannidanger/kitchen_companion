document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
    const groceryListElement = document.createElement('ul');
    groceryListElement.id = 'grocery-list';
    groceryListContainer.appendChild(groceryListElement);

    const weeklyPlanId = new URLSearchParams(window.location.search).get('weekly_plan_id');
    console.log('Weekly Plan ID:', weeklyPlanId);

    if (weeklyPlanId) {
        fetchGroceryList({ weekly_plan_id: weeklyPlanId });
    } else {
        groceryListContainer.innerHTML = '<p>No weekly plan selected. Please go back and choose one.</p>';
    }

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

            renderGroceryList(result); // Call render with the fetched list
        } catch (error) {
            console.error('Error fetching grocery list:', error);
            groceryListContainer.innerHTML = '<p>Error loading grocery list. Please try again later.</p>';
        }
    }

    function renderGroceryList(groceryList) {
        groceryListElement.innerHTML = ''; // Clear the current list

        if (!groceryList || groceryList.length === 0) {
            groceryListElement.innerHTML = '<p>No items in the grocery list.</p>';
            return;
        }

        // Render sections and their items
        groceryList.forEach((section) => {
            const sectionHeader = document.createElement('h3');
            sectionHeader.textContent = section.section; // Add section name
            groceryListElement.appendChild(sectionHeader);

            const ul = document.createElement('ul');
            section.items.forEach((item) => {
                const li = document.createElement('li');
                li.textContent = `${item.item_name}` + 
                    (item.quantity ? ` - ${item.quantity} ${item.unit || ''}` : '');
                ul.appendChild(li);
            });
            groceryListElement.appendChild(ul);
        });
    }
});
