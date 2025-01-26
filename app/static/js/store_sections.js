document.addEventListener('DOMContentLoaded', () => {
    const storeId = document.getElementById('storeId').value; // Assuming storeId is stored in an element with id 'storeId'
    const sectionsTable = document.getElementById('sectionsTable').querySelector('tbody');
    const addSectionBtn = document.getElementById('addSectionBtn');
    const sectionModal = document.getElementById('sectionModal');
    const sectionForm = document.getElementById('sectionForm');

    // Fetch and render sections
    async function fetchSections() {
        const response = await fetch(`/api/stores/${storeId}/sections`);
        const sections = await response.json();
        sectionsTable.innerHTML = sections.map(section => `
            <tr data-id="${section.id}">
                <td>${section.order}</td>
                <td>${section.name}</td>
                <td>
                    <button class="editBtn">Edit</button>
                    <button class="deleteBtn">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    // Show modal for adding/editing
    addSectionBtn.addEventListener('click', () => {
        sectionForm.reset();
        sectionModal.style.display = 'block';
    });

    // Save section
    sectionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(sectionForm);
        const sectionData = Object.fromEntries(formData);
        await fetch(`/api/stores/${storeId}/sections`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sectionData)
        });
        sectionModal.style.display = 'none';
        fetchSections();
    });

    // Delete section
    sectionsTable.addEventListener('click', async (e) => {
        if (e.target.classList.contains('deleteBtn')) {
            const row = e.target.closest('tr');
            const sectionId = row.dataset.id;
            await fetch(`/api/stores/${storeId}/sections/${sectionId}`, { method: 'DELETE' });
            fetchSections();
        }
    });

    // Load sections on page load
    fetchSections();
});
