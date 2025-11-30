// Configure your backend URL
const BACKEND_URL = 'https://6zr1t9v1-5000.inc1.devtunnels.ms/api'; // Replace with production URL

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Cliq SDK
    // In a real app, we get the user ID from the Cliq context
    // For this demo, we might need to mock it or ask the user to input it if not available in context immediately
    
    // Mock User ID for demo purposes or try to get from URL params if passed by Cliq
    const userId = "test_user"; // Replace with actual logic to get current user ID
    
    try {
        const response = await fetch(`${BACKEND_URL}/portfolio/${userId}`);
        const data = await response.json();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
        
        document.getElementById('total-value').textContent = `$${data.total_value.toFixed(2)}`;
        
        const list = document.getElementById('holdings-list');
        list.innerHTML = '';
        
        data.holdings.forEach(h => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${h.coin.toUpperCase()}</td>
                <td>$${h.current_price}</td>
                <td>${h.amount}</td>
                <td>$${h.value.toFixed(2)}</td>
            `;
            list.appendChild(row);
        });
        
    } catch (error) {
        document.getElementById('loading').textContent = "Error loading data. Ensure backend is running.";
        console.error(error);
    }
});
